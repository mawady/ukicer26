import json
import re
from ollama import chat
from models import ModuleInput, ModuleSpecification

SYSTEM_PROMPT = """
You are an expert academic curriculum designer.

Your task is to propose a high-quality module specification based on the provided inputs.
If RETRIEVED KNOWLEDGE is empty, rely entirely on standard Higher Education pedagogical frameworks, Bloom's Taxonomy, credit frameworks (e.g., QAA/SCQF/CATS standards), and your internal parametric memory.

ASSESSMENT RULES:
- Summative assessments must sum to EXACTLY 100% total weighting.
- Formative assessments can be included for practice/feedback, but MUST have a weighting of 0%.

Ensure:
- Constructive alignment between ILOs, syllabus topics, and quizzes.
- Include a 2-question multiple choice quiz for each week's topic.
- All ILOs are covered across syllabus and assessment mappings.

Generate JSON only.
"""


class SuggestionEngine:
    def __init__(self, model="gemma4:e2b"):
        self.model = model

    def _extract_json(self, text: str) -> dict:
        text = text.strip()
        text = re.sub(r"^```json", "", text, flags=re.MULTILINE)
        text = re.sub(r"^```", "", text, flags=re.MULTILINE)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= 0:
            text = text[start:end + 1]
        return json.loads(text)

    def _format_context_for_prompt(self, context: list) -> str:
        if not context:
            return "No local files indexed. Relying entirely on model parametric memory."

        formatted_blocks = []
        for idx, item in enumerate(context, 1):
            source = item.get("source", "Unknown File")
            level = item.get("source_level", "General")
            content = item.get("content", "").strip()

            block = (
                f"--- KNOWLEDGE ENTRY #{idx} ---\n"
                f"Category: {level}\n"
                f"Source Document: {source}\n"
                f"Excerpt:\n{content}\n"
            )
            formatted_blocks.append(block)

        return "\n".join(formatted_blocks)

    def generate(self, module_input: ModuleInput, context: list,
                 reviewer_feedback: str = "", failed_checks: list = None) -> ModuleSpecification:
        context_text = self._format_context_for_prompt(context)

        prompt = f"""
MODULE INPUT:
{module_input.model_dump_json(indent=2)}

RETRIEVED KNOWLEDGE:
{context_text}

FAILED CHECKS FROM PREVIOUS RUN:
{failed_checks or ["None"]}

USER FEEDBACK / ADJUSTMENTS:
{reviewer_feedback or "None"}

Respond strictly with valid JSON following this structure:
{{
  "overview": "...",
  "rationale": "...",
  "syllabus": [
    {{
      "week": 1,
      "topic": "...",
      "ilo_mapping": ["ILO1"],
      "scheduled_learning_hours": 3,
      "independent_study_hours": 7,
      "placement_hours": 0,
      "activities": ["Lecture"],
      "materials": ["Slides"],
      "quiz": [
        {{
          "question": "Sample Question?",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_answer": "Option A"
        }}
      ]
    }}
  ],
  "assessments": [
    {{
      "title": "Summative Coursework",
      "type": "summative",
      "purpose": "Evaluate overall performance",
      "weighting": 100,
      "mapped_ilos": ["ILO1"],
      "description": "...",
      "rubric": {{"Criterion": "Description"}},
      "genai_usage": "Permitted with citation"
    }},
    {{
      "title": "Formative Practice Quiz",
      "type": "formative",
      "purpose": "Provide early feedback",
      "weighting": 0,
      "mapped_ilos": ["ILO1"],
      "description": "...",
      "rubric": {{"Criterion": "Description"}},
      "genai_usage": "Permitted"
    }}
  ],
  "teaching_materials": {{
    "weekly_slides": ["Week 1 Slides"],
    "tutorials": []
  }},
  "assumptions": []
}}
"""

        response = chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.2}
        )

        data = self._extract_json(response.message.content)

        syllabus = data.get("syllabus", [])
        data["total_scheduled_hours"] = sum(w.get("scheduled_learning_hours", 0) for w in syllabus)
        data["total_independent_hours"] = sum(w.get("independent_study_hours", 0) for w in syllabus)
        data["total_placement_hours"] = sum(w.get("placement_hours", 0) for w in syllabus)

        return ModuleSpecification(**data)