# ADR 007 — Import Job entity

Status: Accepted

Context

We need an import workflow domain that is provider-independent and supports asynchronous ingestion of large files and video metadata for future workflows.

Decision

Create a new `ImportJob` entity with the following fields:

- `id` (UUID)
- `match_id` (FK to `matches`)
- `provider` (string enum: `veo`, `csv`, `other`)
- `status` (string enum: `pending`, `running`, `completed`, `failed`)
- `filename` (string)
- `started_at`, `finished_at` (timestamps)
- `imported_events_count`, `warnings_count` (integers)
- `error_message` (nullable text)
- standard audit timestamps `created_at`, `updated_at`

Rationale

- Separates import orchestration from event and match entities.
- Enables asynchronous job tracking for large imports and provider-specific plugins.
- Keeps the domain ready for future import processors without locking in file parsing details.

Consequences

- Import workflows can be added as services or background workers later.
- Events remain generic and can be populated from import jobs once parsing is implemented.
- Providers can be extended without changing the core job schema.

Date: 2026-06-27
