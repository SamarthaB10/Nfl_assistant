# LeagueWatch

LeagueWatch is a Next.js and FastAPI application that ranks every 2025 NFL
regular-season matchup by how valuable it should be to watch and displays the
published 2026 regular-season schedule. It turns pregame team quality,
projected competitiveness, rivalry context, and standings consequences into a
transparent `1.00–10.00` watchability score for 2025 games.

The prototype answers a focused question:

> Given the NFL schedule for a particular week, which games are most—and
> least—worth watching?

The responsive web interface lets a user choose a week and request every game,
the top `x`, or the bottom `x`. Each result presents team records and logos
beside the watchability rating. Opening a matchup reveals its ranking reasons,
validated pregame headline, and two active player spotlights—one per team—with
pregame season totals, league-position context, and recent performance.

The FastAPI response stays focused: matchup, actual pregame records, final
scores when available, logo URLs, rating, human-readable reasons, and the two
player spotlights needed by the interface. This repository currently
implements the general NFL-watcher experience; favorite-team personalization
remains future work.

## Current capabilities

- Ranks all 2025 regular-season games for Weeks 1–18.
- Displays all published 2026 regular-season games for Weeks 1–18 without
  calculating watchability scores.
- Returns either the complete weekly slate, the top `x`, or the bottom `x`
  games.
- Scores games on an absolute `1.00–10.00` scale with two-decimal precision.
- Reconstructs records, scoring statistics, and standings strictly before the
  selected week.
- Uses a 2024 prior during Weeks 1–5, then switches entirely to 2025 data.
- Measures team strength from record, offense, defense, and point differential.
- Estimates matchup closeness from each offense against the opposing defense.
- Adds divisional, curated rivalry, playoff-cutoff, division-race, and
  conference top-seed context.
- Includes one validated pregame ESPN headline when available.
- Provides a mobile-first matchup interface with expandable insights.
- Supports email/password signup and login with database-backed sessions.
- Gives each account a unique public handle and mobile-first public profile.
- Lets profile owners edit their display name and About text without exposing
  their private email address.
- Aggregates current NFL offseason, transaction, injury, and training-camp
  coverage from the official ESPN, CBS Sports, FOX Sports, and NBC Sports
  syndication feeds.
- Refreshes live headlines hourly, retains one rolling year in PostgreSQL, and
  exposes cursor pagination with optional publisher and team filters.
- Provides a mobile-first Headlines tab with article imagery, publisher/team
  controls, loading and failure states, and cursor-based “Load 20 more.”
- Dynamically selects one active offensive player per team and explains each
  selection with two or three statistics available before that game.
- Explains ratings of `3.20` or lower with specific quality, blowout-risk, and
  low-stakes reasons.
- Uses deterministic football-specific tiebreakers when displayed scores are
  equal.
- Performs no network calls in the ranking request path.

## Quick start

### Requirements

