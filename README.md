# LeagueWatch

LeagueWatch is a Next.js and FastAPI application that ranks every 2025 NFL
regular-season matchup by how valuable it should be to watch. It turns pregame
team quality, projected competitiveness, rivalry context, and standings
consequences into a transparent `1.00–10.00` watchability score.

The prototype answers a focused question:

> Given the NFL schedule for a particular week, which games are most—and
> least—worth watching?

The responsive web interface lets a user choose a week and request every game,
the top `x`, or the bottom `x`. Each result presents team records and logos
beside the watchability rating. Opening a matchup reveals its ranking reasons,
validated pregame headline, and two active player spotlights—one per team—with
pregame season totals, league-position context, and recent performance.

The FastAPI response stays focused: matchup, actual pregame records, logo URLs,
rating, human-readable reasons, and the two player spotlights needed by the
interface. This repository currently implements the general NFL-watcher
experience; favorite-team personalization remains future work.

## Current capabilities

- Ranks all 2025 regular-season games for Weeks 1–18.
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
- [`uv`](https://docs.astral.sh/uv/)

### Install and run

```bash
git clone https://github.com/SamarthaB10/Nfl_assistant.git
cd Nfl_assistant
uv sync
uv run python -m nflviewer.sync_data
uv run fastapi dev
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The data sync downloads 2024 and 2025 schedule, team, weekly roster, and player
statistics through `nflreadpy`, validates them, and writes normalized Parquet
files under `data/processed/`. Subsequent syncs use the local files unless
`--force` is supplied.

Open:

- Web app: <http://localhost:3000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- Health endpoint: <http://127.0.0.1:8000/health>

The frontend proxies `/api/rankings` to FastAPI so the browser does not need a
separate CORS configuration. Set `NFL_API_BASE_URL` before starting Next.js
only when FastAPI is not available at `http://127.0.0.1:8000`.

To replace the local nflverse cache:

```bash
uv run python -m nflviewer.sync_data --force
```

The validated 2025 headline cache is checked into the repository. Rebuilding
it is optional and makes requests to ESPN's search endpoint:

```bash
uv run python -m nflviewer.sync_headlines
```

## API

### `GET /api/v1/rankings`

Ranks one week of the 2025 regular season.

| Query field | Required | Validation | Meaning |
| --- | --- | --- | --- |
| `season` | No | Exactly `2025` | Supported season; defaults to `2025` |
| `week` | Yes | Integer `1–18` | Week to rank |
| `top` | No | Integer `1–16` | Return only the highest-rated games |
| `bottom` | No | Integer `1–16` | Return only the lowest-rated games, worst first |

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
record.

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

## System architecture

The prototype separates offline data collection from the low-latency request
path.

```mermaid
flowchart LR
    subgraph Sync["Offline / explicit synchronization"]
        NV["nflverse data"] --> NR["nflreadpy"]
        NR --> DV["Schema and integrity validation"]
        DV --> PQ["Local Parquet cache"]
        ESPN["ESPN search"] --> HF["Pregame headline filters"]
        HF --> HJ["Headline JSON cache"]
    end

    subgraph Runtime["FastAPI runtime"]
        PQ --> MEM["Validated SeasonData in memory"]
        RQ["GET /api/v1/rankings"] --> PRE["Build preweek records, metrics, and standings"]
        MEM --> PRE
        PRE --> MQ["Calculate matchup quality"]
        PRE --> CTX["Calculate rivalry and standings context"]
        MQ --> SCORE["Compose and rank scores"]
        CTX --> SCORE
        SCORE --> SUMMARY["Compact GameSummary response"]
        HJ --> SUMMARY
    end
```

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
- only 2024 and 2025 regular-season games are retained;
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
│   ├── src/app/                  # Next.js page shell, API proxy, and styles
│   ├── src/components/           # Ranking controls and expandable game cards
│   ├── src/lib/                  # Typed API client and player spotlights
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
| pytest | Regression tests | Covers data boundaries, formula behavior, and API output |
| Vitest + Testing Library | Frontend regression tests | Covers initial loading, selection, errors, and expandable details |
| Ruff | Linting and formatting | One fast, deterministic Python quality tool |

No paid NFL API, Vegas feed, database, Redis instance, or MCP server is required
to run this version.

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
```

## Known limitations

- Only the 2025 regular season is supported.
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

## Roadmap

### Near-term platform backlog

These items are recorded for ideation before implementation; no provider or
infrastructure decision has been made yet.

1. **Authentication**
   - Determine what requires an account, beginning with saved favorite teams
     and viewer preferences.
   - Compare social providers, email magic links, and traditional credentials.
   - Decide the session model, account-linking behavior, and guest-to-account
     migration before selecting an authentication library.
2. **Database-backed user profiles**
   - Store one profile per authenticated user, with a display name, avatar,
     favorite teams or general-watcher status, and saved interface preferences.
   - Define profile visibility, authorization, account deletion, and
     provider-account linking before finalizing the schema.
   - Keep private account data separate from public-facing profile fields.
3. **Persistent data pipeline**
   - Add a scheduled, idempotent nflverse ingestion job rather than treating
     upstream downloads as an application concern.
   - Store normalized schedules, weekly team statistics, standings inputs,
     rosters, and data-version metadata in a database.
   - Preserve historical weekly snapshots so rankings remain reproducible when
     upstream datasets change.
4. **Application caching**
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
3. Add the first user preference: favorite team or general NFL watcher.
4. Add a personalized layer that boosts games affecting the selected team's
   division, conference, and playoff position without changing general quality.
5. Add starter-only injury adjustments with position tiers and explicit
   availability confidence.
6. Replace approximate standings ordering with official NFL tiebreaker logic or
   a playoff-probability simulation.
7. Add opponent-adjusted efficiency and recent-form features after validating
   them against historical outcomes.
8. Add defensive-player spotlights and richer opponent-relative player context.

The complete scoring reference is available in
[ELOformula.md](ELOformula.md).
