# V1 Status

## IMPLEMENTED

- Learning mission creation, automatic/override depth, editable mission review.
- Validated course manifest, skill graph, prerequisites, phases, source metadata, classification, and manual refresh seam.
- Deterministic fine-tuning demo with diagnostic, focused lesson, scenario, confidence capture, hint ladder, misconception, remediation, novel-retest path, queue, project rubric, viva questions, and skill report.
- Explicit evidence and multidimensional mastery updater, review scheduling, adaptive activity selection, source ranking/freshness, project score aggregation.
- Provider interfaces with deterministic fakes and current OpenAI structured-output adapter.
- Strict Docker code-runner command, hidden-test input, timeout result, stdout/stderr.
- Responsive light/dark UI, reduced-motion behavior, keyboard focus, and uncluttered one-task lesson layout.
- PostgreSQL/SQLite persistence, Compose, seed data, tests, logging events, and core documentation.

## PARTIAL

- Course compiler: the full stage boundary and manifest exist; the deterministic demo implements the researched fine-tuning vertical slice. Arbitrary topics currently reuse this fixture instead of invoking all live research/LLM stages.
- Authentication: ownership enforcement exists, but the V1 header adapter is for local evaluation only.
- Assessments: schemas and demo exercise types are present; the UI does not yet expose every listed assessment type as a separate renderer.
- Project/viva: scoring and dynamic-question endpoints exist; artifact upload, persistent evaluation orchestration, and full viva response scoring need completion.
- Observability: structured event points exist; JSON log configuration, tracing, dashboards, and provider cost persistence are not complete.
- Alembic: a generated baseline migration covers all V1 domain tables; PostgreSQL-specific review is still required before production deployment.

## DEFERRED

- Scheduled freshness checks, production research fetcher, embeddings/semantic retrieval, production sandbox service, hidden-test authoring UI, OAuth/session authentication, full accessibility audit, mobile-specific polish, and background jobs.
- Voice, avatar, social, classrooms, marketplace, payments, certificates, native mobile, multi-agent orchestration, RL curriculum optimization, and neural knowledge tracing are intentionally outside V1.

## BLOCKED

- None for the local deterministic proof. Live provider quality and external research depend on API access, approved model configuration, outbound network policy, and provider budget.

## Recommended next step

Complete the persistent compiler pipeline for arbitrary goals, replace header auth, move code execution behind a dedicated sandbox boundary, and run a calibrated learner study before interpreting mastery estimates as predictive.
