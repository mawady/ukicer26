import os
import re
from pathlib import Path
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeEngine:
    def __init__(self):
        # Local storage directory for indexed text chunks
        self.storage_dir = Path("knowledge/index")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def clear_cache(self) -> int:
        """Deletes all cached index files inside the storage directory."""
        deleted_count = 0
        if self.storage_dir.exists():
            for file_path in self.storage_dir.glob("*.txt"):
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting cached file {file_path}: {e}")
        return deleted_count

    @staticmethod
    def _is_useless_chunk(text: str, title: str) -> bool:
        """Filters out noise like Table of Contents, copyright notices, and generic boilerplate."""
        text_lower = text.lower()
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
            "contents", "table of contents", "about this statement",
            "relationship to legislation", "how can i use this document",
            "copyright", "all rights reserved", "isbn", "published by"
        ]
        if any(keyword in title_lower for keyword in junk_keywords):
            return True

        # Check for TOC-like structural density (e.g. lines ending with numbers)
        toc_line_matches = re.findall(r"\.\s*\d+$", text, flags=re.MULTILINE)
        if len(toc_line_matches) >= 2:
            return True

        return False

    @staticmethod
    def _clean_text(text: str) -> str:
        """Sanitizes raw extracted text to remove junk characters, page numbers, and fix spacing."""
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

    def index_directory(self, folder_path: str, source_level: str) -> int:
        path = Path(folder_path)
        path.mkdir(parents=True, exist_ok=True)

        chunks_indexed = 0
        # Regex to detect meaningful document headings (e.g., '1 Context', '2 Subject Benchmark', 'Characteristics')
        section_pattern = re.compile(
            r"\n(?=(\d+(\.\d+)*\s+[A-Z][a-zA-Z\s,]+|Subject Benchmark|Characteristics of|Purposes of|Core Subjects|Course Content))"
        )

        for root, _, files in os.walk(path):
            for file_name in files:
                if file_name.startswith(".") or file_name.startswith("~$"):
                    continue

                file_path = Path(root) / file_name
                try:
                    if file_path.suffix.lower() == ".pdf":
                        raw_text = self._extract_raw_pdf_text(file_path)
                    else:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            raw_text = f.read()

                    cleaned_text = self._clean_text(raw_text)
                    if not cleaned_text:
                        continue

                    # Split document into distinct structural sections
                    sections = section_pattern.split(cleaned_text)
                    for idx, section in enumerate(sections):
                        if not section or len(section.strip()) < 40:
                            continue

                        section_text = self._clean_text(section)
                        lines = [line.strip() for line in section_text.splitlines() if line.strip()]
                        
                        section_title = lines[0] if lines else "General Overview"

                        # Skip useless chunks (TOCs, page indexes, disclaimers)
                        if self._is_useless_chunk(section_text, section_title):
                            continue

                        # Save clean, useful chunk
                        out_file = self.storage_dir / f"{source_level}_{file_path.stem}_sec_{idx}.txt"
                        with open(out_file, "w", encoding="utf-8") as out:
                            out.write(f"SECTION: {section_title}\n{section_text}")

                        chunks_indexed += 1

                except Exception as e:
                    print(f"Error indexing {file_name}: {e}")

        return chunks_indexed

    def retrieve(self, query: str, top_k: int = 3) -> list:
        """Ranks indexed section chunks using TF-IDF cosine similarity."""
        if not self.storage_dir.exists():
            return []

        file_paths = list(self.storage_dir.glob("*.txt"))
        if not file_paths:
            return []

        documents = []
        metadata = []

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if not content.strip():
                    continue

                parts = file_path.stem.split("_", 1)
                level = parts[0] if len(parts) > 1 else "General"
                doc_name = parts[1].split("_sec_")[0] if "_sec_" in parts[1] else parts[1]

                lines = content.splitlines()
                if lines and lines[0].startswith("SECTION:"):
                    section_heading = lines[0].replace("SECTION:", "").strip()
                    body_content = "\n".join(lines[1:]).strip()
                else:
                    section_heading = "General Overview"
                    body_content = content.strip()

                clean_body = self._clean_text(body_content)

                # Skip chunk if recognized as noise
                if self._is_useless_chunk(clean_body, section_heading):
                    continue

                documents.append(clean_body)
                metadata.append({
                    "source": f"{doc_name}.pdf" if "pdf" in doc_name.lower() or "sbs" in doc_name.lower() else doc_name,
                    "source_level": level,
                    "section": section_heading,
                    "content": clean_body[:800]
                })
            except Exception:
                continue

        if not documents:
            return []

        # Calculate TF-IDF vector relevance scores
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(documents + [query])

        query_vec = tfidf_matrix[-1]
        doc_vecs = tfidf_matrix[:-1]

        similarities = cosine_similarity(query_vec, doc_vecs).flatten()

        ranked_indices = similarities.argsort()[::-1]

        results = []
        for idx in ranked_indices[:top_k]:
            if similarities[idx] > 0.05:  # Enforce minimum similarity threshold
                item = metadata[idx]
                item["score"] = round(float(similarities[idx]), 3)
                results.append(item)

        # Fallback to top metadata entries if no high-confidence TF-IDF matches occur
        if not results:
            results = metadata[:top_k]

        return results