- Python `3.12`
- Node.js `20.9` or newer
- Docker with Compose for local PostgreSQL
- [`uv`](https://docs.astral.sh/uv/)

### Install and run

```bash
git clone https://github.com/SamarthaB10/Nfl_assistant.git
cd Nfl_assistant
uv sync
uv run python -m nflviewer.sync_data
docker compose up -d --wait postgres
cp frontend/.env.example frontend/.env.local
cd frontend
npm ci
npm run db:migrate
cd ..
DATABASE_URL=postgresql://leaguewatch:leaguewatch@127.0.0.1:5433/leaguewatch \
  uv run fastapi dev
```

In a second terminal:

```bash
cd frontend
npm run dev
```

The data sync downloads the 2024 and 2025 schedule/statistics plus the 2026
schedule through `nflreadpy`, validates them, and writes normalized Parquet
files under `data/processed/`. Subsequent syncs use the local files unless
`--force` is supplied.

Open:

- Web app: <http://localhost:3000>
- Current NFL headlines: <http://localhost:3000/headlines>
- Swagger UI: <http://127.0.0.1:8000/docs>
- Health endpoint: <http://127.0.0.1:8000/health>

## Deploy the web app to Netlify

The repository is configured for Netlify through the root
[`netlify.toml`](netlify.toml). Netlify builds the Next.js application from
`frontend/` with Node.js 22 and publishes the `.next` output through Netlify's
native Next.js runtime. This deployment does not use OpenAI Sites.

The FastAPI process is a separate long-running service and must be deployed to
a Python host such as Render, Railway, or Fly.io before the Netlify site can
load rankings and live headlines. PostgreSQL must also be hosted outside
Netlify. Use a pooled PostgreSQL connection string when the provider offers
one.

Before importing the GitHub repository into Netlify:

1. Deploy FastAPI and confirm `GET /health` returns `200`.
2. Provision PostgreSQL and apply the frontend migrations:

   ```bash
   cd frontend
   DATABASE_URL="postgresql://..." npm run db:migrate
   ```

3. In Netlify, choose **Add new project → Import an existing project**, select
   this repository, and deploy the `main` branch. The committed configuration
   supplies the base directory, build command, publish directory, and Node.js
   version.
4. Add these variables under **Project configuration → Environment
   variables**:

   | Variable | Production value |
   | --- | --- |
   | `DATABASE_URL` | Hosted PostgreSQL connection string |
   | `BETTER_AUTH_SECRET` | Cryptographically random value of at least 32 characters |
   | `BETTER_AUTH_URL` | Exact Netlify production origin, such as `https://drizzle.example.com` |
   | `NFL_API_BASE_URL` | Public HTTPS origin of the deployed FastAPI service |

Do not place secrets in `netlify.toml` or commit a production `.env` file.
Deploy previews need their own safe environment-variable scope if accounts or
comments should work in previews. Database migrations are intentionally not
part of `npm run build`; run them explicitly before deploying schema changes
so a failed preview build cannot modify production data.

After the first production deploy, verify:

- `/` loads weekly rankings through FastAPI;
- `/headlines` loads current articles;
- signup, login, logout, and a public profile work;
- creating and deleting a comment works while signed in;
- security headers are present; and
- FastAPI `/health` remains healthy.

To roll back, select the previous successful production deploy in Netlify and
publish it. If the release included a database migration, review that
migration separately before rolling the schema back.

### Accounts and profiles

PostgreSQL listens on local host port `5433` so it does not conflict with a
system PostgreSQL installation on the default `5432`. The committed
`frontend/.env.example` points to this container.

Before using accounts outside local development, replace
`BETTER_AUTH_SECRET` with a cryptographically random value of at least 32
characters and set `BETTER_AUTH_URL` to the exact deployed origin. Never commit
the resulting `.env.local`.

Account routes:

- Sign up: <http://localhost:3000/signup>
- Log in: <http://localhost:3000/login>
- Public profile: `http://localhost:3000/u/<username>`
- Owner profile settings: <http://localhost:3000/settings/profile>

Email is private and is the only login identifier. Username, display name,
About text, and joined month are public. Version 1 uses local LeagueWatch
default profile/header artwork; image uploads and object storage are not yet
enabled.

Authentication and profile storage stay inside Next.js. FastAPI serves public
NFL ranking and headline data, but never receives passwords, session tokens, or
user email addresses.

The frontend proxies `/api/rankings` and `/api/headlines` to FastAPI so the
browser does not need a separate CORS configuration. Set `NFL_API_BASE_URL`
before starting Next.js only when FastAPI is not available at
`http://127.0.0.1:8000`.

To replace the local nflverse cache:

```bash
uv run python -m nflviewer.sync_data --force
```

The validated 2025 headline cache is checked into the repository. Rebuilding
it is optional and makes requests to ESPN's search endpoint:

```bash
uv run python -m nflviewer.sync_headlines
```

That cache is used only for historical 2025 matchup explanations. The
standalone live Headlines service does not import it. When FastAPI starts with
`DATABASE_URL` configured, it reads current articles from the official ESPN,
CBS Sports, FOX Sports, and NBC Sports feeds, stores them in `news_articles`,
and checks for updates once per hour. NBC Atom entries are enriched from their
canonical article metadata for author, image, and publisher-provided team tags.

## API

### `GET /api/v1/rankings`

Ranks one week of the 2025 regular season or returns one week of the 2026
schedule.

| Query field | Required | Validation | Meaning |
| --- | --- | --- | --- |
| `season` | No | `2025` or `2026` | Ranked season or schedule-only season; defaults to `2025` |
| `week` | Yes | Integer `1–18` | Week to rank |
| `top` | No | Integer `1–16` for 2025 | Return only the highest-rated games |
| `bottom` | No | Integer `1–16` for 2025 | Return only the lowest-rated games, worst first |

`top` and `bottom` are mutually exclusive. If both are omitted, the complete
slate is returned from highest to lowest.

Examples:

```bash
# Complete Week 4 slate
curl "http://127.0.0.1:8000/api/v1/rankings?season=2025&week=4"

# Five best Week 4 games
curl "http://127.0.0.1:8000/api/v1/rankings?season=2025&week=4&top=5"

# Five least-watchable Week 4 games
curl "http://127.0.0.1:8000/api/v1/rankings?season=2025&week=4&bottom=5"

# Published Week 1 2026 schedule; no score or ranking limit is returned
curl "http://127.0.0.1:8000/api/v1/rankings?season=2026&week=1"
```

Example response:

```json
[
  {
    "matchup": "Seattle Seahawks vs San Francisco 49ers",
    "records": {
      "SEA": "13-3",
      "SF": "12-4"
    },
    "logos": {
      "SEA": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png",
      "SF": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png"
    },
    "finalScores": {
      "SEA": 13,
      "SF": 3
    },
    "score": 8.39,
    "reasons": [
      "Both teams have winning records",
      "Divisional matchup",
      "Direct division race matchup",
      "Seattle Seahawks profile: elite record, top-tier offense, top-tier defense",
      "San Francisco 49ers profile: elite record, above-average offense, above-average defense",
      "Projected matchup closeness: 0.87/1.00",
      "Headline: 49ers host the Seahawks in the season finale with the division title and top NFC seed on the line"
    ]
  }
]
```

The displayed records are the actual 2025 records before that game. Early
season prior values affect scoring only; they are never shown as the team's
record. `finalScores` is populated from nflverse only when both teams have a
score; unfinished games return an empty object.

### Weekly player availability

The explicit data sync loads 2025 weekly rosters with
`nflreadpy.load_rosters_weekly([2025])` and caches them at
`data/processed/rosters-weekly-2025-v2.parquet`. It also loads weekly 2024 and
2025 player statistics with
`nflreadpy.load_player_stats([2024, 2025], summary_level="week")` and caches
them at `data/processed/player-stats-2024-2025.parquet`.

For the requested week, each game includes one `playersToWatch` entry per team.
Candidates must have an `ACT` weekly roster status and play quarterback,
running back, fullback, wide receiver, or tight end. Selection favors the
active player with the strongest pregame production. Each entry includes:

- a season-to-date yardage total appropriate to the position;
- a touchdown fact that includes both a top-five peer rank and the touchdown
  count when applicable; and
- a top-five yardage rank or prior-week production fact when available.

Weeks 2–18 use only 2025 regular-season statistics from before the selected
week. Week 1 uses 2024 production as context while still requiring the player
to be active on the 2025 Week 1 roster. Selected-week and future statistics are
never included.

Each game also includes `unavailablePlayerIds`: rostered player IDs whose
weekly status is not `ACT`. The frontend keeps a curated player map only as a
backward-compatible fallback for API responses created before dynamic
spotlights were added.

This is roster-availability filtering, not a complete historical injury report.
The official nflverse injuries pipeline stops after 2024, so 2025 statuses come
from weekly rosters and can identify designations such as `RES`, `PUP`, and
`INA`, but not the full Questionable/Doubtful/Out reporting history. A missing
weekly roster row is unknown and does not disqualify the player, so it is not
evidence that the player was active.

### `GET /health`

Reports whether the season data loaded successfully and identifies the active
formula:

```json
{
  "status": "ok",
  "dataLoaded": true,
  "supportedSeason": 2025,
  "formulaVersion": "dynamic-watchability-v6"
}
```

The API returns:

- `422` for invalid query fields, including an unsupported week or combining
  `top` and `bottom`;
- `503` from the rankings endpoint when the NFL data cache could not be loaded.

### `GET /api/v1/headlines`

Returns current NFL reporting stored in PostgreSQL, newest first. This feed is
independent from the historical 2025 ranking data and is intended for current
offseason and training-camp coverage.

| Query field | Default | Validation | Meaning |
| --- | --- | --- | --- |
| `limit` | `20` | Integer `1–50` | Maximum stories returned |
| `cursor` | none | Opaque cursor from the prior response | Continue pagination |
| `source` | none | `ESPN`, `CBS`, `FOX`, or `NBC` | Filter by publisher |
| `team` | none | NFL abbreviation such as `NE` | Filter by tagged team |

```bash
# Newest 20 stories
curl "http://127.0.0.1:8000/api/v1/headlines"

# Up to 20 Patriots stories from ESPN
curl "http://127.0.0.1:8000/api/v1/headlines?source=ESPN&team=NE"
```

Example response:

```json
{
  "items": [
    {
      "id": 10482,
      "source": "ESPN",
      "title": "Example current NFL headline",
      "author": "Example Author",
      "excerpt": "Feed-provided summary.",
      "url": "https://www.espn.com/nfl/story/_/id/example",
      "imageUrl": "https://example.com/image.jpg",
      "teamCodes": ["NE"],
      "publishedAt": "2026-07-29T19:02:00Z"
    }
  ],
  "nextCursor": null,
  "hasMore": false
}
```

Pass `nextCursor` unchanged as the next request's `cursor`. Invalid filters or
cursors return `422`. If `DATABASE_URL` is missing or PostgreSQL is
unavailable, this endpoint returns `503`; rankings remain available.

The hourly synchronizer starts with FastAPI, runs immediately when stored
source data is stale, and uses a PostgreSQL advisory lock to prevent duplicate
work across API instances. Publisher failures are isolated, so successfully
stored stories remain readable and other publishers can still refresh. Rows
older than one year by publisher timestamp are removed after synchronization.

## System architecture

LeagueWatch separates three concerns: the browser-facing Next.js application,
the FastAPI ranking service, and durable account storage. PostgreSQL runs in
Docker for reproducible local development; it is not on the NFL ranking request
path.

For a file-level orientation of every runtime path, see the
[LeagueWatch codebase mind map](docs/codebase-mind-map.md).

```mermaid
flowchart TB
    USER["Mobile or desktop browser"]

    subgraph WEB["Next.js 16 and React 19"]
        UI["LeagueWatch interface"]
        RANK_PROXY["Rankings API proxy"]
        AUTH["Better Auth API"]
        PROFILE["Public profile pages and owner profile API"]
    end

    subgraph RANKING["Python ranking service"]
        API["FastAPI GET /api/v1/rankings"]
        ENGINE["Watchability v6 scoring and deterministic ranking"]
        SEASON["Validated SeasonData in memory"]
        HEADLINE_LOOKUP["Pregame headlines in memory"]
    end

    subgraph LIVE_NEWS["Current NFL news service"]
        NEWS_API["FastAPI GET /api/v1/headlines"]
        SCHEDULER["Hourly isolated synchronizer"]
        FEEDS["Official ESPN, CBS, FOX, and NBC syndication feeds"]
    end

    subgraph LOCAL_DATA["Persisted NFL data"]
        PARQUET["Normalized nflverse Parquet files"]
        HEADLINE_JSON["Validated 2025 headline JSON"]
    end

    subgraph DOCKER["Docker Compose local infrastructure"]
        POSTGRES["PostgreSQL 16<br/>accounts, profiles, and live news_articles"]
        VOLUME["Named persistent volume"]
    end

    subgraph SYNC["Explicit offline synchronization"]
        NFLVERSE["nflverse"]
        NFLREADPY["nflreadpy loaders"]
        VALIDATE["Schema and integrity validation"]
        ESPN["ESPN search"]
        FILTER["Pregame headline validation"]
    end

    USER --> UI
    UI --> RANK_PROXY
    RANK_PROXY --> API
    API --> ENGINE
    ENGINE -->|"compact JSON ratings"| RANK_PROXY

    UI --> AUTH
    UI --> PROFILE
    AUTH --> POSTGRES
    PROFILE --> POSTGRES
    POSTGRES --- VOLUME

    PARQUET -->|"loaded once at startup"| SEASON
    HEADLINE_JSON -->|"loaded once at startup"| HEADLINE_LOOKUP
    SEASON --> ENGINE
    HEADLINE_LOOKUP --> ENGINE

    UI --> NEWS_API
    NEWS_API --> POSTGRES
    SCHEDULER --> FEEDS
    SCHEDULER --> POSTGRES

    NFLVERSE --> NFLREADPY
    NFLREADPY --> VALIDATE
    VALIDATE --> PARQUET
    ESPN --> FILTER
    FILTER --> HEADLINE_JSON
```

The resulting boundaries are:

- **Ranking path:** browser → Next.js proxy → FastAPI → in-memory scoring. It
  does not query PostgreSQL, nflverse, ESPN, or an MCP server.
- **Identity path:** browser → Better Auth or the profile API → PostgreSQL.
  Password hashing and session handling remain isolated from FastAPI.
- **Live-news path:** browser → FastAPI → PostgreSQL. A separate hourly
  background task ingests only current official RSS metadata; live publisher
  requests never occur in a user request.
- **Synchronization path:** explicit CLI commands download and validate NFL
  ranking data before replacing the local Parquet or historical JSON cache.
- **Docker boundary:** only local PostgreSQL runs in Compose. Its named volume
  preserves accounts and live headline metadata when the container is
  recreated. A production deployment can replace it with managed PostgreSQL
  without changing the application data model.
- **Current cache boundary:** source data is persisted and held in memory, but
  final weekly rating responses are not cached in Redis.

### Request lifecycle

1. FastAPI loads the normalized Parquet cache once during application startup.
2. A validated request supplies `week` and optional `top` or `bottom`.
3. The service selects that week's matchups.
4. It reconstructs 2025 records, point totals, and standings using only games
   with `gameWeek < requestedWeek`.
5. It creates league-relative offense, defense, and point-differential
   percentiles.
6. Each game receives a matchup-quality score and a context score.
7. Games are sorted using unrounded values and deterministic secondary keys.
8. `top` or `bottom` selection is applied after the entire slate is scored.
9. A cached headline may be appended as an explanatory reason.
10. Internal scoring details are reduced to the public `GameSummary` model.

### Latency and caching

Ranking requests do not download nflverse data, query ESPN, or call a database.
The application loads local Parquet into memory at startup and calculates one
weekly slate from that in-memory state. This keeps the MVP request path fast and
deterministic without adding Redis or a database.

Redis was intentionally not added to the prototype. A distributed cache becomes
useful when the service runs across multiple instances, supports many seasons
or personalized scoring, or receives enough traffic that recomputing the same
week is material. At that point, an appropriate cache key would include at
least:

```text
formulaVersion : season : week : viewerProfile : selection
```

Formula versioning is essential because cached scores from different scoring
models must never be mixed.

## Watchability formula v6

The model produces a watchability rating, not a win probability, point spread,
or predicted final score. All intermediate values are normalized to
`0.00–1.00`.

The two top-level benchmarks are:

```text
55% pure matchup quality
45% rivalry and standings context
```

### Variables

| Variable | Meaning | Range |
| --- | --- | ---: |
| `W_i` | Pregame scoring win rate for team `i` | `0.00–1.00` |
| `O_i` | League-relative points-scored percentile | `0.00–1.00` |
| `D_i` | League-relative defensive percentile | `0.00–1.00` |
| `P_i` | League-relative point-differential percentile | `0.00–1.00` |
| `T_i` | Team strength | `0.00–1.00` |
| `C` | Expected competitive closeness | `0.00–1.00` |
| `Q` | Pure matchup quality | `0.00–1.00` |
| `R` | Rivalry value | `0.00–0.20` |
| `L` | Standings leverage | `0.00–0.82` |
| `X` | Saturated context value | `0.00–1.00` |
| `N` | Normalized watchability | `0.00–1.00` |
| `S` | Public watchability score | `1.00–10.00` |

### 1. Pregame data boundary

For requested Week `K`, only completed regular-season games satisfying this
condition are used:

```text
gameWeek < K
```

The target game and all future games are excluded from records, scoring rates,
point differential, and standings. This prevents historical-result leakage
when the complete 2025 schedule cache is used to reconstruct an earlier week.

### 2. Early-season record prior

Week 1 has no current-season evidence, so treating every team as exactly equal
would make its rankings nearly context-only. Weeks 1–5 therefore use a
four-game-equivalent prior based on the team's final 2024 record.

```text
previousWinRate =
  (previousWins + 0.5 × previousTies) / previousGames

W_i =
  (4 × previousWinRate + currentWins + 0.5 × currentTies)
  / (4 + currentGames)
```

From Week 6 onward:

```text
W_i =
  (currentWins + 0.5 × currentTies) / currentGames
```

A tie is treated as half a win. A team is considered to have a winning record
for explanatory purposes only when `W_i > 0.50`.

The same four-game prior is applied independently to points scored and points
allowed during Weeks 1–5. It is fully removed starting in Week 6.

### 3. League-relative team metrics

For every team, the service calculates:

```text
pointsForPerGame
pointsAllowedPerGame
pointDifferentialPerGame =
  pointsForPerGame - pointsAllowedPerGame
```

These rates are converted to percentiles within that week's league
environment:

- higher points scored is better;
- fewer points allowed is better;
- higher point differential is better.

Ties receive a midpoint percentile:

```text
percentile =
  (numberOfWorseTeams + 0.5 × numberOfOtherTiedTeams)
  / (numberOfTeams - 1)
```

Percentiles avoid arbitrary fixed bands and automatically adjust to whether a
particular season is high- or low-scoring.

### 4. Team strength

Each team receives equal weight across four understandable signals:

```text
T_i = (W_i + O_i + D_i + P_i) / 4
```

| Team-strength input | Weight within `T_i` |
| --- | ---: |
| Pregame win rate | `25%` |
| Offense percentile | `25%` |
| Defense percentile | `25%` |
| Point-differential percentile | `25%` |

The combination prevents a misleading record from being the only definition of
quality. It also prevents strong underlying statistics from completely erasing
poor game results.

### 5. Offense-versus-defense projection

The model estimates how the scoring profiles interact:

```text
homeExpectedPoints =
  (homePointsForPerGame + awayPointsAllowedPerGame) / 2

awayExpectedPoints =
  (awayPointsForPerGame + homePointsAllowedPerGame) / 2
```

This is a compatibility signal only. There is no home-field bump and no Vegas
line.

### 6. Competitive closeness

```text
C =
  1 - abs(homeExpectedPoints - awayExpectedPoints)
      / max(homeExpectedPoints, awayExpectedPoints, 1)
```

`C` is clamped to `0.00–1.00`. Similar expected scoring profiles approach
`1.00`; projected mismatches reduce the value.

Closeness cannot make two weak teams a premium game because it only modifies
the strength already contributed by the pair.

### 7. Pure matchup quality

First, the geometric mean requires both teams to contribute strength:

```text
pairStrength = sqrt(homeTeamStrength × awayTeamStrength)
```

The pair is then adjusted by closeness:

```text
Q = pairStrength × (0.65 + 0.35 × C)
```

The `65/35` structure makes team strength the primary signal while preserving a
meaningful imbalance penalty:

- `65%` of matchup quality is retained from pair strength regardless of
  closeness;
- the remaining `35%` depends on the offense-defense compatibility;
- a strong projected matchup receives the full strength value when `C = 1`;
- a mismatch can reduce, but cannot completely erase, value created by two
  strong teams.

Because `Q` is `55%` of the final normalized score, this produces the following
structural allocation:

| Final-score component | Maximum structural share |
| --- | ---: |
| Pair-strength base | `35.75%` (`55% × 65%`) |
| Closeness-conditioned quality | `19.25%` (`55% × 35%`) |
| Context and standings | `45.00%` |

The individual record/offense/defense/differential inputs remain equal inside
each team's nonlinear geometric pair-strength calculation, so they should not
be interpreted as simple additive percentages of the final score.

### 8. Rivalry value

Only the strongest applicable rivalry category is used:

| Category | `R` |
| --- | ---: |
| Same division | `0.20` |
| Named conference or interconference rivalry | `0.12` |
| Historic or regional rivalry | `0.06` |
| No recognized rivalry | `0.00` |

Categories do not stack. The nflverse divisional flag takes precedence over the
curated rivalry map in `data/rivalries.json`.

### 9. Standings leverage

Standings are reconstructed before the requested week. Teams are ordered within
their division and conference by:

```text
win rate, then point differential, then team ID
```

For each team, the model evaluates proximity to three boundaries:

- division lead;
- seventh-place conference playoff cutoff;
- conference top seed.

For each objective:

```text
remainingGames = max(1, 17 - gamesPlayed)

proximity =
  max(0, 1 - min(|marginAfterWin|, |marginAfterLoss|) / remainingGames)

consequence =
  1.0  if the result crosses the boundary or creates a two-win swing
  0.5  otherwise

objectiveImpact = min(1, proximity × consequence)
```

The strongest objective is retained for each team. Both teams' impacts are
combined without simple addition:

```text
gameImpact =
  1 - (1 - homeImpact) × (1 - awayImpact)

seasonMaturity =
  clamp((week - 1) / 17, 0, 1)

L =
  0.82 × seasonMaturity × gameImpact
```

The maturity term makes a similar standings gap more consequential late in the
season than early in the season.

This is a deterministic prototype approximation. It does not implement the
NFL's complete head-to-head, division-record, conference-record,
common-opponents, strength-of-victory, and strength-of-schedule tiebreaker
sequence.

### 10. Context saturation

Rivalry fills only the context space not already occupied by standings
leverage:

```text
X = L + (1 - L) × R
```

This saturation prevents independent context signals from stacking
unboundedly. A late-season game with real division or playoff consequences can
outrank a slightly stronger ordinary matchup, while rivalry alone cannot turn
two poor teams into the best game of the week.

### 11. Final watchability score

```text
N = 0.55 × Q + 0.45 × X

S =
  round(1 + 9 × clamp(N, 0, 1), 2)
```

| Normalized value `N` | Public score `S` |
| ---: | ---: |
| `0.00` | `1.00` |
| `0.25` | `3.25` |
| `0.50` | `5.50` |
| `0.75` | `7.75` |
| `1.00` | `10.00` |

A score is an absolute model output, not a percentile within that week's slate.
The API may serialize `8.50` as `8.5`; a frontend should format scores to two
decimal places.

### 12. Ranking tiebreakers

Sorting uses the unrounded normalized score before the two-decimal display
value. If games remain tied, the backend applies:

```text
1. Context value
2. Pure matchup quality
3. Competitive closeness
4. Record quality
5. Standings leverage
6. Rivalry value
7. Earlier kickoff
8. Game ID
```

This means two games that both display `7.42` can still have a stable,
football-relevant order.

## Explanatory reasons and headlines

The numeric calculation can generate reasons for:

- both teams having winning records;
- adjusted winning records during Weeks 1–5;
- a divisional or curated rivalry;
- direct division-race consequences;
- playoff-cutoff implications;
- conference top-seed implications;
- a plain-language record, offense, and defense profile for each team when
  combined matchup quality is strong;
- the corresponding `0.00–1.00` projected matchup closeness;
- a close offense-defense projection for other competitive games.

For a displayed score of `3.20` or lower, the model instead adds at least one
negative explanation. The applicable reasons identify below-average strength
for both teams, elevated blowout risk, or limited rivalry and standings stakes.
If no individual diagnostic crosses its threshold, the response explains that
combined quality and context remain below the weekly standard.

Headline reasons are display-only. They have exactly zero effect on scores,
ordering, or tiebreakers.

Team-profile descriptions translate the same pregame inputs used by the
formula into league-relative labels. Record labels range from losing through
elite; offense and defense labels range from below average through top tier.
These labels replace the internal `0.00–1.00` strength values in user-facing
reasons without changing any score.

The optional headline sync applies several safeguards:

- only ESPN NFL URLs are accepted;
- the article must be published during the 14 days before kickoff;
- the title must mention both teams;
- post-kickoff articles are excluded;
- betting, odds, picks, and prediction content is excluded;
- a preview URL is preferred, then the most recent valid result.

These constraints prevent postgame result leakage into a pregame ranking.

## Data validation and correctness boundaries

Before nflverse data is accepted, the service verifies:

- required schedule and team columns exist;
- only 2024, 2025, and 2026 regular-season games are retained;
- game IDs are unique;
- a completed game has both scores, never exactly one;
- all 32 teams have metadata;
- legacy aliases such as `LA → LAR` and `JAC → JAX` are normalized;
- kickoff timestamps are parsed in US Eastern time and represented as UTC in
  the runtime matchup model.

The application fails closed for ranking requests when the cache cannot be
loaded. `/health` remains available and reports `"dataLoaded": false` for
diagnosis.

## Project structure

```text
.
├── data/
│   ├── headlines-2025.json       # Validated, display-only pregame headlines
│   ├── rivalries.json            # Curated non-divisional rivalry categories
│   └── processed/                # Generated nflverse Parquet cache
├── frontend/
│   ├── drizzle/                  # Committed PostgreSQL migrations
│   ├── src/app/                  # Rankings, auth, profile pages, and API routes
│   ├── src/components/           # Ranking, account, and profile components
│   ├── src/db/                   # Drizzle PostgreSQL schema and connection
│   ├── src/lib/                  # Auth, profile, ranking, and spotlight logic
│   └── package.json              # Frontend dependencies and quality commands
├── src/nflviewer/
│   ├── app.py                    # FastAPI lifecycle, routes, response shaping
│   ├── data.py                   # nflverse validation, aggregation, caching
│   ├── headlines.py              # Headline validation and read-only lookup
│   ├── matchup_quality.py        # Team strength and matchup-quality formula
│   ├── models.py                 # Pydantic query, internal, and API models
│   ├── ranking.py                # 55/45 composition, reasons, sorting
│   ├── records.py                # Win-rate and early-season prior logic
│   ├── rivalries.py              # Rivalry classification and values
│   ├── spotlights.py             # Active player selection and pregame facts
│   ├── standings.py              # Standings reconstruction and leverage
│   ├── sync_data.py              # nflverse synchronization CLI
│   └── sync_headlines.py         # Optional ESPN headline backfill CLI
├── tests/                        # Unit and API regression tests
├── ELOformula.md                 # Dedicated formula reference
└── pyproject.toml                # Dependencies and tool configuration
```

Despite the historical `ELOformula.md` filename, this version does not
calculate Elo ratings.

## Technology choices

| Technology | Role | Why it fits the MVP |
| --- | --- | --- |
| Python 3.12 | Scoring and service runtime | Natural fit for data processing and nflverse tooling |
| FastAPI | HTTP API and Swagger UI | Typed validation and an immediately usable prototype UI |
| Pydantic | Query and response contracts | Rejects invalid weeks/selections at the API boundary |
| Polars | Schedule/stat aggregation | Fast DataFrame operations over nflverse data |
| nflreadpy | nflverse ingestion | Free access to schedules and team metadata for the prototype |
| Parquet | Local normalized cache | Compact, typed, and fast to load without a database |
| Next.js 16 | Responsive web interface and API proxy | One typed application for the UI and server-side FastAPI proxy |
| React 19 + TypeScript | Interactive matchup cards | Accessible stateful controls with checked API contracts |
| PostgreSQL 16 | Users, credentials, sessions, and profiles | Durable relational constraints for unique identities and read-heavy profiles |
| Better Auth | Email/password authentication | Owns scrypt password hashing, cookie sessions, and auth rate limiting |
| Drizzle ORM + Kit | Typed account persistence and migrations | Keeps PostgreSQL access typed and schema changes reviewable |
| pytest | Regression tests | Covers data boundaries, formula behavior, and API output |
| Vitest + Testing Library | Frontend regression tests | Covers initial loading, selection, errors, and expandable details |
| Ruff | Linting and formatting | One fast, deterministic Python quality tool |

No paid NFL API, Vegas feed, Redis instance, or MCP server is required to run
this version. A local PostgreSQL container is required for account features.

## Development commands

| Command | Purpose |
| --- | --- |
| `uv sync` | Install locked application and development dependencies |
| `uv run python -m nflviewer.sync_data` | Create the local nflverse cache if missing |
| `uv run python -m nflviewer.sync_data --force` | Replace the nflverse cache |
| `uv run python -m nflviewer.sync_headlines` | Rebuild the optional headline cache |
| `uv run fastapi dev` | Start the development server |
| `uv run pytest` | Run the complete test suite |
| `uv run ruff check .` | Run lint checks |
| `uv run ruff format --check .` | Verify formatting |
| `cd frontend && npm run dev` | Start the Next.js development server |
| `docker compose up -d --wait postgres` | Start local PostgreSQL on port `5433` |
| `cd frontend && npm run db:generate` | Generate a migration from schema changes |
| `cd frontend && npm run db:migrate` | Apply committed PostgreSQL migrations |
| `cd frontend && npm run db:check` | Validate the Drizzle migration history |
| `cd frontend && npm test` | Run frontend unit/component tests |
| `cd frontend && npm run typecheck` | Check TypeScript without emitting files |
| `cd frontend && npm run lint` | Run Next.js ESLint rules |
| `cd frontend && npm run build` | Produce a production frontend build |

## Testing strategy

The test suite covers:

- nflverse schema and integrity validation;
- cache creation and reload behavior;
- preweek record, metric, and standings boundaries;
- exclusion of target-week and future results;
- early-season prior activation and removal;
- percentile handling, including tied values;
- rivalry categories and non-stacking behavior;
- matchup-quality and final `55/45` composition;
- weak-but-close and strong-but-imbalanced games;
- standings leverage and late-season maturity;
- deterministic score tiebreakers;
- `top` and `bottom` selection;
- Pydantic query validation;
- compact API response shape;
- headline filtering and postgame-leakage prevention;
- active player selection, pregame stat boundaries, and peer rankings;
- graceful `503` behavior when data is unavailable;
- frontend query construction and FastAPI proxy behavior;
- initial, top, and bottom matchup loading;
- team-logo rendering, detail expansion, headlines, and player spotlights;
- frontend error handling without removing the ranking controls.
- signup/login validation and generic credential failures;
- strict public-profile field mapping;
- anonymous and cross-account profile-update rejection;
- public profile and owner-edit component behavior.

Run the complete quality gate:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
cd frontend
npm test
npm run typecheck
npm run lint
npm run build
npm audit --audit-level=high
```

## Known limitations

- Only the 2025 regular season is scored; 2026 currently provides schedule data
  without rankings.
- The API currently ranks for a general viewer; favorite-team personalization
  is not implemented.
- Injuries do not affect watchability scores. Player cards use weekly roster
  availability, but adding injury-based scoring safely still requires confirmed
  starter status, position-impact tiers, availability timing, and replacement
  quality.
- Vegas lines are intentionally excluded.
- Headlines explain context but do not numerically measure public interest.
- Scoring statistics use season-to-date averages rather than opponent-adjusted
  efficiency, EPA, success rate, or recent-form windows.
- Standings use a deterministic approximation rather than the complete NFL
  tiebreaker procedure.
- Weekly results are calculated on demand and are not cached in Redis.
- Player spotlights currently cover offensive skill positions only. Their
  statistics explain who to watch but do not affect the watchability score.
- Team logos and player headshots are loaded from ESPN-hosted URLs for this
  prototype. A production release must confirm media usage rights and provide
  a licensed or owned asset pipeline.
- Email verification, password recovery, OAuth, account deletion, username
  changes, and profile image uploads are not implemented yet.
- `npm audit` reports a moderate advisory in Drizzle Kit's development-only
  `esbuild` loader chain. npm's automated remedy is a breaking Drizzle Kit
  downgrade, so the project currently gates on high-severity findings and
  should adopt an upstream non-breaking fix when available.

## Roadmap

### Near-term platform backlog

Authentication and the first database-backed public profile are now
implemented. The remaining platform work is:

1. **Email ownership verification**
   - Send a short-lived, one-time verification code to the submitted email
     address before treating an account as verified.
   - Store only a hash of the code, enforce expiration and attempt limits, and
     add resend cooldowns plus rate limits for both email and IP address.
   - Keep verification state in PostgreSQL and define which account and
     personalization features remain unavailable until verification succeeds.
   - Select an email provider and production sender domain before
     implementation. Verification proves control of a mailbox; it does not
     guarantee that an address is permanent or non-disposable.
2. **Persistent NFL data pipeline**
   - Add a scheduled, idempotent nflverse ingestion job rather than treating
     upstream downloads as an application concern.
   - Store normalized schedules, weekly team statistics, standings inputs,
     rosters, and data-version metadata in a database.
   - Preserve historical weekly snapshots so rankings remain reproducible when
     upstream datasets change.
3. **Application caching**
   - Cache fully ranked weekly slates and derive top/bottom selections from the
     cached result.
   - Include season, week, formula version, data version, and viewer profile in
     cache keys.
   - Define invalidation around completed data syncs and formula releases before
     introducing Redis or another distributed cache.

The current request path already makes no nflverse network calls: it reads
locally synchronized Parquet data into memory at startup. The database pipeline
would make that synchronization durable and operationally managed; the caching
layer would avoid repeated scoring and database reads after that pipeline
exists.

### Product and scoring backlog

The next product and model increments are:

1. Add a dedicated home page that introduces LeagueWatch, surfaces the current
   week's best games, and provides a clear path into the full rankings.
2. Add a curated YouTube video section to the home page.
   - Decide between manually managed links and YouTube Data API discovery.
   - Define which video categories belong in the product, how frequently links
     are refreshed, and whether videos open externally or use
     privacy-enhanced embeds.
   - Display source/channel attribution and never treat video popularity as a
     watchability-score input without a separate scoring decision.
3. Add the first user preference: favorite team or general NFL watcher, stored
   per account with an explicit neutral/default state.
4. Add a serious, explainable personalization layer on top of the universal
   matchup score.
   - Preserve the general-viewer score as the stable quality baseline rather
     than maintaining a separate opaque formula per user.
   - Add user-context value for the favorite team's games, divisional and
     conference consequences, rivalry relevance, playoff leverage, and outcomes
     that materially affect the selected team's standing.
   - Keep team quality, competitiveness, injury penalties, and league-wide
     can't-miss games active so personalization cannot promote a poor game only
     because it is adjacent to the user's team.
   - Return personalized explanations that identify which preference changed a
     ranking, and version both the base formula and personalization formula.
   - Include preference and personalization versions in cache keys; invalidate
     personalized results when the user changes teams or the model changes.
   - Validate that general-watcher accounts receive the same ordering as
     anonymous users and test personalized rankings against historical weekly
     standings scenarios before release.
5. Add starter-only injury adjustments with position tiers and explicit
   availability confidence.
6. Replace approximate standings ordering with official NFL tiebreaker logic or
   a playoff-probability simulation.
7. Add opponent-adjusted efficiency and recent-form features after validating
   them against historical outcomes.
8. Add defensive-player spotlights and richer opponent-relative player context.
9. Add a postgame **Game Stats** view for completed matchups.
   - Show a compact button beside the existing comments control only after the
     game status is final.
   - Open a mobile-first view with offense and defense tabs, team summary
     metrics, player headshots, and position-specific box-score statistics.
   - Load the completed game's player and team statistics from nflverse, attach
     them to the canonical `game_key`, and keep the control hidden while the
     game is scheduled or in progress.
   - Treat this as postgame context only; it must not change the matchup's
     original watchability score or pregame explanations.

The complete scoring reference is available in
[ELOformula.md](ELOformula.md).
