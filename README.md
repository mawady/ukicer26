# Bridging Learning Outcomes and Module Specifications: GenAI Framework for Curriculum Development in CS Education

[![UKICER 2026](https://img.shields.io/badge/UKICER-2026-blue)](https://ukicer.github.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black)](https://ollama.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> A Generative AI framework for supporting curriculum and module specification development in Computer Science education.

This repository accompanies our UKICER 2026 research paper:

**Bridging Learning Outcomes and Module Specifications: A GenAI Framework for Curriculum Development in CS Education**

The framework combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and automated consistency verification to support the development of structured module specifications.

---

## Overview

Designing and updating academic modules requires alignment between multiple components, including:

- Intended Learning Outcomes (ILOs)
- Module content and weekly syllabus
- Learning and teaching activities
- Assessments
- Student workload
- Institutional and sector guidelines

This project explores how Generative AI can support this process by automatically generating structured module specifications from module metadata, learning outcomes, and trusted knowledge sources.

The framework combines:

1. Structured module metadata
2. Retrieval-Augmented Generation (RAG)
3. Local Large Language Models via Ollama
4. Automated module specification generation
5. Weekly formative quiz generation
6. Consistency and alignment verification

The system is designed to support academic staff in curriculum development rather than replace academic judgement.

---

## Key Features

- Generate structured module specifications from high-level module metadata.
- Define and incorporate Intended Learning Outcomes (ILOs).
- Retrieve relevant institutional and sector guidelines using RAG.
- Generate module overviews and rationales.
- Generate weekly syllabi and learning activities.
- Map weekly topics to Intended Learning Outcomes.
- Generate assessment components and weightings.
- Generate formative weekly quizzes.
- Calculate and verify student workload.
- Perform automated consistency checks across generated specifications.
- Support local LLMs through Ollama.
- Provide an interactive web interface using Streamlit.

---

## Framework Architecture

The proposed framework consists of four main stages:

```text
┌─────────────────────────────────┐
│          Module Input           │
│                                 │
│  • Module title                 │
│  • Module code                  │
│  • Academic level               │
│  • Credits                      │
│  • Intended Learning Outcomes   │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│      Knowledge Retrieval        │
│             (RAG)               │
│                                 │
│  • University guidelines        │
│  • Sector guidelines            │
│  • Trusted documents            │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│       LLM Generation            │
│                                 │
│  • Module specification         │
│  • Weekly syllabus              │
│  • Assessments                  │
│  • Practice quizzes             │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│    Consistency Verification     │
│                                 │
│  • ILO alignment                │
│  • Workload checks              │
│  • Assessment weighting         │
│  • Internal consistency         │
└─────────────────────────────────┘
```

---

## Application Workflow

The framework follows the following workflow:

1. Enter the module metadata.
2. Define the Intended Learning Outcomes.
3. Select a local LLM.
4. Index trusted institutional and sector knowledge sources.
5. Generate the module specification.
6. Review the generated syllabus and assessments.
7. Generate formative weekly quizzes.
8. Run automated consistency checks.
9. Review and refine the generated specification.

---

## Repository Structure

```text
ukicer26/
│
├── src/
│   ├── app.py
│   ├── generator.py
│   ├── models.py
│   ├── rag.py
│   ├── verifier.py
│   │
│   └── knowledge/
│       ├── university/
│       └── sector/
│
├── requirements.txt
├── LICENSE
└── README.md
```

### Core Components

| Component | Description |
|---|---|
| `app.py` | Streamlit web application and user interface |
| `generator.py` | LLM-based content and quiz generation |
| `models.py` | Data models and structured representations |
| `rag.py` | Retrieval-Augmented Generation and knowledge indexing |
| `verifier.py` | Automated consistency and alignment verification |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mawady/ukicer26.git
cd ukicer26
```

### 2. Install Ollama

Install Ollama from:

https://ollama.com

After installation, pull a supported model. For example:

```bash
ollama pull gemma4:e4b
```

You can verify that Ollama is running using:

```bash
ollama list
```

### 3. Install UV

This project uses [UV](https://docs.astral.sh/uv/) for Python environment and dependency management.

Install UV:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For alternative installation methods, see:

https://docs.astral.sh/uv/getting-started/installation/

### 4. Create a Python Environment

```bash
uv venv --python 3.10
```

Activate the environment:

**macOS/Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### 5. Install Dependencies

```bash
uv pip install -r requirements.txt
```

---

## Running the Application

Run the Streamlit application from the repository root:

```bash
uv run streamlit run src/app.py
```

The application will open automatically in your browser.

---

## Knowledge Base and RAG

The framework uses Retrieval-Augmented Generation (RAG) to incorporate trusted documents into the generation process.

The knowledge base is organised into two categories:

```text
src/knowledge/
├── university/
└── sector/
```

### University Knowledge

The `university/` directory can contain institutional documents such as:

- Module specification guidelines
- Assessment regulations
- Credit and workload policies
- Curriculum frameworks
- Learning and teaching guidance

### Sector Knowledge

The `sector/` directory can contain external documents such as:

- QAA benchmark statements
- Professional body guidelines
- National qualification frameworks
- Accreditation requirements
- Discipline-specific curriculum guidance

### RAG Workflow

The RAG pipeline follows the following process:

```text
Knowledge Documents
        │
        ▼
Document Loading
        │
        ▼
Text Chunking
        │
        ▼
Embedding Generation
        │
        ▼
Vector Database
        │
        ▼
Relevant Context Retrieval
        │
        ▼
LLM Generation
```

The retrieved context is incorporated into the LLM prompt to improve the relevance, consistency, and grounding of the generated module specification.

After adding documents to the knowledge folders, use the application's knowledge indexing functionality to process them for retrieval.

---

## Supported Document Formats

Depending on the configured RAG pipeline, the knowledge base may include:

- PDF
- DOCX
- TXT

It is recommended to use authoritative and up-to-date documents to ensure reliable retrieval and generation.

---

## Large Language Models

The framework uses local Large Language Models through [Ollama](https://ollama.com).

The application can be configured to work with compatible models available through Ollama.

For example:

```bash
ollama pull gemma4:e4b
```

Other Ollama-compatible models can also be used depending on the available computational resources and application configuration.

---

## Generated Outputs

The framework can generate several components of a module specification.

### Module Overview

A high-level description of the module and its academic purpose.

### Module Rationale

An explanation of the relevance, scope, and academic positioning of the module.

### Weekly Syllabus

For each teaching week, the framework can generate:

- Topic
- Learning activities
- ILO mapping
- Scheduled learning hours
- Independent study hours

### Assessments

The framework supports the generation of assessment structures, including:

- Assessment title
- Assessment type
- Weighting
- Description
- Alignment with Intended Learning Outcomes

### Weekly Formative Quizzes

The system can generate formative quiz questions based on weekly topics and learning outcomes.

These quizzes can support:

- Student self-assessment
- Formative feedback
- Knowledge reinforcement
- Continuous learning

### Consistency Verification

The framework evaluates several aspects of the generated specification, including:

- Intended Learning Outcome alignment
- Assessment weighting
- Student workload
- Scheduled learning hours
- Internal consistency between module components

---

## Example Workflow

```text
Module Metadata
      │
      ▼
Intended Learning Outcomes
      │
      ▼
Knowledge Retrieval (RAG)
      │
      ▼
LLM-Based Generation
      │
      ├── Module Overview
      ├── Module Rationale
      ├── Weekly Syllabus
      ├── Assessments
      └── Weekly Quizzes
      │
      ▼
Consistency Verification
      │
      ▼
Structured Module Specification
```

---

## Research Paper

This repository accompanies the following publication:

> Mohamed Elawady and Hazrat Ali. 2026. Bridging Learning Outcomes and Module Specifications: GenAI Framework for Curriculum Development in CS Education. In Proceedings of the 2026 United Kingdom and Ireland Computing Education Research (UKICER 2026). Association for Computing Machinery, New York, NY, USA, Article 21, 1. https://doi.org/10.1145/3830800.3830829

---

## Citation

If you use this repository or framework in your research, please cite:

```bibtex
@inproceedings{elawady2026bridging,
  author    = {Mohamed Elawady and Hazrat Ali},
  title     = {Bridging Learning Outcomes and Module Specifications:
               A GenAI Framework for Curriculum Development in CS Education},
  booktitle = {Proceedings of the United Kingdom and Ireland
               Computing Education Research Conference},
  year      = {2026},
  isbn      = {9798400725937}, 
  publisher = {Association for Computing Machinery}, 
  url       = {https://doi.org/10.1145/3830800.3830829}, 
  doi       = {10.1145/3830800.3830829},
  articleno = {21}, 
  numpages  = {1},
}
```

---

## Limitations

This framework is intended to support academic curriculum development and does not replace academic expertise or institutional quality assurance processes.

Generated outputs should always be reviewed by qualified academic staff.

The quality of the generated specification depends on:

- The selected Large Language Model.
- The quality of the retrieved knowledge sources.
- The completeness of the module metadata.
- The clarity and quality of the Intended Learning Outcomes.
- The relevance and currency of institutional and sector guidelines.

---

## Future Work

Potential future developments include:

- Multi-agent curriculum design workflows.
- Improved automated alignment verification.
- Support for programme-level curriculum mapping.
- Integration with institutional curriculum management systems.
- Human-in-the-loop review and feedback mechanisms.
- Evaluation across multiple disciplines and institutions.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---