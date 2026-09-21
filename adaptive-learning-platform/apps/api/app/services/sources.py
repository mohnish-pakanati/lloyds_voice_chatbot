from datetime import datetime, timezone


AUTHORITY = {
    "paper": 8,
    "specification": 8,
    "official_docs": 7,
    "official_repository": 6,
    "maintainer": 5,
    "course": 4,
    "practitioner": 3,
    "community": 1,
}


class SourceEvaluationService:
    def rank(self, source_type: str, relevance: float, freshness: float, confidence: float) -> float:
        authority = AUTHORITY.get(source_type, 1) / 8
        return round(authority * 0.45 + relevance * 0.30 + freshness * 0.15 + confidence * 0.10, 4)

    def freshness(self, published_at: datetime | None, volatile: bool, *, now: datetime | None = None) -> float:
        if not published_at:
            return 0.5
        now = now or datetime.now(timezone.utc)
        age_days = max(0, (now - published_at).days)
        horizon = 365 if volatile else 3650
        return round(max(0.0, 1 - age_days / horizon), 4)

    @staticmethod
    def sanitize_external_text(text: str) -> str:
        blocked = ("ignore previous instructions", "system message", "developer message", "reveal secrets")
        lines = [line for line in text.splitlines() if not any(token in line.lower() for token in blocked)]
        return "\n".join(lines)[:50_000]
