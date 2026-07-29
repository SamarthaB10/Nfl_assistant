# Spec: Live NFL Headlines Backend

## Objective

Add a standalone live-news data service to the existing LeagueWatch FastAPI
application. The service aggregates current NFL articles from the official
ESPN, CBS Sports, and FOX Sports RSS feeds, refreshes them hourly, stores one
year of normalized metadata in the existing PostgreSQL database, and exposes a
cursor-paginated read API for the later Headlines tab. During the current
offseason, that means current offseason, transaction, injury, and training-camp
coverage—not the historical 2025 pregame headlines shown on ranking cards.

This feature is independent from matchup ratings. News must never change a
watchability score or enter the ranking request path.

### User stories

- As an NFL viewer, I can retrieve current NFL reporting from multiple trusted
  publishers without visiting each publisher separately.
- As a user, I can filter the feed by publisher or NFL team.
- As a user, I can follow a headline to the original publisher to read the full
  article.
- As an operator, I can retain a rolling year of article metadata without
  manually refreshing feeds.

### Confirmed assumptions

1. The implementation targets `/Users/samarthab/NFLviewer`, not the Sites
   worktree.
2. ESPN, CBS Sports, and FOX Sports are the complete MVP source set.
3. Only content supplied by each official feed is stored and returned. Article
   bodies are never copied.
4. Publisher headlines and excerpts are not rewritten.
5. PostgreSQL remains the single database. Headlines use a dedicated table,
   not a separate database.
6. Separate publishers may cover the same event and both articles remain.
   Repeated copies of the same publisher article are deduplicated.
7. The detailed Headlines UI is a separate specification.
8. The live feed is based on current publisher timestamps. The checked-in 2025
   matchup-headline data is not imported into `news_articles`.

## Tech Stack

- Python 3.12
- FastAPI `>=0.115,<1`
- Pydantic through `fastapi[standard]`
- PostgreSQL 16
- `psycopg` 3 for FastAPI database access
- `httpx` for bounded HTTP requests and redirects
- Python standard-library XML parsing for RSS
- Drizzle ORM/Kit `0.45.2`/`0.31.10` as the existing PostgreSQL migration
  authority
- pytest 8 and Ruff for backend verification

FastAPI owns feed ingestion and the public headlines API. Next.js continues to
own authentication but does not ingest news or query publishers directly.

## Data Model

Create `news_articles` in the existing `leaguewatch` PostgreSQL database:

| Column | Type | Rules |
| --- | --- | --- |
| `id` | `bigint` identity | Primary key and cursor tie-breaker |
| `source` | `text` | `ESPN`, `CBS`, or `FOX` |
| `source_article_id` | `text` | Publisher GUID, falling back to canonical URL |
| `title` | `text` | Required, exact feed value |
| `author` | `text` | Nullable |
| `excerpt` | `text` | Nullable, exact feed value |
| `canonical_url` | `text` | Required HTTPS publisher link |
| `image_url` | `text` | Nullable, feed-provided URL only |
| `team_codes` | `text[]` | Detected NFL team abbreviations |
| `published_at` | `timestamptz` | Required publisher timestamp |
| `fetched_at` | `timestamptz` | First successful ingestion |
| `updated_at` | `timestamptz` | Most recent metadata refresh |

Required indexes and constraints:

- primary key on `id`;
- unique `(source, source_article_id)`;
- unique `canonical_url`;
- cursor index `(published_at DESC, id DESC)`;
- source cursor index `(source, published_at DESC, id DESC)`;
- GIN index on `team_codes`.

Article retention is based on `published_at`. Every successful synchronization
deletes rows older than one year.

## Ingestion

- A FastAPI lifespan task checks feeds immediately after startup and then every
  hour while the process remains active.
- Before fetching, the task obtains a PostgreSQL advisory lock so multiple API
  instances do not run the same synchronization concurrently.
- A source is skipped at startup when its stored articles were fetched less
  than one hour ago.
- Each source request has a finite timeout, a descriptive User-Agent, redirect
  support, and independent error handling.
- One publisher failure must not prevent other publishers from refreshing.
- Inserts use an upsert keyed by `(source, source_article_id)`.
- Existing rows may refresh metadata and `updated_at`, but `fetched_at` remains
  the original ingestion time.
- Feed values are validated before persistence. Unsupported URL hosts,
  non-HTTP(S) links, empty titles, and invalid publication timestamps are
  rejected.
- Team tags are derived from the title and excerpt using the existing NFL team
  alias vocabulary. Tagging never modifies publisher content.
- The existing checked-in 2025 pregame-headline cache remains unchanged and
  continues serving matchup explanations.

## Public API

### `GET /api/v1/headlines`

Query parameters:

| Field | Default | Validation | Meaning |
| --- | --- | --- | --- |
| `limit` | `20` | Integer `1–50` | Maximum articles returned |
| `cursor` | none | Opaque validated string | Continue after the previous page |
| `source` | none | `ESPN`, `CBS`, or `FOX` | Optional publisher filter |
| `team` | none | Valid NFL abbreviation | Optional team filter |

Response:

