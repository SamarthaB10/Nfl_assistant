# Implementation Plan: Live NFL Headlines Backend

## Overview

Implement the approved backend/data contract in
`docs/specs/headlines-backend.md`. The work adds an independently failing live
news path to FastAPI while preserving the existing in-memory ranking path. A
Drizzle migration creates the shared PostgreSQL table; Python adapters ingest
official RSS feeds hourly; a repository provides stable cursor pagination; and
FastAPI exposes the public read endpoint. Detailed Next.js UI work remains
deferred to its own specification. The feed contains current publisher stories
(including current offseason and training-camp coverage), never the checked-in
2025 matchup-headline cache.

## Dependency Graph

```text
Official feed contracts
        |
        v
PostgreSQL schema + runtime dependencies
        |
        +------------------+
        |                  |
        v                  v
RSS normalization     News repository
        |                  |
        +--------+---------+
                 |
                 v
       Hourly synchronization
                 |
                 v
       API models + endpoint
                 |
                 v
     Documentation + regression
```

## Architecture Decisions

- Continue using the existing PostgreSQL database and Drizzle migration
  history. Do not introduce a second migration system.
- Add `psycopg` as FastAPI's PostgreSQL driver. Move `httpx` into runtime
  dependencies because ingestion requires bounded asynchronous HTTP.
- Parse publisher RSS with the standard library. Do not add a parser dependency
  unless a verified official feed cannot be normalized correctly.
- Keep feed adapters publisher-specific at their boundary and normalize into
  one internal article model.
- Start an hourly synchronization task through FastAPI lifespan only when
  `DATABASE_URL` is configured. Rankings remain available when news storage is
  not configured or temporarily unavailable.
- Use a PostgreSQL advisory lock around each synchronization cycle so multiple
  FastAPI instances do not duplicate upstream requests.
- Use `(published_at, id)` keyset pagination with an opaque base64url cursor.
  Offset pagination is excluded because concurrent inserts would shift pages.
- Keep live articles separate from the checked-in historical pregame-headline
  cache.

## Implementation Order

### Phase 1: Storage and source normalization

- [x] Task 1: Add the news schema and backend runtime dependencies.
- [x] Task 2: Normalize official ESPN, CBS, and FOX RSS entries.
- [x] Task 3: Implement PostgreSQL persistence and cursor reads.

### Checkpoint: Data foundation

- [x] Drizzle schema validation and migration generation succeed.
- [x] Feed fixtures parse without network access.
- [x] Deduplication, retention, filters, and deterministic cursor behavior are
      covered by focused tests.
- [x] Existing ranking tests remain green.

### Phase 2: Scheduling and API

- [x] Task 4: Add isolated hourly synchronization.
- [x] Task 5: Expose the public headlines endpoint.

### Checkpoint: Backend feature

- [x] A publisher failure does not block other sources.
- [x] Multiple scheduler instances are serialized by the advisory lock.
- [x] The API returns stored data without contacting publishers.
- [x] Pagination produces no duplicates or omissions across equal timestamps.

### Phase 3: Operational handoff

- [x] Task 6: Document configuration, migration, synchronization, and API use.

### Checkpoint: Complete

- [x] `uv run pytest` passes.
- [x] `uv run ruff check .` passes.
- [x] `uv run ruff format --check .` passes.
- [x] `cd frontend && npm run typecheck` passes.
- [x] `cd frontend && npm test` passes.
- [x] `cd frontend && npm run lint` passes.
- [x] The running rankings experience has no regression.
- [x] The implementation is ready for the separate Headlines UI specification.

## Verification Strategy

1. Test source parsing with committed minimal RSS fixtures rather than live
   network calls.
2. Test repository behavior against PostgreSQL when the local service is
   available; keep query construction and cursor encoding unit-testable.
3. Inject fake feed clients and repositories into scheduler tests.
4. Inject a fake news repository into FastAPI tests so API behavior remains
   deterministic.
5. Perform one explicit live synchronization only after automated parsing and
   persistence tests pass.
6. Re-run the complete backend and frontend suites after integration.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Publisher changes RSS shape | Medium | Isolate adapters, validate entries, and keep source fixtures |
| One feed is unavailable | Low | Refresh sources independently and continue serving stored rows |
| Multiple API replicas fetch simultaneously | Medium | PostgreSQL advisory lock around the cycle |
| Equal publication timestamps break pagination | High | Composite `(published_at, id)` cursor and ordering |
| RSS contains unsafe or irrelevant URLs | High | Allowlist HTTPS publisher hosts and reject invalid entries |
| PostgreSQL is unavailable | Medium | Disable news scheduler/API cleanly while leaving rankings healthy |
| Feed content violates publisher terms | High | Store/display only feed-supplied fields with attribution and canonical links |
| Local Docker Compose is unavailable | Medium | Keep database setup explicit; verify with any available local/managed PostgreSQL |

## Sequential vs. Parallel Work

The schema, repository contract, scheduler wiring, and API route share the same
data model and must be implemented sequentially. Feed fixtures can be prepared
independently after the normalized model is fixed, but no multi-agent work is
needed for this scope.

## Open Questions

- None for the backend/data slice. UI presentation decisions are intentionally
  deferred.
