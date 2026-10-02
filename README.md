# Warehouse Layout Advisor

> [!WARNING]
> 本项目是一份未完工的废案，不具备任何实际价值，仅供参考。请勿将其用于生产环境、商业决策或任何真实业务场景。

Warehouse Layout Advisor is a full-stack decision-support WebUI for warehouse
layout analysis. A conversational agent clarifies business goals, translates
them into structured analysis conditions, runs an evaluation workflow, and
presents traceable evidence, recommendations, and version history.

The frontend handles interaction and visualization. The FastAPI backend owns
the workflow state, business rules, versioning, persistence, and model gateway.
The evaluation model is an interchangeable backend service and defaults to a
deterministic mock gateway.

## Features

- Multi-turn clarification for scope, priorities, budget, performance floor,
  risk preference, and analysis period.
- Scenario versioning with optimistic concurrency checks.
- Background evaluation workflow with Server-Sent Events progress updates.
- Evidence, KPI, insight, recommendation, approval, and revision views.
- OpenAI-compatible chat-completions gateway with an offline mock fallback.
- SQLite persistence with automatic schema creation and demo seed data.

## Architecture

```text
frontend/
  src/api/             HTTP and SSE clients
  src/components/      Shared interaction and analysis components
  src/features/        Scenario version comparison
  src/pages/           Project dashboard and scenario workbench
  src/stores/          Cross-component UI state
  tests/               Vitest and Testing Library tests

backend/
  app/api/             FastAPI routes
  app/domain/          Clarification, translation, explanation, recommendation
  app/orchestration/   Evaluation jobs, workflow runner, event publishing
  app/adapters/        Mock and OpenAI-compatible model gateways
  app/models/          Pydantic schemas, ORM entities, enums
  app/persistence/     SQLite engine, repositories, migrations
  tests/               Pytest integration and workflow tests
```

## Requirements

- Python 3.11 or newer
- Node.js 18 or newer
- npm 9 or newer

## Backend

Install dependencies:

```powershell
cd backend
python -m pip install -r requirements.txt
```

Start the API:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

From the repository root, the equivalent command is:

```powershell
$env:PYTHONPATH='backend'
python -m uvicorn app.main:app --port 8000
```

The API is available at `http://127.0.0.1:8000`, and its health endpoint is
`GET /api/health`.

## Frontend

Install dependencies and start the development server:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to
`http://127.0.0.1:8000`.

To use a different API origin, set `VITE_API_BASE_URL` before starting Vite.

## Model Configuration

The backend uses the built-in mock gateway when `OPENCODE_API_KEY` is empty.
That mode is deterministic and requires no network access.

To use an OpenAI-compatible Chat Completions endpoint, set:

```powershell
$env:OPENCODE_API_KEY='your-api-key'
$env:OPENCODE_API_URL='https://opencode.ai/zen/go/v1/chat/completions'
$env:OPENCODE_MODEL='deepseek-v4-flash'
$env:OPENCODE_FORCE_IPV4='1'
```

Values are read from environment variables only. Never commit a real key.
See `backend/.env.example` for the supported names.

## Tests

Backend:

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/tests -q
```

Frontend:

```powershell
cd frontend
npm test
npm run build
```

## API Overview

```text
GET    /api/health

GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}

GET    /api/projects/{project_id}/scenarios
POST   /api/projects/{project_id}/scenarios
GET    /api/scenarios/{scenario_id}
PATCH  /api/scenarios/{scenario_id}
GET    /api/scenarios/{scenario_id}/versions
GET    /api/scenarios/{scenario_id}/events

GET    /api/scenarios/{scenario_id}/messages
POST   /api/scenarios/{scenario_id}/messages
GET    /api/scenarios/{scenario_id}/clarifications
POST   /api/scenarios/{scenario_id}/clarifications/{question_id}/answer
POST   /api/scenarios/{scenario_id}/confirm

POST   /api/scenarios/{scenario_id}/evaluations
GET    /api/evaluations/{evaluation_id}
GET    /api/evaluations/{evaluation_id}/events
GET    /api/evaluations/{evaluation_id}/stream
GET    /api/evaluations/{evaluation_id}/evidence
GET    /api/evaluations/{evaluation_id}/insights
GET    /api/evaluations/{evaluation_id}/recommendation

POST   /api/scenarios/{scenario_id}/approve
POST   /api/scenarios/{scenario_id}/revise
```

Errors use a consistent response shape:

```json
{
  "error": {
    "code": "SCENARIO_VERSION_CONFLICT",
    "message": "当前场景已产生新版本",
    "details": {
      "server_version": 5,
      "client_version": 4
    }
  }
}
```

## Data Storage

SQLite is used for local persistence. The default database is created at
`backend/data/warehouse_decision.db` on first startup. It stores projects,
scenarios, messages, clarifications, evaluation runs, evidence,
recommendations, versions, and audit events.

The database is runtime state and is ignored by Git. Set `WAREHOUSE_DB_PATH`
to use a different location.

## License

MIT
