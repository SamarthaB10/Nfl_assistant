# Dynamic Matchup Headlines

## Problem Statement

Drizzle needs to publish a stable weekly watchability rating while keeping the headline beneath each matchup current as the week develops. A Wednesday ranking should remain reproducible, but the article shown for a Seahawks–Rams game should be able to move from a preview to an injury update and finally to a postgame recap.

The standalone LIVE NEWS page serves broad NFL coverage. Matchup cards need a narrower, game-specific editorial stream with one primary headline and an expandable list of other relevant articles.

## Recommended Direction

Use immutable weekly ranking snapshots plus a dynamic matchup-news layer.

- Calculate and publish the upcoming week’s rankings on Wednesday.
- Keep the score, rank, records, and scoring reasons fixed for that snapshot.
- Ingest ESPN, CBS Sports, and FOX Sports articles independently from ranking calculation.
- Attach matchup-specific articles to exactly one scheduled game through a nullable `game_key` foreign key.
- Prefer ESPN for the primary matchup headline; fall back to CBS Sports, then FOX Sports when ESPN has no suitable article.
- Expose one primary headline on the matchup card and provide a cursor-paginated “View more” list of other relevant articles.
- Change the eligible article phase from pregame to postgame when the game becomes final.

This preserves the meaning of the rating while allowing the editorial context around a matchup to evolve.

## Product Contract

For each matchup, the UI shows:

1. One current primary headline.
2. A `View more` control below it.
3. An expandable list of additional matchup-specific articles.

Publisher priority for selecting the primary headline is:

```text
ESPN → CBS Sports → FOX Sports
```

The “View more” list may contain articles from all three publishers, ordered by phase, relevance, publisher priority, and publication time.

General LIVE NEWS articles have `game_key = NULL`. Matchup articles have exactly one `game_key`.

## Data Model Changes

### `games`

Create a canonical schedule table so every other record can refer to a stable matchup.

```text
game_key       primary key or unique immutable key
season
week
away_team
home_team
kickoff_at
status         scheduled | live | final
completed_at
created_at
updated_at
```

`game_key` should use the existing stable format, such as `2025_08_SEA_LAR`. The key must be unique and must not change when article data is refreshed.

### `ranking_snapshots`

Store the Wednesday calculation as an immutable versioned result.

```text
id             primary key
season
week
calculated_at
formula_version
data_version
published_at
status         draft | published | superseded
```

Add a unique constraint for the active published snapshot per season and week.

### `game_rankings`

Store the matchup-level result belonging to a snapshot.

```text
snapshot_id    foreign key → ranking_snapshots.id
game_key       foreign key → games.game_key
rank
score
reasons        structured JSON or normalized reason rows
records        structured JSON or normalized team records
```

Use `(snapshot_id, game_key)` as the primary key and index `game_key` for matchup detail lookups.

### `news_articles`

Extend the existing table with matchup metadata.

```text
game_key       nullable foreign key → games.game_key
phase          pregame | postgame | general
relevance_score
```

Existing article identity and metadata remain unchanged:

```text
source
source_article_id
title
author
excerpt
canonical_url
image_url
team_codes
published_at
fetched_at
updated_at
```

`game_key` is nullable because general LIVE NEWS stories are not about one specific game. A non-null `game_key` means the article is assigned to exactly one matchup.

Recommended indexes:

```text
(game_key, phase, published_at DESC, id DESC)
(source, game_key, published_at DESC, id DESC)
GIN(team_codes)
```

### `game_headline_state`

Store the current primary-selection state separately from the article itself.

```text
game_key             primary key and foreign key → games.game_key
phase                pregame | postgame
primary_article_id   foreign key → news_articles.id
last_refreshed_at
next_refresh_at
selection_version
updated_at
```

This makes scheduled refreshes explicit and allows the system to explain which article was selected without changing article metadata.

The “View more” list is derived from `news_articles` rather than stored as a separate list.

## Extraction and Matching Pipeline

### 1. Schedule synchronization

Before the weekly ranking job, synchronize the upcoming schedule into `games`. The schedule is the authority for valid team pairings, kickoff times, game status, and canonical game IDs.

### 2. Feed ingestion

Fetch ESPN, CBS Sports, and FOX Sports feeds hourly. Ingestion should be idempotent using `(source, source_article_id)` and canonical URL uniqueness.

Feed ingestion and primary-headline selection are separate operations. Articles should be stored as soon as they are discovered even if they are not selected as the primary headline.

### 3. Article normalization

Normalize:

- Publisher name
- Team aliases and abbreviations
- Publication time to UTC
- Article type and phase
- Canonical URL
- Author and excerpt metadata

### 4. Game matching

Assign `game_key` only when exactly one matchup is identified. Matching evidence should combine:

- Both teams appearing in normalized metadata or title/excerpt
- Team aliases and abbreviations
- Kickoff proximity
- Article title relevance
- Publisher metadata when available

Do not attach an article to a matchup based on one team mention alone. A low-confidence article remains a general LIVE NEWS item until it can be matched safely.

### 5. Phase assignment

```text
Before kickoff       → pregame
Game in progress     → live handling or pregame exclusion
Game is final        → postgame
Unrelated NFL story  → general
```

For the initial design, only `pregame` and `postgame` are displayed under matchup cards. Live-game handling can be added once live scores and in-game data are part of the product.

## Primary Headline Selection

When a game is due for refresh, select the best eligible article using this order:

