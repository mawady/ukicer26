# Bridging Learning Outcomes and Module Specifications: GenAI Framework for Curriculum Development in CS Education

##  Citation

```ACM reference
Mohamed Elawady and Hazrat Ali. 2026. Bridging Learning Outcomes and Module Specifications: GenAI Framework for Curriculum Development in CS Education. In Proceedings of the 2026 United Kingdom and Ireland Computing Education Research (UKICER 2026). Association for Computing Machinery, New York, NY, USA, Article 21, 1. https://doi.org/10.1145/3830800.3830829
```

## Installation

1. Install Ollama and pull a model, for example:

```bash
ollama pull gemma4:e4b
```

2. Create a virtual environment:

```bash
uv venv --python 3.10
source .venv/bin/activate      # Linux/macOS
```

3. Install dependencies:

```bash
uv pip install -r requirements.txt
```

4. Place trusted PDF, DOCX or TXT documents in:

```text
src/knowledge/university/
src/knowledge/sector/
```

5. Run:

```bash
uv run streamlit run app.py
```