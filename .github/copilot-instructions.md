# Barghouth Footy Analytics - Copilot Instructions

## Project Overview

Barghouth Footy Analytics is a football performance analysis platform built by a performance analyst for football analysts.

The primary goal is NOT to build another statistics dashboard.

The goal is to reduce the time between the final whistle and a coach-ready report while improving the quality and consistency of football analysis.

Every feature should help analysts become:

- Faster
- Smarter
- More consistent

If a feature does not achieve at least one of these goals, question whether it belongs.

---

## Product Principles

Always optimise for:

1. Simplicity
2. Maintainability
3. Scalability
4. User experience
5. Clean architecture

Avoid unnecessary abstraction.

Avoid overengineering.

Write readable code.

---

## Architecture

Frontend

- React
- TypeScript
- Vite
- TailwindCSS
- React Router
- TanStack Query
- shadcn/ui

Backend

- FastAPI
- SQLAlchemy 2
- Alembic
- Pydantic v2

Database

- PostgreSQL

Infrastructure

- Docker Compose

---

## Coding Standards

Follow Clean Architecture.

Business logic belongs inside Services.

Database access belongs inside Repositories.

API routes should remain thin.

Never place business logic inside controllers.

Prefer dependency injection.

Prefer composition over inheritance.

Write type-safe code.

Use meaningful names.

Keep functions small.

---

## User Experience

The application should feel like:

- Linear
- GitHub
- Notion

Minimal.

Professional.

Dark mode first.

No unnecessary animations.

Fast.

---

## Football Philosophy

Football drives the software.

Do not create statistics for the sake of statistics.

Every metric should answer a football question.

Every statistic should eventually be linked to video.

Everything revolves around Events.

Events belong to Matches.

Reports are collections of Events.

---

## Future Modules

The application will eventually contain:

- Match Centre
- Event Engine
- Shot Engine
- xG Engine
- Tactical Dashboard
- Player Reports
- Opposition Reports
- AI-assisted Video Analysis
- PowerPoint Report Generator

Design code so these modules can be added without major refactoring.

---

## Development Philosophy

Prefer building small complete features rather than large incomplete systems.

Keep commits focused.

Every pull request should move the product forward.

Always consider future maintainability.

Write production-quality code.