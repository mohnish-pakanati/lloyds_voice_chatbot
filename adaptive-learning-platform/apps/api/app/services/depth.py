from ..schemas import Depth, MissionCreate


LABELS = {1: "Literacy", 2: "Practitioner", 3: "Professional", 4: "Specialist", 5: "Research / Frontier"}
OVERRIDES = {
    Depth.literacy: 1,
    Depth.practitioner: 2,
    Depth.professional: 3,
    Depth.specialist: 4,
    Depth.research: 5,
}


class DepthEngine:
    professional_terms = {"professionally", "production", "architect", "implement", "debug", "deploy", "job"}
    literacy_terms = {"understand", "discuss", "overview", "literacy", "basics"}
    research_terms = {"research", "frontier", "publish", "novel"}

    def select(self, mission: MissionCreate) -> tuple[int, str]:
        if mission.depth != Depth.auto:
            value = OVERRIDES[mission.depth]
            return value, LABELS[value]
        text = f"{mission.objective} {mission.expected_outcome or ''}".lower()
        if any(term in text for term in self.research_terms):
            value = 5
        elif any(term in text for term in self.professional_terms):
            value = 3
        elif any(term in text for term in self.literacy_terms):
            value = 1
        else:
            value = 2
        if mission.prior_experience == "experienced" and value < 4 and "architect" in text:
            value += 1
        if mission.hours_per_week <= 2 and value > 2:
            value -= 1
        return value, LABELS[value]
