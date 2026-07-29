# Tasks: Live NFL Headlines Backend

## Task 1: Add the news schema and backend dependencies

**Description:** Create the `news_articles` Drizzle schema and migration, then
add only the Python runtime dependencies required for PostgreSQL and bounded
HTTP access.

**Acceptance criteria:**

- [x] The migration creates every approved column, constraint, and index.
- [x] `psycopg` and runtime `httpx` resolve through `uv sync`.
- [x] Existing account tables and migrations remain unchanged.

**Verification:**

- [ ] `cd frontend && npm run db:check`
- [ ] `cd frontend && npm run db:generate`
- [ ] `uv sync`
- [ ] `uv run pytest tests/test_models.py tests/test_health.py`

**Dependencies:** None

**Files likely touched:**

- `frontend/src/db/schema.ts`
- `frontend/drizzle/*.sql`
- `frontend/drizzle/meta/*`
- `pyproject.toml`
- `uv.lock`

**Estimated scope:** Medium

## Task 2: Normalize official RSS feeds

**Description:** Add source definitions, safe feed fetching, RSS parsing, URL
allowlists, metadata normalization, and team tagging for ESPN, CBS, and FOX.

**Acceptance criteria:**

- [x] Valid fixtures from all three sources normalize to the shared article model.
- [x] Missing optional metadata does not discard an otherwise valid article.
- [x] Invalid titles, timestamps, schemes, and publisher hosts are rejected.

**Verification:**

- [ ] `uv run pytest tests/test_news_feeds.py`
- [ ] `uv run ruff check src/nflviewer/news tests/test_news_feeds.py`
- [ ] `uv run ruff format --check src/nflviewer/news tests/test_news_feeds.py`

**Dependencies:** Task 1

**Files likely touched:**

- `src/nflviewer/news/__init__.py`
- `src/nflviewer/news/feeds.py`
- `tests/fixtures/news/*.xml`
- `tests/test_news_feeds.py`

**Estimated scope:** Medium

## Task 3: Implement persistence and cursor reads

**Description:** Add the psycopg repository for advisory locking, freshness
checks, article upserts, one-year cleanup, filters, and keyset pagination.

**Acceptance criteria:**

- [x] Re-ingesting one publisher item updates one row while preserving `fetched_at`.
- [x] Rows older than one year are deleted without affecting newer rows.
- [x] Source/team filters and `(published_at, id)` cursors return deterministic pages.

**Verification:**

- [ ] `uv run pytest tests/test_news_repository.py`
- [ ] Apply the migration to a test PostgreSQL database when available.
- [ ] Inspect the resulting indexes with `psql`.

**Dependencies:** Tasks 1 and 2

**Files likely touched:**

- `src/nflviewer/news/repository.py`
- `src/nflviewer/news/cursor.py`
- `tests/test_news_repository.py`

**Estimated scope:** Medium

## Checkpoint: Data foundation

- [x] Tasks 1–3 acceptance criteria pass.
- [x] `uv run pytest tests/test_ranking.py tests/test_api.py`
- [x] No live publisher requests occur during tests.

## Task 4: Add isolated hourly synchronization

**Description:** Orchestrate immediate-when-stale and hourly refreshes through a
cancellable FastAPI lifespan task with per-source failure isolation and a
PostgreSQL advisory lock.

**Acceptance criteria:**

- [x] Fresh data prevents an unnecessary startup fetch.
- [x] One source failure does not block successful sources or retention cleanup.
- [x] Scheduler shutdown cancels cleanly and rankings remain available on news failure.

**Verification:**

- [ ] `uv run pytest tests/test_news_service.py tests/test_health.py`
- [ ] Start and stop FastAPI twice without leaked-task warnings.

**Dependencies:** Task 3

**Files likely touched:**

- `src/nflviewer/news/service.py`
- `src/nflviewer/app.py`
- `tests/test_news_service.py`
- `tests/test_health.py`

**Estimated scope:** Medium

## Task 5: Expose cursor-paginated headlines

**Description:** Add API models, strict query validation, repository injection,
and `GET /api/v1/headlines`.

**Acceptance criteria:**

- [x] The default response contains at most 20 newest-first items.
- [x] Valid source/team filters and next cursors return stable subsequent pages.
- [x] Invalid queries return `422`; unavailable storage returns `503`.

**Verification:**

- [ ] `uv run pytest tests/test_headlines_api.py tests/test_api.py`
- [ ] Inspect the generated contract at `http://127.0.0.1:8000/docs`.

**Dependencies:** Tasks 3 and 4

**Files likely touched:**

- `src/nflviewer/models.py`
- `src/nflviewer/app.py`
- `tests/test_headlines_api.py`

**Estimated scope:** Medium

## Checkpoint: Backend feature

- [x] Tasks 4–5 acceptance criteria pass.
- [x] A manual two-page query has no repeated article IDs.
- [x] Existing `/api/v1/rankings` behavior is unchanged.

## Task 6: Document and verify operational use

**Description:** Update repository documentation with the migration, environment,
hourly refresh, API contract, retention behavior, source attribution, and
failure semantics.

**Acceptance criteria:**

- [x] A new developer can configure PostgreSQL and start the scheduler.
- [x] README API examples match the implemented response exactly.
- [x] Deferred UI scope and publisher-content boundaries remain explicit.

**Verification:**

- [ ] Run every command in the final project verification checklist.
- [ ] Review the README links and curl examples.

**Dependencies:** Tasks 1–5

**Files likely touched:**

- `README.md`
- `docs/specs/headlines-backend.md`
- `tasks/todo.md`

**Estimated scope:** Small

## Final verification

- [x] `uv run pytest`
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `cd frontend && npm run typecheck`
- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] Manual live-feed synchronization against ESPN, CBS, and FOX
- [x] Manual cursor pagination and source/team filter checks
