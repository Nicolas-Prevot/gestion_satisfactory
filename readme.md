# Gestion Satisfactory (FastAPI + React)

Gestion Satisfactory is now a clean 2-service architecture:

- `apps/backend`: FastAPI API (SQLite, optimizer, planner, scraper CLI)
- `apps/frontend`: React + TypeScript + Vite UI

The project is multiplayer-safe on SQLite with:

- WAL mode + busy timeout
- short explicit transactions
- optimistic locking on planner lines (`version` field)
- websocket live refresh (`/ws/scenarios/{scenario_id}`)

## Features

- Factory planner with scenario/area/factory/line structure
- One recipe per line (`building_count` + `efficiency_multiplier` + recipe)
- Live balances: outputs, inputs, intermediates, power
- Recipe optimizer with:
  - free-form float quantity inputs
  - raw item weights
  - raw item limits
  - available-items bootstrap per run
  - interactive graph output
- Full debug error payloads in UI (`trace_id`, message, stack)

## Prerequisites

- Docker + Docker Compose
- Node 22+ and npm (for local frontend dev)
- Python 3.11+ and `uv` (for local backend dev)

## Setup

1. Copy env file:

```bash
cp default.env .env
```

2. Optional: edit `.env` values.

## Run with Docker Compose

```bash
docker compose up -d --build
```

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

## Local Development

### Backend (uv)

```bash
uv sync --project apps/backend
uv run --project apps/backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir apps/backend
```

### Frontend (npm)

```bash
cd apps/frontend
npm install
npm run dev
```

Frontend requests default to same-origin (`/api`, `/ws`, `/static`) and the Vite dev server proxies to `http://localhost:8000`.
If needed, override the proxy target with `VITE_DEV_PROXY_TARGET` or force direct API calls with `VITE_API_BASE_URL`.

## Scraper (CLI only)

Run scraper from backend project:

```bash
uv run --project apps/backend python -m app.cli scrape --full-trace
```

List recent runs:

```bash
uv run --project apps/backend python -m app.cli scrape-runs --limit 20
```

Scrape failures are kept in `scrape_runs` with full traceback text.

Image policy:

- During scrape, remote wiki images are downloaded into `static/`.
- During normal app/API usage, only local images are served by default.
- If a local file is missing, `image_url` is `null` (no remote fetch).
- Static assets are stored in repo root `./static` (not `./apps/static`).

## API Overview

Base path: `/api/v1`

- `GET /health`
- `GET /meta/items`
- `GET /meta/buildings`
- `GET /meta/recipes`
- Scenarios/areas/factories/lines CRUD
- `GET /scenarios/{id}/balances`
- `POST /optimizer/solve`
- `GET /errors/{trace_id}`

Websocket:

- `GET ws /ws/scenarios/{scenario_id}`

## Testing

Backend:

```bash
uv run --project apps/backend pytest apps/backend/tests -q
```

Frontend:

```bash
cd apps/frontend
npm run build
```

## Notes

- Existing Streamlit planner data is intentionally not migrated.
- SQLite is the only supported database in this version.
- No authentication is configured in v1.
