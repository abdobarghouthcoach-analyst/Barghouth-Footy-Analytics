# ADR-005

## Title

Add `Team` as a first-class domain entity belonging to a `Club`.

## Status

Accepted

## Context

Teams are the unit of competition in football analytics. Each team belongs to a club, plays matches, and carries identity metadata such as name, stadium, colours, and badge.

The existing domain already describes competitions and seasons. Adding `Team` enables team-level reporting, match context, and future squad/player modeling.

## Decision

Introduce `Team` as an entity with the following properties:

- `name`
- `short_name`
- `city`
- `country`
- `stadium`
- `colours`
- `badge_url`
- `club_id`

The `Team` model is owned by the domain layer with repository/service abstractions and thin API routes.

## Consequences

Pros:

- team metadata is captured explicitly
- matches can reference teams without mixing competition metadata
- the domain remains flexible for club/team season hierarchies

Cons:

- requires club entity support later for full referential integrity
- introduces another layer of CRUD surface area
