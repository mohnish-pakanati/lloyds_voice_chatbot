from datetime import datetime, timezone
from ..schemas import CourseManifest


def demo_manifest(depth: int = 3) -> CourseManifest:
    raw = {
        "mission_title": "LLM Fine-tuning",
        "course_version": "2026.09",
        "last_researched_at": datetime(2026, 9, 21, tzinfo=timezone.utc),
        "estimated_hours": "24–30 focused hours" if depth >= 3 else "10–14 focused hours",
        "depth": depth,
        "prerequisites": ["Transformer fundamentals", "PyTorch basics", "LLM inference concepts"],
        "target_capabilities": [
            "Decide whether fine-tuning is appropriate",
            "Choose between SFT, LoRA, QLoRA, RAG, and prompting",
            "Prepare and validate training datasets",
            "Configure and debug constrained training runs",
            "Evaluate behavior and justify trade-offs",
            "Serve and monitor adapters",
        ],
        "skills": [
            {"id": "decision", "name": "Fine-tuning decisions", "category": "Decisions", "classification": "FOUNDATIONAL", "dependencies": [], "capabilities": ["Distinguish behavior adaptation from knowledge retrieval", "Reject fine-tuning when a cheaper intervention fits"]},
            {"id": "data", "name": "Dataset design", "category": "Data", "classification": "FOUNDATIONAL", "dependencies": ["decision"], "capabilities": ["Design representative examples", "Detect leakage and format defects"]},
            {"id": "sft", "name": "Supervised fine-tuning", "category": "Training", "classification": "FOUNDATIONAL", "dependencies": ["data"], "capabilities": ["Configure SFT", "Reason about loss and hyperparameters"]},
            {"id": "lora", "name": "LoRA", "category": "PEFT", "classification": "CURRENT_PRACTICE", "dependencies": ["sft"], "capabilities": ["Choose rank and target modules", "Implement adapter training"]},
            {"id": "quantization", "name": "Quantization", "category": "Efficiency", "classification": "CURRENT_PRACTICE", "dependencies": ["sft"], "capabilities": ["Explain precision trade-offs", "Estimate memory constraints"]},
            {"id": "qlora", "name": "QLoRA", "category": "PEFT", "classification": "CURRENT_PRACTICE", "dependencies": ["lora", "quantization"], "capabilities": ["Configure 4-bit adapter training", "Debug memory failures"]},
            {"id": "evaluation", "name": "Evaluation", "category": "Evidence", "classification": "FOUNDATIONAL", "dependencies": ["data", "sft"], "capabilities": ["Design held-out evaluation", "Diagnose proxy metric failure"]},
            {"id": "production", "name": "Production adapters", "category": "Production", "classification": "CURRENT_PRACTICE", "dependencies": ["qlora", "evaluation"], "capabilities": ["Serve adapters", "Monitor regressions"]},
            {"id": "preference", "name": "Preference optimization", "category": "Alignment", "classification": "FRONTIER", "dependencies": ["sft", "evaluation"], "capabilities": ["Judge when preference optimization is justified"]},
        ],
        "phases": [
            {"id": "phase-1", "title": "Make the right intervention", "purpose": "Decide whether and what to train before touching a training loop.", "skill_ids": ["decision", "data"], "generated": True},
            {"id": "phase-2", "title": "Train efficiently", "purpose": "Implement SFT and parameter-efficient methods under realistic constraints.", "skill_ids": ["sft", "lora", "quantization", "qlora"], "generated": False},
            {"id": "phase-3", "title": "Prove and operate results", "purpose": "Evaluate, debug, serve, and defend a production decision.", "skill_ids": ["evaluation", "production", "preference"], "generated": False},
        ],
        "assessment_types": ["MCQ", "short_answer", "explanation", "scenario", "debugging", "code_implementation", "decision", "counterfactual", "transfer"],
        "sources": [
            {"title": "LoRA: Low-Rank Adaptation of Large Language Models", "url": "https://arxiv.org/abs/2106.09685", "source_type": "paper", "author_publisher": "Hu et al.", "authority_level": 8, "freshness": 0.91, "relevance": 0.99, "confidence": 0.98, "classification": "FOUNDATIONAL"},
            {"title": "QLoRA: Efficient Finetuning of Quantized LLMs", "url": "https://arxiv.org/abs/2305.14314", "source_type": "paper", "author_publisher": "Dettmers et al.", "authority_level": 8, "freshness": 0.88, "relevance": 0.98, "confidence": 0.98, "classification": "CURRENT_PRACTICE"},
            {"title": "Hugging Face PEFT documentation", "url": "https://huggingface.co/docs/peft/", "source_type": "official_docs", "author_publisher": "Hugging Face", "authority_level": 7, "freshness": 0.97, "relevance": 0.96, "confidence": 0.95, "classification": "CURRENT_PRACTICE"},
        ],
        "project": {
            "title": "Constrained adaptation decision and implementation",
            "brief": "Given a dataset, a 16 GB GPU, and a product behavior target, decide whether fine-tuning is appropriate; implement a defensible approach; evaluate it; and document what evidence would change your decision.",
            "rubric": {"problem_framing": 0.15, "data_quality": 0.2, "implementation": 0.25, "evaluation": 0.25, "decision_quality": 0.15},
        },
    }
    return CourseManifest.model_validate(raw)


class CourseCompiler:
    def compile(self, objective: str, depth: int) -> CourseManifest:
        # Deterministic fixture proves the pipeline offline. A configured provider may replace
        # individual compiler stages, but all output still validates against CourseManifest.
        return demo_manifest(depth)
