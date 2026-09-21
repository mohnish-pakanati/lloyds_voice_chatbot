from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class Depth(str, Enum):
    auto = "auto"
    literacy = "literacy"
    practitioner = "practitioner"
    professional = "professional"
    specialist = "specialist"
    research = "research"


class MissionCreate(BaseModel):
    objective: str = Field(min_length=8, max_length=1200)
    expected_outcome: str | None = Field(default=None, max_length=1200)
    hours_per_week: int = Field(default=5, ge=1, le=40)
    prior_experience: Literal["none", "some", "experienced"] = "some"
    intensity: Literal["gentle", "focused", "intensive"] = "focused"
    depth: Depth = Depth.auto
    deadline: datetime | None = None

    @field_validator("objective", "expected_outcome")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class MissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    objective: str
    outcome: str
    depth: int
    depth_label: str
    hours_per_week: int
    prior_experience: str
    intensity: str
    status: str
    estimated_hours: str
    prerequisites: list[str]
    target_capabilities: list[str]
    course_version: str


class SourceSchema(BaseModel):
    title: str
    url: HttpUrl
    source_type: str
    author_publisher: str
    authority_level: int = Field(ge=1, le=8)
    freshness: float = Field(ge=0, le=1)
    relevance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    classification: Literal["FOUNDATIONAL", "CURRENT_PRACTICE", "FRONTIER"]


class SkillSchema(BaseModel):
    id: str
    name: str
    category: str
    classification: Literal["FOUNDATIONAL", "CURRENT_PRACTICE", "FRONTIER"]
    dependencies: list[str] = []
    capabilities: list[str]


class PhaseSchema(BaseModel):
    id: str
    title: str
    purpose: str
    skill_ids: list[str]
    generated: bool = False


class ProjectSchema(BaseModel):
    title: str
    brief: str
    rubric: dict[str, float]


class CourseManifest(BaseModel):
    mission_title: str
    course_version: str
    last_researched_at: datetime
    estimated_hours: str
    depth: int = Field(ge=1, le=5)
    prerequisites: list[str]
    target_capabilities: list[str]
    skills: list[SkillSchema]
    phases: list[PhaseSchema]
    assessment_types: list[str]
    sources: list[SourceSchema]
    project: ProjectSchema

    @field_validator("skills")
    @classmethod
    def unique_skills(cls, skills: list[SkillSchema]) -> list[SkillSchema]:
        ids = [item.id for item in skills]
        if len(ids) != len(set(ids)):
            raise ValueError("skill ids must be unique")
        known = set(ids)
        for skill in skills:
            if not set(skill.dependencies).issubset(known):
                raise ValueError(f"unknown dependency for {skill.id}")
            if skill.id in skill.dependencies:
                raise ValueError("a skill cannot depend on itself")
        return skills


class EvidenceInput(BaseModel):
    skill_id: str
    dimension: Literal["concept", "explanation", "implementation", "debugging", "design", "transfer"]
    assessment_type: str
    mode: Literal["learning", "assessment", "real_world"] = "learning"
    difficulty: float = Field(ge=0, le=1)
    correctness: float = Field(ge=0, le=1)
    hint_level: int = Field(default=0, ge=0, le=5)
    learner_confidence: float = Field(ge=0, le=1)
    independent: bool = True
    answer: dict = {}
    misconception_detected: str | None = None


class MasteryRead(BaseModel):
    skill_id: str
    skill_name: str
    concept: float
    explanation: float
    implementation: float
    debugging: float
    design: float
    transfer: float
    evidence_count: int
    retention_confidence: float
    confidence_calibration: float
    hint_dependency: float
    status: str
    review_due_at: datetime | None


class DiagnosticAnswer(BaseModel):
    question_id: str
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)


class DiagnosticSubmit(BaseModel):
    answers: list[DiagnosticAnswer]


class CodeRunRequest(BaseModel):
    code: str = Field(max_length=20_000)
    visible_tests: str = Field(default="", max_length=10_000)
    hidden_tests: str = Field(default="", max_length=10_000)


class ProjectScoreRequest(BaseModel):
    automated_score: float = Field(ge=0, le=1)
    rubric_scores: dict[str, float]
    review_score: float = Field(ge=0, le=1)


class StructuredTeacherOutput(BaseModel):
    mode: Literal["TEACHER", "SOCRATIC", "ASSESSMENT", "CODE_REVIEW", "DEBUGGING_MENTOR", "VIVA", "PROJECT_REVIEWER"]
    message: str
    next_action: Literal["attempt", "hint", "teach", "retest", "advance"]
    citations: list[str] = []
    misconception: str | None = None
