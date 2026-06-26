# ADR-003

## Title

Model `Competition` as the top-level football entity above `Season`.

## Status

Accepted

## Context

Football competitions such as domestic leagues, cups, and international tournaments are primary structural elements in the sport. Seasons belong to competitions, but competitions are broader and more stable across years.

Existing domain models are expected to support:

- multiple seasons per competition
- tournament-level reporting and analytics
- competition-level metadata such as country, level, and type

## Decision

We model `Competition` as a top-level domain entity, with `Season` as a subordinate concept. This means:

- `Competition` contains stable metadata for the competition itself
- `Season` can be related to `Competition` through a foreign key in future models
- domain logic and repositories should treat `Competition` as the primary holder of competition identity

## Consequences

Pros:

- clearer football hierarchy
- better support for cross-season analytics
- simpler competition lookup and sharing of metadata

Cons:

- requires explicit season linking in future data models
- introduces an additional layer in the domain model
