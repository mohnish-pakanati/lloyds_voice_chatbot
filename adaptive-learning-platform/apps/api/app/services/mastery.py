from dataclasses import dataclass
from datetime import datetime, timezone


DIMENSIONS = ("concept", "explanation", "implementation", "debugging", "design", "transfer")


@dataclass(frozen=True)
class Evidence:
    dimension: str
    correctness: float
    difficulty: float
    hint_level: int
    learner_confidence: float
    independent: bool
    mode: str = "learning"


class MasteryService:
    """Transparent, replaceable evidence-weighted updater; scores are product estimates."""

    def update(self, current: float, evidence: Evidence, evidence_count: int) -> float:
        hint_factor = max(0.35, 1 - 0.11 * evidence.hint_level)
        independence_factor = 1.0 if evidence.independent else 0.78
        mode_factor = {"learning": 0.88, "assessment": 1.0, "real_world": 0.94}[evidence.mode]
        difficulty_factor = 0.8 + 0.4 * evidence.difficulty
        observed = evidence.correctness * hint_factor * independence_factor
        observed = min(1.0, observed * difficulty_factor * mode_factor)
        alpha = max(0.16, 0.42 / (1 + evidence_count * 0.08))
        return round(max(0.0, min(1.0, current * (1 - alpha) + observed * alpha)), 4)

    def hint_dependency(self, current: float, hint_level: int, evidence_count: int) -> float:
        observed = hint_level / 5
        alpha = 0.35 if evidence_count < 4 else 0.2
        return round(current * (1 - alpha) + observed * alpha, 4)

    def confidence_calibration(self, current: float, correctness: float, confidence: float) -> float:
        calibration = 1 - abs(correctness - confidence)
        return round(current * 0.7 + calibration * 0.3, 4)

    def probable_misconception(self, correctness: float, confidence: float) -> bool:
        return correctness < 0.45 and confidence >= 0.75

    def status(self, values: list[float]) -> str:
        weakest = min(values)
        mean = sum(values) / len(values)
        if weakest >= 0.72 and mean >= 0.8:
            return "Stable"
        if mean >= 0.48:
            return "Developing"
        return "Needs reinforcement"

    @staticmethod
    def verified_now() -> datetime:
        return datetime.now(timezone.utc)
