from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ILO(BaseModel):
    code: str
    description: str


class ModuleInput(BaseModel):
    module_title: str
    module_code: str
    level: str
    cats: float
    ects: float
    ilos: List[ILO]


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str


class WeeklyTopic(BaseModel):
    week: int
    topic: str
    ilo_mapping: List[str]
    scheduled_learning_hours: float
    independent_study_hours: float
    placement_hours: float = 0.0
    activities: List[str]
    materials: List[str]
    quiz: Optional[List[QuizQuestion]] = []


class Assessment(BaseModel):
    title: str
    type: str  # "summative" or "formative"
    purpose: str
    weighting: float
    mapped_ilos: List[str]
    description: str
    rubric: Dict[str, str]
    genai_usage: str


class TeachingMaterials(BaseModel):
    weekly_slides: List[str]
    tutorials: List[str]


class ModuleSpecification(BaseModel):
    overview: str
    rationale: str
    syllabus: List[WeeklyTopic]
    assessments: List[Assessment]
    teaching_materials: TeachingMaterials
    assumptions: List[str]
    total_scheduled_hours: float = 0.0
    total_independent_hours: float = 0.0
    total_placement_hours: float = 0.0