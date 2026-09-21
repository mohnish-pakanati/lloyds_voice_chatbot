# Arc — Adaptive Learning Platform V1

Arc is an executable V1 proof that separates an AI teacher from the learning system around it. Skills, dependencies, evidence, misconceptions, hint usage, mastery dimensions, and review schedules are explicit application state. The deterministic LLM and research providers make the demo and test suite work without paid calls; a configured OpenAI provider uses validated structured outputs.

## Run with Docker

```powershell
cd adaptive-learning-platform
Copy-Item .env.example .env
docker compose up --build
```

Open `http://localhost:3000`. The API is at `http://localhost:8000/docs`.

## Run locally

```powershell
cd adaptive-learning-platform
python -m venv apps/api/.venv
apps/api/.venv/Scripts/python -m pip install -r apps/api/requirements.txt
npm install
Start-Process -WindowStyle Hidden -FilePath apps/api/.venv/Scripts/python -ArgumentList '-m','uvicorn','app.main:app','--reload','--port','8000' -WorkingDirectory apps/api
npm run dev:web
```

SQLite is the local fallback. Docker Compose uses PostgreSQL. Set `LLM_PROVIDER=openai` only when live generation is desired; `fake` is the safe default.

## Test

```powershell
npm run typecheck
npm run build
apps/api/.venv/Scripts/python -m pytest apps/api/tests -q
```

See [V1 status](docs/V1_STATUS.md), [architecture](docs/ARCHITECTURE.md), and [security](docs/SECURITY.md).
