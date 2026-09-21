# Local Development

Requirements: Node 22, npm 10, Python 3.13, and Docker Desktop for PostgreSQL and learner code execution.

`docker compose up --build` is the full-stack path. Local API work may use SQLite by omitting `DATABASE_URL`. The seeded provider is deterministic and requires no network. Copy `.env.example` to `.env` only for Compose; never commit a populated secret file.

The web rewrites `/backend/*` to the API, avoiding browser-side service discovery. API docs are available at `/docs`. The demo user id is `demo-user` and is sent only by the local V1 interface.
