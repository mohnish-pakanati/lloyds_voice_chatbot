from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


def uid() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LearningMission(Base):
    __tablename__ = "learning_missions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    objective: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(Text)
    depth: Mapped[int] = mapped_column(Integer)
    depth_label: Mapped[str] = mapped_column(String(32))
    hours_per_week: Mapped[int] = mapped_column(Integer, default=5)
    prior_experience: Mapped[str] = mapped_column(String(32), default="some")
    intensity: Mapped[str] = mapped_column(String(32), default="focused")
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey("learning_missions.id"), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    active_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CourseVersion(Base):
    __tablename__ = "course_versions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"), index=True)
    version: Mapped[str] = mapped_column(String(24))
    last_researched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    manifest: Mapped[dict] = mapped_column(JSON, default=dict)


class Phase(Base):
    __tablename__ = "phases"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    course_version_id: Mapped[str] = mapped_column(ForeignKey("course_versions.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    position: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="locked")


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course_version_id: Mapped[str | None] = mapped_column(ForeignKey("course_versions.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80))
    classification: Mapped[str] = mapped_column(String(32), default="FOUNDATIONAL")
    target_depth: Mapped[int] = mapped_column(Integer, default=3)


class SkillDependency(Base):
    __tablename__ = "skill_dependencies"
    __table_args__ = (UniqueConstraint("skill_id", "prerequisite_skill_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"))
    prerequisite_skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"))


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    phase_id: Mapped[str] = mapped_column(ForeignKey("phases.id"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    position: Mapped[int] = mapped_column(Integer)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict] = mapped_column(JSON, default=dict)


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    activity_id: Mapped[str | None] = mapped_column(ForeignKey("activities.id"), nullable=True)
    assessment_type: Mapped[str] = mapped_column(String(40))
    mode: Mapped[str] = mapped_column(String(32), default="learning")
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)
    prompt: Mapped[str] = mapped_column(Text)
    rubric: Mapped[dict] = mapped_column(JSON, default=dict)


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    assessment_id: Mapped[str | None] = mapped_column(ForeignKey("assessments.id"), nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    answer: Mapped[dict] = mapped_column(JSON, default=dict)
    correctness: Mapped[float] = mapped_column(Float)
    learner_confidence: Mapped[float] = mapped_column(Float)
    hint_level: Mapped[int] = mapped_column(Integer, default=0)
    independent: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AssessmentEvidence(Base):
    __tablename__ = "assessment_evidence"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("assessment_attempts.id"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(32))
    assessment_type: Mapped[str] = mapped_column(String(40))
    difficulty: Mapped[float] = mapped_column(Float)
    correctness: Mapped[float] = mapped_column(Float)
    hint_level: Mapped[int] = mapped_column(Integer)
    learner_confidence: Mapped[float] = mapped_column(Float)
    independent: Mapped[bool] = mapped_column(Boolean)
    misconception_detected: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SkillMastery(Base):
    __tablename__ = "skill_mastery"
    __table_args__ = (UniqueConstraint("user_id", "skill_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    concept: Mapped[float] = mapped_column(Float, default=0.2)
    explanation: Mapped[float] = mapped_column(Float, default=0.2)
    implementation: Mapped[float] = mapped_column(Float, default=0.2)
    debugging: Mapped[float] = mapped_column(Float, default=0.2)
    design: Mapped[float] = mapped_column(Float, default=0.2)
    transfer: Mapped[float] = mapped_column(Float, default=0.2)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    retention_confidence: Mapped[float] = mapped_column(Float, default=0.2)
    confidence_calibration: Mapped[float] = mapped_column(Float, default=0.5)
    hint_dependency: Mapped[float] = mapped_column(Float, default=0.0)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Misconception(Base):
    __tablename__ = "misconceptions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    label: Mapped[str] = mapped_column(String(240))
    related_prerequisite: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="active")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HintUsage(Base):
    __tablename__ = "hint_usage"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("assessment_attempts.id"), index=True)
    level: Mapped[int] = mapped_column(Integer)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ReviewSchedule(Base):
    __tablename__ = "review_schedules"
    __table_args__ = (UniqueConstraint("user_id", "skill_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    interval_index: Mapped[int] = mapped_column(Integer, default=0)
    review_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_score: Mapped[float] = mapped_column(Float, default=0.0)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(Text, unique=True)
    source_type: Mapped[str] = mapped_column(String(40))
    author_publisher: Mapped[str] = mapped_column(String(200))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    authority_level: Mapped[int] = mapped_column(Integer)
    freshness: Mapped[float] = mapped_column(Float)
    topics: Mapped[list] = mapped_column(JSON, default=list)
    relevance: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)


class SourceReference(Base):
    __tablename__ = "source_references"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(64), index=True)


class LearningSession(Base):
    __tablename__ = "learning_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    mission_id: Mapped[str] = mapped_column(ForeignKey("learning_missions.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    plan: Mapped[dict] = mapped_column(JSON, default=dict)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    course_version_id: Mapped[str] = mapped_column(ForeignKey("course_versions.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    brief: Mapped[str] = mapped_column(Text)
    rubric: Mapped[dict] = mapped_column(JSON)


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ProjectEvaluation(Base):
    __tablename__ = "project_evaluations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey("project_submissions.id"), index=True)
    automated_score: Mapped[float] = mapped_column(Float)
    rubric_score: Mapped[float] = mapped_column(Float)
    review_score: Mapped[float] = mapped_column(Float)
    total_score: Mapped[float] = mapped_column(Float)
    evidence: Mapped[dict] = mapped_column(JSON)


class Viva(Base):
    __tablename__ = "vivas"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey("project_submissions.id"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="pending")


class VivaQuestion(Base):
    __tablename__ = "viva_questions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    viva_id: Mapped[str] = mapped_column(ForeignKey("vivas.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)


class VivaResponse(Base):
    __tablename__ = "viva_responses"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    question_id: Mapped[str] = mapped_column(ForeignKey("viva_questions.id"), index=True)
    response: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    evidence: Mapped[str] = mapped_column(Text)
