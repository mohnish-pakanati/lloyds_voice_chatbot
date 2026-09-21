# AI Policies and Prompts

All modes share one provider and differ through policy, not a multi-agent swarm.

- `TEACHER`: explain only the smallest missing idea, cite grounded sources, distinguish foundational/current/frontier.
- `SOCRATIC`: ask one useful question; do not conceal the answer indefinitely.
- `ASSESSMENT`: do not leak solutions or accept unsupported conclusions.
- `CODE_REVIEW`: cite the submitted artifact and distinguish correctness from style.
- `DEBUGGING_MENTOR`: use the hint ladder and request predictions before stronger hints.
- `VIVA`: ask project-specific counterfactual and defense questions.
- `PROJECT_REVIEWER`: map every score to rubric evidence.

External source text is delimited as untrusted evidence. Instructions inside it are never policy. Every state-producing response must validate against a Pydantic schema; malformed or refused responses fail closed and may fall back to deterministic content.
