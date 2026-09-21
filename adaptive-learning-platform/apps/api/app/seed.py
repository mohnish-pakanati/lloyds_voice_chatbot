from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import ReviewSchedule, Skill, SkillMastery, User
from .services.compiler import demo_manifest


DEMO_USER_ID = "demo-user"


def seed_demo(db: Session) -> None:
    if db.get(User, DEMO_USER_ID):
        return
    db.add(User(id=DEMO_USER_ID, email="learner@example.test", display_name="Demo learner"))
    manifest = demo_manifest()
    for index, item in enumerate(manifest.skills):
        db.add(Skill(id=item.id, name=item.name, category=item.category, classification=item.classification, target_depth=manifest.depth))
        baseline = 0.78 if item.id == "decision" else max(0.18, 0.48 - index * 0.035)
        db.add(SkillMastery(user_id=DEMO_USER_ID, skill_id=item.id, concept=baseline, explanation=max(0.15, baseline - .08), implementation=max(0.12, baseline - .16), debugging=max(0.1, baseline - .25), design=max(0.1, baseline - .18), transfer=max(0.1, baseline - .22)))
        db.add(ReviewSchedule(user_id=DEMO_USER_ID, skill_id=item.id, interval_index=0, review_due_at=datetime.now(timezone.utc) + timedelta(days=1), last_score=baseline))
    db.commit()