1. Exact `game_key` match.
2. Correct phase for the game’s current lifecycle.
3. Higher relevance score.
4. Publisher priority: ESPN, CBS Sports, FOX Sports.
5. Newer `published_at`.
6. Newer article ID as a deterministic tie-breaker.

If no new article passes the matching threshold, preserve the previous valid primary article rather than attaching an unrelated story.

The selected article ID is written to `game_headline_state.primary_article_id`. Other eligible articles remain available through `View more`.

## Weekly and Headline Lifecycle

### Wednesday

1. Synchronize the upcoming schedule and data inputs.
2. Calculate the weekly matchup scores.
3. Create and publish one `ranking_snapshots` row.
4. Create `game_rankings` rows for every matchup.
5. Initialize `game_headline_state` for the week.
6. Select the first available pregame headline for each game.

### Wednesday through Friday

- Continue hourly feed ingestion.
- Refresh each game’s primary headline every 48 hours.
- Keep the ranking snapshot unchanged.

### Saturday and game day

Increase refresh frequency near kickoff, for example every 12 hours on Saturday and every 1–2 hours on game day. The exact interval should be configuration, not hard-coded into article rows.

### After the final whistle

1. Update the game status to `final`.
2. Change headline state to `postgame`.
3. Search for an ESPN recap first.
4. Fall back to CBS Sports or FOX Sports if ESPN has not published a suitable recap.
5. Keep pregame articles in the “View more” history.

The target is for a newly published relevant article to become visible under the correct matchup within two hours during normal feed availability.

## Operational Design

### Workers

Use separate idempotent jobs conceptually, even if they initially run in one FastAPI process:

- `schedule_sync`
- `ranking_publish`
- `feed_ingest`
- `game_article_match`
- `headline_select`
- `game_status_sync`
- `news_retention`

PostgreSQL advisory locks should prevent two workers from processing the same refresh simultaneously.

### Retention

Retain one year of articles using `published_at`. Keep matchup associations and headline-selection state for the same retention window unless historical matchup pages require longer retention.

### Idempotency

Every job should be safe to retry. Use unique source identifiers, upserts, immutable ranking snapshot IDs, and deterministic headline selection.

### Caching

Redis is not required for the first version of this foundation. PostgreSQL stores the durable state, and the weekly ranking snapshot is inexpensive to read. Add Redis later for:

- Hot weekly ranking responses
- Frequently opened matchup headline lists
- Shared cache state across multiple API instances

## Migration Sequence

1. Add `games` and import the known schedule.
2. Add `ranking_snapshots` and `game_rankings`.
3. Add nullable `game_key`, `phase`, and `relevance_score` to `news_articles`.
4. Add matchup-specific indexes.
5. Add `game_headline_state`.
6. Backfill historical matchup articles only when a deterministic game match exists.
7. Add feed matching and primary-selection workers.
8. Add matchup API fields for `primaryHeadline` and paginated `relatedArticles`.
9. Add the matchup “View more” UI.
10. Enable postgame article selection after game status synchronization is reliable.

## API Shape

The matchup response should keep ranking and news separate:

```json
{
  "gameKey": "2025_08_SEA_LAR",
  "score": 8.4,
  "primaryHeadline": {
    "title": "...",
    "source": "ESPN",
    "phase": "pregame",
    "publishedAt": "...",
    "url": "..."
  },
  "relatedArticlesCursor": "..."
}
```

The “View more” request should be independently paginated:

```text
GET /api/v1/games/{gameKey}/articles?phase=pregame&limit=5&cursor=...
```

This prevents the headline list from changing the ranking calculation or requiring the entire article history in the initial matchup response.

## Assumptions to Validate

- [ ] ESPN, CBS Sports, and FOX feeds provide enough title, excerpt, or team metadata to identify matchup-specific articles reliably.
- [ ] A two-hour article freshness target is acceptable for the user experience.
- [ ] One article-to-one-game assignment remains a permanent product rule.
- [ ] ESPN-first selection is preferable to purely recency-based selection.
- [ ] Preserving the last valid headline is better than showing an unrelated fallback.
- [ ] Postgame recap availability is best handled by polling after the game becomes final.

## MVP Scope

The first implementation of this foundation should include:

- Persistent `games` records
- Immutable weekly ranking snapshots
- Direct matchup assignment through nullable `news_articles.game_key`
- Pregame/postgame phase metadata
- Primary headline state and refresh timestamps
- ESPN/CBS/FOX priority selection
- Cursor-paginated related articles
- Hourly feed ingestion and deterministic matching

## Not Doing Yet

- No Redis requirement
- No live in-game article experience
- No article summarization or LLM-generated headlines
- No automatic “best article” semantic model beyond deterministic relevance rules
- No multi-game article associations
- No social voting to select the primary article
- No recalculation of watchability scores when a headline changes
- No full event-stream platform or message broker

## Definition of Done for the Foundation

- Every scheduled matchup has a stable `game_key`.
- A Wednesday ranking can be reproduced from a versioned snapshot.
- General news remains available without a matchup association.
- A matchup card can retrieve one primary article and a paginated article list.
- ESPN is selected first when a relevant ESPN article exists.
- CBS Sports or FOX Sports is selected when ESPN is unavailable.
- A game’s primary article changes without changing its ranking score.
- Postgame selection begins after the game status becomes final.
- Feed retries do not create duplicate articles or duplicate headline assignments.
