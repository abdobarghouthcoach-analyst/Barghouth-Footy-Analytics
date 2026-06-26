# ADR 006 — Event entity

Status: Accepted

Context

We need a provider-independent event store to capture any football action imported from external providers (Veo, manual entry, etc.). Events should be generic and extensible, not tied to specialized subtypes (Shot, Pass) at this stage.

Decision

Create a single `Event` entity with the following fields:

- `id` (UUID)
- `match_id` (FK to `matches`)
- `team_id` (FK to team)
- `player_id` (nullable)
- `event_type` (string) — provider-agnostic action label
- `minute`, `second`, `period` — temporal placement in the match
- `x_coordinate`, `y_coordinate` — optional normalized coordinates (0.0–1.0)
- `notes`, `tags` — freeform notes and structured tags stored as JSONB
- `source_provider`, `source_event_id` — provenance details
- `raw_payload` — store the original provider payload as JSONB

Rationale

- A single generic entity simplifies ingestion pipelines and avoids premature modelling.
- `raw_payload` preserves source fidelity for future reprocessing.
- `tags` and `event_type` enable downstream classification into more specific events without losing provenance.

Consequences

- Later we can introduce specialized sub-entities or derived tables (e.g., Shots, Passes) using the stored `raw_payload` and `event_type`.
- Event ingestion services should map provider fields into this schema and store `raw_payload` intact.

Date: 2026-06-26
