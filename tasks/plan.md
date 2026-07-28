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

- [ ] Configure Better Auth and mount the Next.js auth handler.
- [ ] Add tested signup, login, sign-out, and session-aware header behavior.
- [ ] Verify cookies, generic credential errors, and authentication rate limits.

### Checkpoint: Authentication

- [ ] Auth-focused tests pass.
- [ ] Typecheck, lint, build, and existing ranking tests pass.
- [ ] Commit the working authentication slice.

### Phase 3: Public profile and owner editing

- [ ] Add public profile data access with a strict field allowlist.
- [ ] Add `/u/[username]` and `/settings/profile`.
- [ ] Add ownership checks and tested display-name/About updates.
- [ ] Build and verify the mobile-first dark/light profile UI.

### Checkpoint: Profile

- [ ] Profile unit, component, and authorization tests pass.
- [ ] Browser verification passes at mobile and desktop widths.
- [ ] Commit the public-profile slice.

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
