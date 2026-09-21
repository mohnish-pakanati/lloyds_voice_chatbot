from fastapi.testclient import TestClient
from app.main import app


HEADERS = {"X-User-ID": "demo-user"}


def test_api_authorization_boundary():
    with TestClient(app) as client:
        assert client.get("/api/v1/demo/manifest").status_code == 401
        assert client.get("/api/v1/demo/manifest", headers={"X-User-ID": "not-a-user"}).status_code == 403
        assert client.get("/api/v1/demo/manifest", headers=HEADERS).status_code == 200


def test_end_to_end_failure_remediation_retest_mastery_memory_queue():
    with TestClient(app) as client:
        mission = client.post("/api/v1/missions", headers=HEADERS, json={"objective": "I want to learn LLM fine-tuning professionally.", "depth": "auto"})
        assert mission.status_code == 201 and mission.json()["depth"] == 3
        diagnostic = client.post("/api/v1/diagnostic", headers=HEADERS, json={"answers": [{"question_id": "d1", "score": .5, "confidence": .8}]})
        assert diagnostic.json()["start_phase"] == "phase-1"
        failed = client.post("/api/v1/evidence", headers=HEADERS, json={"skill_id": "qlora", "dimension": "debugging", "assessment_type": "scenario", "difficulty": .7, "correctness": .2, "hint_level": 0, "learner_confidence": .9, "independent": True})
        assert failed.json()["next_action"] == "targeted_remediation"
        assert failed.json()["misconception_detected"]
        retest = client.post("/api/v1/evidence", headers=HEADERS, json={"skill_id": "qlora", "dimension": "debugging", "assessment_type": "novel_transfer", "mode": "assessment", "difficulty": .75, "correctness": .9, "hint_level": 0, "learner_confidence": .8, "independent": True})
        assert retest.json()["updated"] > failed.json()["updated"]
        report = client.get("/api/v1/skills/report", headers=HEADERS)
        qlora = next(skill for skill in report.json()["skills"] if skill["skill_id"] == "qlora")
        assert qlora["evidence_count"] >= 2
        queue = client.get("/api/v1/sessions/recommended", headers=HEADERS)
        assert queue.status_code == 200 and len(queue.json()["items"]) == 4
