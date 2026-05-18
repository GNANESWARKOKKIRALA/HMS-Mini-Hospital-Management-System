# Claude Session — HMS Build

**Tool:** Claude (Anthropic) — claude-sonnet-4-6  
**Date:** 2026-05-18  
**Purpose:** HMS shortlisting task — architecture, code generation, README

---

## Prompt 1

> "Create project with the above pdf Requirements and give step by step how to run in vs code and setup of the project."

**Claude response summary:**
- Designed the full project structure: Django apps (accounts, doctors, patients, appointments), serverless email-service, templates, README
- Chose `AbstractUser` with a `role` field rather than separate User models per role — simpler foreign key graph, one auth system
- Chose `SELECT FOR UPDATE` + `transaction.atomic()` for race condition handling rather than optimistic locking with retries — PostgreSQL's row lock is the right primitive; retries add complexity with no benefit when a hard-block gives a clean result
- Chose to store Google OAuth2 tokens on the User model directly (plaintext, noted as a production limitation) vs. a separate encrypted token model — acceptable for a local demo scope
- Built non-blocking email and calendar calls: failures logged, never crash the booking flow
- Used `OneToOneField(AvailabilitySlot)` on Appointment as DB-level uniqueness guard on top of the application lock

## Decisions made with AI assistance

1. Architecture: Django monolith + separate serverless function (not microservices) — fits the spec exactly
2. Race condition: `select_for_update()` inside `transaction.atomic()` — correct answer for PostgreSQL
3. Role access: decorator pattern (`@doctor_required`, `@patient_required`) — clean, reusable, Django-idiomatic
4. Email failure mode: swallow + log, never raise — email is a side effect, not part of booking atomicity
5. Calendar token storage: on User model, noted limitation in README

---

*Raw session — not cleaned up per submission requirements.*
