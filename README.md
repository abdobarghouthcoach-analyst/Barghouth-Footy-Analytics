# Barghouth Footy Analytics

Barghouth Footy Analytics is a football analysis workspace for turning match setup data and Veo highlight exports into reviewable, correctable match events.

The current release candidate is focused on the v0.2.0-alpha Match Management and Import workflow.

## Tech Stack

Backend:
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Pydantic v2

Frontend:
- React
- TypeScript
- Vite
- TailwindCSS
- TanStack Query v5

Infrastructure:
- Docker
- Docker Compose

## Docker Setup

Start the full local stack:

```bash
docker compose up --build
```

Services:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

The frontend uses `VITE_API_BASE_URL=http://localhost:8000/api/v1`.

## Development Commands

Backend tests:

```bash
docker build -t bfa-backend-check .
docker run --rm bfa-backend-check sh -c "uv pip install --system '.[dev]' && pytest"
```

Frontend build:

```bash
docker build -t bfa-frontend-check ./frontend
docker run --rm bfa-frontend-check npm run build
```

Database migration:

```bash
docker compose run --rm backend alembic upgrade head
```

The backend service also runs `alembic upgrade head` on startup in Docker Compose.

## Supported Veo Import Format

BFA currently supports Veo Highlights ZIP imports.

Supported metadata sources:
- JSON metadata files with event rows
- CSV metadata files with event rows
- Real-style Veo MP4 highlight filenames when no JSON/CSV metadata is present

Supported MP4 filename pattern:

```text
{index} {HHMMSS}_-_{label}.mp4
```

Example:

```text
01 000124_-_Shot_on_goal.mp4
04 000659_-_Goal.mp4
16 010353_-_Shot_on_goal.mp4
```

The MP4 parser reads filename metadata only. It does not inspect or process video contents.

## Current Analyst Workflow

Create Match

↓

Import Veo ZIP

↓

Review Events

↓

Correct Events

↓

Delete Import

↓

Re-import

## Known Limitations

- Veo MP4 support is filename-based only.
- No video playback yet.
- Unknown team remains unknown until analyst correction.
- Statistics are not yet implemented.
- Reports, xG, authentication, SaaS, clubs, users, and background jobs are not part of v0.2.0-alpha.

## API Prefix

The canonical API prefix is:

```text
/api/v1
```

The frontend and OpenAPI routes are expected to use this prefix for application APIs.