```json
{
  "items": [
    {
      "id": 10482,
      "source": "ESPN",
      "title": "Example NFL headline",
      "author": "Example Author",
      "excerpt": "Feed-provided summary.",
      "url": "https://www.espn.com/nfl/story/_/id/example",
      "imageUrl": "https://example.com/image.jpg",
      "teamCodes": ["KC"],
      "publishedAt": "2026-07-29T19:02:00Z"
    }
  ],
  "nextCursor": "opaque-cursor-or-null",
  "hasMore": true
}
```

Cursor ordering is `(published_at DESC, id DESC)`. The cursor encodes both
values so identical publication timestamps cannot create omissions or
duplicates. Invalid cursors return `422`. The service queries `limit + 1` rows
to determine `hasMore`.

The endpoint is public and read-only. It returns stored data even when the most
recent publisher refresh failed.

## Commands

```bash
# Start local PostgreSQL
docker compose up -d --wait postgres

# Install/update Python dependencies
uv sync

# Generate and apply the PostgreSQL migration
cd frontend
npm run db:generate
npm run db:migrate
cd ..

# Start FastAPI
uv run fastapi dev

# Backend tests and quality checks
uv run pytest
uv run ruff check .
uv run ruff format --check .

# Frontend schema checks affected by the shared migration
cd frontend
npm run typecheck
npm test
npm run lint
```

## Project Structure

```text
src/nflviewer/
  app.py                 FastAPI lifecycle and headlines route
  models.py              Public request/response models
  news/
    feeds.py             Source definitions and RSS normalization
    repository.py        PostgreSQL reads, upserts, locking, retention
    service.py           Hourly synchronization orchestration

tests/
  test_news_feeds.py     RSS parsing and validation
  test_news_repository.py
  test_news_service.py   Source isolation, locking, retention
  test_headlines_api.py  Validation and cursor behavior

frontend/src/db/
  schema.ts              Shared news_articles schema

frontend/drizzle/
  *.sql                  Generated PostgreSQL migration
```

## Code Style

Use typed, dependency-injected boundaries so feed parsing and API pagination
can be tested without live publisher or PostgreSQL calls:

```python
class FeedClient(Protocol):
    async def fetch(self, source: NewsSource) -> list[FeedArticle]: ...


async def synchronize_source(
    source: NewsSource,
    *,
    client: FeedClient,
    repository: NewsRepository,
) -> SyncResult:
    articles = await client.fetch(source)
    return await repository.upsert(source, articles)
```

- Python modules and functions use `snake_case`; classes use `PascalCase`.
- Public functions and models are fully typed.
- Network and database dependencies enter through explicit interfaces.
- Publisher-specific parsing stays out of API route handlers.
- API JSON continues using the existing camelCase alias convention.

## Testing Strategy

- Unit tests use committed RSS fixtures; tests never depend on live publisher
  availability.
- Feed tests cover ESPN, CBS, and FOX parsing, missing optional fields,
  malformed items, URL-host validation, and team tagging.
- Repository tests cover deterministic cursor ordering, source/team filters,
  upsert deduplication, advisory-lock behavior, and one-year deletion.
- Service tests prove one failed source does not block the others and that the
  hourly loop can shut down cleanly.
- API tests cover the default 20-item limit, maximum limit, invalid filters,
  malformed cursors, empty pages, and `503` when PostgreSQL is unavailable.
- Existing ranking, authentication, and profile tests must continue passing.
- A manual verification fetch confirms that each displayed URL opens the
  original publisher.

## Boundaries

### Always

- Preserve publisher attribution and canonical links.
- Use only data supplied by official feeds.
- Bound network timeouts and validate all external data.
- Serve reads from PostgreSQL, never directly from a publisher request.
- Keep news unavailable/failure states isolated from matchup rankings.
- Preserve the current uncommitted `frontend/next-env.d.ts` change.

### Ask first

- Add another publisher.
- Change the one-hour refresh interval or one-year retention period.
- Add full-text search, personalized ordering, bookmarks, or notifications.
- Change the matchup formula based on news.
- Introduce Redis, a task queue, or a separate database.

### Never

- Scrape publisher article pages.
- Store or display full article bodies.
- Rewrite publisher headlines or excerpts.
- Treat a publisher failure as a reason to delete stored articles.
- Put credentials or secrets in source control.

## Success Criteria

1. FastAPI ingests valid NFL feed entries from ESPN, CBS, and FOX at most once
   per hour across concurrent instances.
2. Articles persist in `news_articles` with the confirmed metadata and required
   indexes.
3. Duplicate publisher items update one row rather than create another.
4. Separate publisher coverage of the same event remains separately visible.
5. Rows older than one year are removed during synchronization.
6. `GET /api/v1/headlines` returns newest-first, 20 items by default, with
   stable cursor pagination and optional source/team filters.
7. Publisher outages leave the stored feed readable and do not affect ranking
   endpoints.
8. All existing and new automated checks pass.

## Open Questions

- The Headlines page layout, visual hierarchy, responsive behavior, loading
  states, and filter controls will be defined in a separate UI specification
  after this backend/data contract is implemented.
