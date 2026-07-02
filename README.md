# Barghouth Footy Analytics

Barghouth Footy Analytics is a football analysis workspace for turning match setup data and Veo highlight exports into reviewable, correctable match events with linked video evidence.

The current release candidate is **v0.3.0-alpha**, focused on Match Workspace review, video synchronisation, event correction, import management, and analyst workflow.

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

## API Prefix

The canonical API prefix is:

```text
/api/v1
```

The frontend and OpenAPI routes use this prefix for application APIs.

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

## M3 Architecture Notes

`MatchVideoClip` is provider-neutral match evidence. Clips are linked to matches and optionally to import jobs, and events can optionally reference a clip through nullable `events.video_clip_id`.

Video files are stored separately from import ZIPs under:

```text
/app/storage/video/{match_id}/imports/{import_job_id}/clips/
```

The streaming endpoint resolves stored paths against the configured video storage root before serving a file.

Event review workflow is explicit and separate from event correction:
- `is_reviewed`
- `reviewed_at`
- `reviewed_by`
- `confidence`: `high`, `medium`, `low`, or `unknown`

`edited_at` records correction edits only. It is not used as review state.

## M4.1 Football Rules Engine

The Football Rules Engine lives in `app/domain/football/rules/`.

Its purpose is to interpret canonical provider-neutral Events and produce explainable derived football facts. It does not calculate or store match statistics yet.

Rules must remain pure and deterministic:
- no FastAPI routes
- no SQLAlchemy ORM models or database sessions
- no provider adapters
- no frontend code

Every derived fact includes:
- contributing event IDs
- rule ID and rule name
- derivation path and reason

Statistics will be derived later from Events and rule facts. Events remain the source of truth; statistics are not stored as canonical football truth.

## M4.2 Match Statistics

The match statistics layer lives in `app/domain/football/statistics/`.

It derives match-level statistics from Football Rules Engine facts:
- goals
- shots
- shots on target
- corners
- fouls
- offsides
- yellow cards
- red cards

Statistics are reproducible calculations, not canonical stored data. Each statistic includes contributing event IDs, fact references, rule identity, and a derivation reason/path.

Shots on target and card color counts are conservative: they are counted only when the provider-neutral event type has already been normalised clearly enough to support the statistic.

## M4.3 Team Statistics

Team statistics are derived in the same statistics domain layer.

Team-level calculations group rule-derived facts by normalized event `team_id`. Events without reliable team attribution are excluded from team statistics rather than guessed.

Each team statistic includes the team ID, statistic name, value, contributing events, fact references, rule identity, and a derivation path/reason.

## M4.4 Player Statistics Foundation

Player statistics are derived from rule facts only when normalized `player_id` attribution exists.

The player statistics foundation supports goals, assists, shots, yellow cards, and red cards. Assists require explicit `assist_player_id` attribution on the provider-neutral event; they are not inferred from event sequence or timing.

Events without reliable player attribution are excluded from player statistics rather than guessed.

## Current Analyst Workflow

```text
Create Match
-> Import Veo ZIP
-> Review Events with linked video
-> Correct Events
-> Mark review state and confidence
-> Delete Import if needed
-> Re-import
```

## Known Limitations

- Veo MP4 support is filename-based only.
- Video playback is clip-based; no advanced video analysis is implemented.
- Unknown team remains unknown until analyst correction.
- Review ownership is a nullable string placeholder until authentication exists.
- Bulk review uses sequential event updates from the frontend.
- Statistics, reports, xG, authentication, SaaS, clubs, users, and background jobs are not part of v0.3.0-alpha.
