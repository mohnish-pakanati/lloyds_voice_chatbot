# Architecture

The repository is a modular monolith:

- `apps/web`: Next.js App Router, React, TypeScript, Tailwind.
- `apps/api`: FastAPI, Pydantic, SQLAlchemy, Alembic.
- PostgreSQL in Docker; SQLite for frictionless local/test execution.
- `LLMProvider`, `ResearchProvider`, `EmbeddingProvider`, and `CodeRunner` isolate external systems.

Core services are deterministic and replaceable: `DepthEngine`, `CourseCompiler`, `MasteryService`, `LearningScienceService`, `SourceEvaluationService`, and `ProjectEvaluationService`. Generated state crosses a Pydantic validation boundary. The compiler creates the graph and all phase outlines up front, but only marks Phase 1 generated.

Requests use an explicit user identity boundary. V1's `X-User-ID` adapter is deliberately narrow and must be replaced by signed sessions before internet deployment.

OpenAI integration uses the Responses API with schema-backed parsing and `store=False`; the selected model is configuration, never business logic. The implementation follows current [official Responses API documentation](https://developers.openai.com/api/reference/cli/resources/responses/methods/create) and [Structured Outputs guidance](https://developers.openai.com/api/docs/guides/structured-outputs).
