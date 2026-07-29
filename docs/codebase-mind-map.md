# LeagueWatch Codebase Mind Map

This map shows the current runtime boundaries and the files responsible for
each path. LeagueWatch has one browser application, one Python API, one shared
PostgreSQL database, and two intentionally separate NFL data pipelines.

```mermaid
mindmap
  root((LeagueWatch))
    Next.js frontend
      Shared shell
        layout.tsx
        site-navigation.tsx
        site-footer.tsx
        theme-toggle.tsx
        globals.css
      Matchup rankings
        page.tsx
        rankings-workspace.tsx
        ranking-controls.tsx
        game-list.tsx
        game-card.tsx
        lib/rankings.ts
        api/rankings/route.ts
      Current headlines
        headlines/page.tsx
        headlines-workspace.tsx
        headline-filters.tsx
        headline-card.tsx
        lib/headlines.ts
        api/headlines/route.ts
      Accounts and profiles
        login and signup pages
        auth forms
        Better Auth
        public profile page
        profile settings
        api/profile/route.ts
      Database layer
        db/schema.ts
        db/index.ts
        Drizzle migrations
    FastAPI backend
      HTTP boundary
        app.py
        models.py
        health endpoint
        rankings endpoint
        headlines endpoint
      Watchability engine
        ranking.py
        matchup_quality.py
        records.py
        standings.py
        rivalries.py
        spotlights.py
      Current news pipeline
        news/feeds.py
        news/service.py
        news/repository.py
        news/cursor.py
      Historical data loading
        data.py
        headlines.py
        sync_data.py
        sync_headlines.py
    PostgreSQL
      Authentication
        users
        accounts
        sessions
        rate limits
      Profiles
        username
        display name
        about
      Current news
        news_articles
        source and team indexes
        one-year retention
    NFL data sources
      Historical 2025 rankings
        nflverse through nflreadpy
        normalized Parquet
        checked-in pregame headline JSON
      Current news
        ESPN RSS
        CBS Sports RSS
        FOX Sports RSS
        hourly FastAPI synchronization
    Verification
      pytest backend tests
      Vitest component and route tests
      Ruff
      TypeScript
      ESLint
      Next.js production build
      Browser runtime checks
```

## 1. Matchup ranking request

```mermaid
flowchart LR
    USER["Browser /"]
    WORKSPACE["RankingsWorkspace"]
    CLIENT["lib/rankings.ts"]
    PROXY["Next.js /api/rankings"]
    API["FastAPI /api/v1/rankings"]
    MEMORY["SeasonData in memory"]
    ENGINE["ranking.py"]
    RESPONSE["GameSummary JSON"]

    USER --> WORKSPACE --> CLIENT --> PROXY --> API
    API --> MEMORY
    API --> ENGINE
    MEMORY --> ENGINE
    ENGINE --> RESPONSE --> PROXY --> WORKSPACE
```

FastAPI loads the normalized 2024–2025 Parquet data at startup. Ranking
requests do not query PostgreSQL, nflverse, RSS feeds, or an MCP server.

## 2. Current headline request and refresh

```mermaid
flowchart LR
    ESPN["ESPN RSS"]
    CBS["CBS Sports RSS"]
    FOX["FOX Sports RSS"]
    SCHEDULER["NewsSyncService every hour"]
    VALIDATE["RssFeedClient validation"]
    NEWS_DB[("PostgreSQL news_articles")]
    BROWSER["Browser /headlines"]
    UI["HeadlinesWorkspace"]
    NEXT_PROXY["Next.js /api/headlines"]
    FASTAPI["FastAPI /api/v1/headlines"]

    ESPN --> VALIDATE
    CBS --> VALIDATE
    FOX --> VALIDATE
    SCHEDULER --> VALIDATE --> NEWS_DB
    BROWSER --> UI --> NEXT_PROXY --> FASTAPI --> NEWS_DB
    NEWS_DB --> FASTAPI --> NEXT_PROXY --> UI
```

Publisher requests happen only in the background scheduler. User requests read
stored rows from PostgreSQL with `(published_at, id)` cursor pagination.
Current RSS articles never enter the watchability formula or the historical
2025 pregame-headline cache.

## 3. Authentication and profile request

```mermaid
flowchart LR
    USER["Browser"]
    AUTH_UI["Login / signup / account nav"]
    BETTER_AUTH["Better Auth route"]
    PROFILE_UI["Public profile / settings"]
    PROFILE_API["Next.js profile API"]
    DRIZZLE["Drizzle schema and queries"]
    POSTGRES[("PostgreSQL")]

    USER --> AUTH_UI --> BETTER_AUTH --> DRIZZLE --> POSTGRES
    USER --> PROFILE_UI --> PROFILE_API --> DRIZZLE --> POSTGRES
```

Authentication remains entirely inside Next.js. FastAPI never receives
passwords, session cookies, authentication tokens, or private email addresses.

## Important boundaries

- `frontend/src/app/api/*` are same-origin proxies or Next.js-owned account
  endpoints. The browser does not call FastAPI directly.
- `src/nflviewer/app.py` wires the Python runtime together; scoring logic stays
  in dedicated pure modules.
- `frontend/src/db/schema.ts` and `frontend/drizzle/` remain the migration
  authority for the shared PostgreSQL schema.
- The ranking path is in-memory and deterministic. The current-news path is
  PostgreSQL-backed and eventually consistent.
- Redis is not currently present. Ranking response caching and personalized
  ranking caches remain future work.
- The hourly news scheduler runs only while a FastAPI instance is running.

## Fast orientation

| Goal | Start here |
| --- | --- |
| Change the weekly score | `src/nflviewer/ranking.py` |
| Change team-quality calculations | `src/nflviewer/matchup_quality.py` |
| Change standings leverage | `src/nflviewer/standings.py` |
| Change the rankings interface | `frontend/src/components/rankings-workspace.tsx` |
| Change the live Headlines interface | `frontend/src/components/headlines/headlines-workspace.tsx` |
| Add or validate a news publisher | `src/nflviewer/news/feeds.py` |
| Change news persistence or pagination | `src/nflviewer/news/repository.py` |
| Change authentication | `frontend/src/lib/auth.ts` |
| Change public profiles | `frontend/src/lib/profiles.ts` |
| Change the database schema | `frontend/src/db/schema.ts` |
