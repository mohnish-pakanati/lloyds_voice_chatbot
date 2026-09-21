from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .models import AssessmentAttempt, AssessmentEvidence, LearningMission, Misconception, ReviewSchedule, Skill, SkillMastery, User
from .schemas import CodeRunRequest, DiagnosticSubmit, EvidenceInput, MissionCreate, ProjectScoreRequest
from .seed import DEMO_USER_ID, seed_demo
from .services.code_runner import DockerCodeRunner
from .services.compiler import CourseCompiler, demo_manifest
from .services.depth import DepthEngine
from .services.learning_science import LearningScienceService
from .services.mastery import DIMENSIONS, Evidence, MasteryService
from .services.project import ProjectEvaluationService

logger = logging.getLogger("adaptive")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_demo(db)
    logger.info("application_started", extra={"environment": settings.environment, "llm_provider": settings.llm_provider})
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=False)


def current_user(x_user_id: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if settings.auth_required and not x_user_id:
        raise HTTPException(401, "X-User-ID is required")
    user_id = x_user_id or DEMO_USER_ID
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(403, "Unknown user")
    return user


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "1.0.0", "providers": {"llm": settings.llm_provider, "research": settings.research_provider}}


@app.post("/api/v1/missions", status_code=201)
def create_mission(payload: MissionCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    depth, depth_label = DepthEngine().select(payload)
    manifest = CourseCompiler().compile(payload.objective, depth)
    mission = LearningMission(
        user_id=user.id,
        objective=payload.objective,
        outcome=payload.expected_outcome or "Independent implementation and design competency",
        depth=depth,
        depth_label=depth_label,
        hours_per_week=payload.hours_per_week,
        prior_experience=payload.prior_experience,
        intensity=payload.intensity,
        deadline=payload.deadline,
        status="ready_for_review",
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    logger.info("mission_created", extra={"mission_id": mission.id, "depth": depth})
    return {
        "id": mission.id, "objective": mission.objective, "outcome": mission.outcome,
        "depth": depth, "depth_label": depth_label, "hours_per_week": mission.hours_per_week,
        "prior_experience": mission.prior_experience, "intensity": mission.intensity,
        "status": mission.status, "estimated_hours": manifest.estimated_hours,
        "prerequisites": manifest.prerequisites, "target_capabilities": manifest.target_capabilities,
        "course_version": manifest.course_version,
    }


@app.get("/api/v1/demo/manifest")
def get_manifest(_: User = Depends(current_user)) -> dict:
    return demo_manifest().model_dump(mode="json")


@app.get("/api/v1/diagnostic")
def diagnostic(_: User = Depends(current_user)) -> dict:
    return {
        "questions": [
            {"id": "d1", "type": "scenario", "skill_id": "decision", "prompt": "A team wants to add fresh private facts to a model every hour. Would you start with prompting, RAG, or fine-tuning—and what fact would change your answer?"},
            {"id": "d2", "type": "explanation", "skill_id": "lora", "prompt": "Why can low-rank adapters change behavior while updating a small fraction of parameters?"},
            {"id": "d3", "type": "debugging", "skill_id": "qlora", "prompt": "A 14B full fine-tune OOMs on one 16 GB GPU. Name the first two interventions you would evaluate and why."},
        ],
        "instruction": "Answer briefly. Say what you do not know; confidence is evidence too.",
    }


@app.post("/api/v1/diagnostic")
def submit_diagnostic(payload: DiagnosticSubmit, _: User = Depends(current_user)) -> dict:
    mean = sum(item.score for item in payload.answers) / max(1, len(payload.answers))
    return {
        "placement": "accelerated" if mean >= .8 else "standard" if mean >= .45 else "foundation_first",
        "skip_skills": ["decision"] if mean >= .8 else [],
        "start_phase": "phase-1",
        "reason": "Placement uses demonstrated performance and calibration, not self-report alone.",
    }


@app.get("/api/v1/sessions/recommended")
def recommended_session(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    due = db.scalars(select(ReviewSchedule).where(ReviewSchedule.user_id == user.id, ReviewSchedule.review_due_at <= datetime.now(timezone.utc))).all()
    plan = LearningScienceService().session_plan()
    return {"recommended_minutes": sum(item["minutes"] for item in plan), "due_count": len(due), "items": plan}


@app.post("/api/v1/evidence")
def record_evidence(payload: EvidenceInput, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    skill = db.get(Skill, payload.skill_id)
    if not skill:
        raise HTTPException(404, "Unknown skill")
    mastery = db.scalar(select(SkillMastery).where(SkillMastery.user_id == user.id, SkillMastery.skill_id == payload.skill_id))
    if not mastery:
        mastery = SkillMastery(user_id=user.id, skill_id=payload.skill_id)
        db.add(mastery)
        db.flush()
    service = MasteryService()
    previous = getattr(mastery, payload.dimension)
    evidence = Evidence(payload.dimension, payload.correctness, payload.difficulty, payload.hint_level, payload.learner_confidence, payload.independent, payload.mode)
    updated = service.update(previous, evidence, mastery.evidence_count)
    setattr(mastery, payload.dimension, updated)
    mastery.hint_dependency = service.hint_dependency(mastery.hint_dependency, payload.hint_level, mastery.evidence_count)
    mastery.confidence_calibration = service.confidence_calibration(mastery.confidence_calibration, payload.correctness, payload.learner_confidence)
    mastery.retention_confidence = round(mastery.retention_confidence * .7 + updated * .3, 4)
    mastery.evidence_count += 1
    mastery.last_verified_at = service.verified_now()
    misconception_label = payload.misconception_detected
    probable = service.probable_misconception(payload.correctness, payload.learner_confidence)
    if probable and not misconception_label:
        misconception_label = "Confident incorrect model requiring targeted diagnosis"
    attempt = AssessmentAttempt(user_id=user.id, answer=payload.answer, correctness=payload.correctness, learner_confidence=payload.learner_confidence, hint_level=payload.hint_level, independent=payload.independent)
    db.add(attempt)
    db.flush()
    db.add(AssessmentEvidence(attempt_id=attempt.id, skill_id=payload.skill_id, dimension=payload.dimension, assessment_type=payload.assessment_type, difficulty=payload.difficulty, correctness=payload.correctness, hint_level=payload.hint_level, learner_confidence=payload.learner_confidence, independent=payload.independent, misconception_detected=misconception_label))
    if misconception_label:
        db.add(Misconception(user_id=user.id, skill_id=payload.skill_id, label=misconception_label, related_prerequisite="Mixed-precision training" if payload.skill_id == "qlora" else None))
    schedule = db.scalar(select(ReviewSchedule).where(ReviewSchedule.user_id == user.id, ReviewSchedule.skill_id == payload.skill_id))
    due, interval_index = LearningScienceService().next_review(payload.correctness, schedule.interval_index if schedule else 0)
    if schedule:
        schedule.review_due_at, schedule.interval_index, schedule.last_score = due, interval_index, payload.correctness
    else:
        db.add(ReviewSchedule(user_id=user.id, skill_id=payload.skill_id, review_due_at=due, interval_index=interval_index, last_score=payload.correctness))
    db.commit()
    values = [getattr(mastery, item) for item in DIMENSIONS]
    logger.info("mastery_changed", extra={"user_id": user.id, "skill_id": skill.id, "dimension": payload.dimension, "before": previous, "after": updated})
    return {"skill_id": skill.id, "dimension": payload.dimension, "previous": previous, "updated": updated, "status": service.status(values), "hint_dependency": mastery.hint_dependency, "misconception_detected": misconception_label, "review_due_at": due.isoformat(), "next_action": "targeted_remediation" if misconception_label or payload.correctness < .5 else LearningScienceService().choose_activity(updated, 0, mastery.hint_dependency)}


@app.get("/api/v1/skills/report")
def skill_report(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(SkillMastery, Skill).join(Skill, Skill.id == SkillMastery.skill_id).where(SkillMastery.user_id == user.id)).all()
    schedules = {item.skill_id: item for item in db.scalars(select(ReviewSchedule).where(ReviewSchedule.user_id == user.id)).all()}
    service = MasteryService()
    skills = []
    for mastery, skill in rows:
        values = [getattr(mastery, dimension) for dimension in DIMENSIONS]
        skills.append({"skill_id": skill.id, "skill_name": skill.name, **{d: getattr(mastery, d) for d in DIMENSIONS}, "evidence_count": mastery.evidence_count, "retention_confidence": mastery.retention_confidence, "confidence_calibration": mastery.confidence_calibration, "hint_dependency": mastery.hint_dependency, "status": service.status(values), "last_verified_at": mastery.last_verified_at, "review_due_at": schedules.get(skill.id).review_due_at if skill.id in schedules else None})
    return {"learner_id": user.id, "disclaimer": "Scores are deterministic product estimates derived from evidence, not scientific probabilities.", "skills": skills}


@app.post("/api/v1/code/run")
def run_code(payload: CodeRunRequest, _: User = Depends(current_user)) -> dict:
    logger.info("code_execution_requested", extra={"code_length": len(payload.code)})
    runner = DockerCodeRunner(settings.code_runner_image, settings.code_runner_timeout_seconds, settings.code_runner_work_root, settings.code_runner_in_container)
    return runner.run(payload.code, payload.visible_tests, payload.hidden_tests).to_dict()


@app.post("/api/v1/projects/evaluate")
def evaluate_project(payload: ProjectScoreRequest, _: User = Depends(current_user)) -> dict:
    result = ProjectEvaluationService().aggregate(payload.automated_score, payload.rubric_scores, payload.review_score)
    logger.info("project_evaluated", extra={"score": result["total_score"]})
    return result


@app.post("/api/v1/viva/questions")
def viva_questions(_: User = Depends(current_user)) -> dict:
    return {"questions": [
        {"prompt": "Why did you choose QLoRA, and which observed constraint ruled out your strongest alternative?", "tests": "decision evidence"},
        {"prompt": "If hardware changed to 4×A100, which parts of your strategy would and would not change?", "tests": "counterfactual transfer"},
        {"prompt": "Validation loss improved while downstream accuracy fell. Give three plausible explanations and the first discriminating test.", "tests": "debugging"},
        {"prompt": "What evidence would make you reverse your current design decision?", "tests": "calibration"},
    ]}
