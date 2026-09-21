from datetime import datetime, timedelta, timezone


class LearningScienceService:
    intervals = (1, 3, 7, 14, 30)

    def next_review(self, performance: float, interval_index: int, *, now: datetime | None = None) -> tuple[datetime, int]:
        now = now or datetime.now(timezone.utc)
        if performance < 0.55:
            next_index = max(0, interval_index - 1)
        elif performance >= 0.82:
            next_index = min(len(self.intervals) - 1, interval_index + 1)
        else:
            next_index = interval_index
        return now + timedelta(days=self.intervals[next_index]), next_index

    def choose_activity(self, mastery: float, failures: int, hint_dependency: float) -> str:
        if failures >= 2:
            return "targeted_remediation"
        if hint_dependency > 0.55:
            return "faded_independent_practice"
        if mastery >= 0.82:
            return "transfer_or_accelerate"
        if mastery >= 0.55:
            return "interleaved_application"
        return "worked_example"

    def session_plan(self) -> list[dict]:
        return [
            {"kind": "retrieval", "minutes": 3, "label": "Recall a prior decision rule"},
            {"kind": "lesson", "minutes": 9, "label": "LoRA: rank and adaptation"},
            {"kind": "misconception_check", "minutes": 3, "label": "Quantized storage vs trainable weights"},
            {"kind": "scenario", "minutes": 7, "label": "Choose under a 16 GB constraint"},
        ]
