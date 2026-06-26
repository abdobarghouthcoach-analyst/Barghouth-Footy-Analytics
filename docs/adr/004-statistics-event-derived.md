# ADR-004

## Title

Keep statistics event-derived; do not persist calculated statistics on domain models.

## Status

Accepted

## Context

Football analytics grows in value when data is traceable to actual match events. Metrics such as goals, shots, passes, and xG are derivable from the underlying event stream.

Persisting derived statistics on domain entities creates several problems:

- stale materialized data when source events change or are corrected
- duplication of business logic across models and services
- increased complexity when supporting multiple event types or new statistic definitions
- weaker auditability for analyst workflows

## Decision

We will treat domain entities like `Competition`, `Season`, and future `Match`/`Event` models as structural holders of metadata and relationships.

Derived statistics belong in analytic services and should be computed from event data on demand or via dedicated analytics projections, not stored directly on domain tables.

### Consequences

Pros:

- strong auditability and traceability to source events
- no synchronization burden for derived values
- simpler domain model and migrations
- easier support for analytical evolution over time

Cons:

- query performance may require dedicated analytic views or materialized projections later
- some precomputed reporting caches may still be needed for performance-sensitive dashboards
