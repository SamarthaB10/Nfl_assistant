# Implementation Plan: Accounts and Public Profiles

## Overview

Implement the approved email/password account and public-profile specification
inside the existing Next.js frontend. Keep FastAPI and the public rankings
contract unchanged.

## Architecture Decisions

- Next.js owns browser authentication, sessions, profile reads, and profile
  writes.
- Better Auth owns credentials and session lifecycle.
- Drizzle owns the PostgreSQL schema and forward migrations.
- Profile access uses narrow server-only functions and public DTOs.
- Real image uploads remain out of scope; static defaults are used.

## Task List

### Phase 1: PostgreSQL and identity foundation

- [x] Add reviewed Better Auth, Drizzle, PostgreSQL, and validation dependencies.
- [x] Add environment contract, local PostgreSQL service, typed schema, and
  committed migration.
- [x] Add validation and public-profile mapping tests before implementation.

### Checkpoint: Foundation

- [x] Focused validation/schema tests pass.
- [x] Typecheck, lint, and existing frontend tests pass.
- [x] Commit the database and identity foundation.

### Phase 2: Authentication flow

- [x] Configure Better Auth and mount the Next.js auth handler.
- [x] Add tested signup, login, sign-out, and session-aware header behavior.
- [x] Verify cookies, generic credential errors, and authentication rate limits.

### Checkpoint: Authentication

- [x] Auth-focused tests pass.
- [x] Typecheck, lint, build, and existing ranking tests pass.
- [x] Commit the working authentication slice.

### Phase 3: Public profile and owner editing

- [x] Add public profile data access with a strict field allowlist.
- [x] Add `/u/[username]` and `/settings/profile`.
- [x] Add ownership checks and tested display-name/About updates.
- [x] Build the mobile-first dark/light profile UI.

### Checkpoint: Profile

- [x] Profile unit, component, and authorization tests pass.
- [ ] Browser verification passes at mobile and desktop widths.
- [x] Commit the public-profile slice.

### Phase 4: Final verification and documentation

- [ ] Run frontend test, lint, typecheck, build, and dependency audit.
- [ ] Run Python regressions to prove FastAPI remains unchanged.
- [ ] Document local PostgreSQL and account setup.
- [ ] Review the final diff for security, scope, and migration risks.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Private fields leak into profiles | High | Explicit public DTO and negative tests |
| Profile edits bypass ownership | High | Derive user ID only from a verified session |
| Username collision under concurrency | High | Normalize input and use a database unique constraint |
| Auth attempts are brute-forced | High | Database-backed Better Auth rate limiting |
| Auth work breaks public rankings | Medium | Keep service boundary unchanged and run regression tests per slice |
| Mobile profile drifts from reference | Medium | Build mobile-first and verify in a real browser |

## Open Questions

None. PostgreSQL production hosting and image storage remain later deployment
decisions.

---

# Implementation Plan: Game Comments

## Overview

Add public, game-scoped discussions to expanded rankings without changing the
FastAPI ranking contract.

### Phase 1: Database foundation

- [x] Add schema tests for game ownership, reply relationships, soft deletion,
  and cursor indexes.
- [x] Add the `game_comments` Drizzle table and PostgreSQL migration.
- [x] Verify schema tests, typecheck, lint, and migration consistency.

### Phase 2: Comment API

- [x] Add public cursor-paginated reads.
- [x] Add authenticated create, one-level reply, and author-only soft delete.
- [x] Add validation, authorization, and pagination tests.

### Phase 3: Game discussion UI

- [x] Add the green comment control beneath players to watch.
- [x] Add public comments, authenticated composer, replies, deletion, and
  incremental pagination.
- [x] Verify the anonymous live flow in a browser and authenticated component
  behavior with session-aware tests.
