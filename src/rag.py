import os
import re
from pathlib import Path
from pypdf import PdfReader

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from fastembed import TextEmbedding


class FastEmbedEmbeddingFunction(EmbeddingFunction):
    """Custom wrapper for FastEmbed to avoid ChromaDB import path mismatches."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        # FastEmbed manages ONNX runtime and lightweight embedding downloads (~130 MB)
        self.model = TextEmbedding(model_name=model_name)

    def __call__(self, input: Documents) -> Embeddings:
        # Generates embedding vectors and converts numpy arrays to plain lists for ChromaDB
        embeddings = self.model.embed(input)
        return [e.tolist() for e in embeddings]


class KnowledgeEngine:
    def __init__(self, db_dir: str = "knowledge/chroma_db"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)

        # Initialize lightweight ONNX embedding function
        self.embedding_fn = FastEmbedEmbeddingFunction(
            model_name="BAAI/bge-small-en-v1.5"
        )

        # Initialize persistent ChromaDB storage
        self.client = chromadb.PersistentClient(path=str(self.db_dir))
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def clear_cache(self) -> int:
        """Deletes all indexed vectors from the database."""
        count = self.collection.count()
        if count > 0:
            self.client.delete_collection("knowledge_base")
            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
        return count

    @staticmethod
    def _is_useless_chunk(text: str, title: str) -> bool:
        """Filters out noise like Table of Contents, copyright notices, and generic boilerplate."""
        title_lower = title.lower()

        # Ignore tiny chunks
        if len(text.strip()) < 120:
            return True

        # Detect Table of Contents (dotted leader lines or heavy page index references)
        dots_count = text.count("...") + text.count(". . .") + text.count("…")
        if dots_count > 3:
            return True

        # Keyword filtering for administrative junk
        junk_keywords = [
            "contents",
            "table of contents",
            "about this statement",
            "relationship to legislation",
            "how can i use this document",
            "copyright",
            "all rights reserved",
            "isbn",
            "published by",
        ]
        if any(keyword in title_lower for keyword in junk_keywords):
            return True

        # Check for TOC-like structural density (e.g., lines ending with page numbers)
        toc_line_matches = re.findall(r"\.\s*\d+$", text, flags=re.MULTILINE)
        if len(toc_line_matches) >= 2:
            return True

        return False

    @staticmethod
    def _clean_text(text: str) -> str:
        """Sanitizes raw extracted text to remove junk control characters and page headers."""
        if not text:
            return ""
        # Remove non-printable control characters
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]", "", text)
        # Strip header markers and standalone page headers/footers
        text = re.sub(r"--- Page \d+ ---", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Page \d+ of \d+", "", text, flags=re.IGNORECASE)
        # Normalize whitespace and line breaks
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _extract_raw_pdf_text(self, file_path: Path) -> str:
        """Extracts plain text from PDF pages."""
        reader = PdfReader(str(file_path))
        pages_text = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                pages_text.append(extracted)
        return "\n".join(pages_text)

    def _chunk_text(
        self, text: str, max_chars: int = 1000, overlap: int = 150
    ) -> list[str]:
        """Splits document text into overlapping paragraph-aware windows."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            if current_length + len(para) > max_chars:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_length = len(para)
            else:
                current_chunk.append(para)
                current_length += len(para)

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def index_directory(self, folder_path: str, source_level: str) -> int:
        path = Path(folder_path)
        if not path.exists():
            return 0

        documents, ids, metadatas = [], [], []

        for root, _, files in os.walk(path):
            for file_name in files:
                if file_name.startswith(".") or file_name.startswith("~$"):
                    continue

                file_path = Path(root) / file_name
                try:
                    if file_path.suffix.lower() == ".pdf":
                        raw_text = self._extract_raw_pdf_text(file_path)
                    else:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            raw_text = f.read()

                    cleaned_text = self._clean_text(raw_text)
                    if not cleaned_text:
                        continue

                    chunks = self._chunk_text(cleaned_text)

                    for idx, chunk in enumerate(chunks):
                        lines = [
                            line.strip()
                            for line in chunk.splitlines()
                            if line.strip()
                        ]
                        section_title = (
                            lines[0] if lines else "General Overview"
                        )

                        if self._is_useless_chunk(chunk, section_title):
                            continue

                        doc_id = f"{source_level}_{file_path.stem}_{idx}"

                        documents.append(chunk)
                        ids.append(doc_id)
                        metadatas.append(
                            {
                                "source": file_path.name,
                                "source_level": source_level,
                                "section": section_title[:100],
                            }
                        )

                except Exception as e:
                    print(f"Error indexing {file_name}: {e}")

        if documents:
            # Upsert into vector store (handles batching internally)
            self.collection.add(
                documents=documents, ids=ids, metadatas=metadatas
            )

        return len(documents)

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Queries the vector database using FastEmbed semantic search."""
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        formatted_results = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for doc, meta, dist in zip(docs, metas, distances):
                # Cosine distance to similarity conversion
                score = round(1 - float(dist), 3)

                # Similarity threshold (filters low confidence semantic matches)
                if score >= 0.25:
                    formatted_results.append(
                        {
                            "source": meta["source"],
                            "source_level": meta["source_level"],
                            "section": meta["section"],
                            "content": doc[:800],
                            "score": score,
                        }
                    )

        return formatted_results