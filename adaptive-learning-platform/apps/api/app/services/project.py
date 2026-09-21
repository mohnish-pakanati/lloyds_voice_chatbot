class ProjectEvaluationService:
    def aggregate(self, automated: float, rubric_scores: dict[str, float], review: float) -> dict:
        if not rubric_scores:
            raise ValueError("rubric evidence is required")
        rubric = sum(rubric_scores.values()) / len(rubric_scores)
        total = automated * 0.4 + rubric * 0.4 + review * 0.2
        return {
            "automated_score": round(automated, 3),
            "rubric_score": round(rubric, 3),
            "review_score": round(review, 3),
            "total_score": round(total, 3),
            "evidence": {"rubric_dimensions": rubric_scores, "weights": {"automated": 0.4, "rubric": 0.4, "review": 0.2}},
        }
