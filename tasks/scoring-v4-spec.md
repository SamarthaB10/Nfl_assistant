# Spec: Dynamic 55/45 Watchability Formula

## Objective

Rank 2025 NFL regular-season games on a `1.00–5.00` scale using two
interpretable benchmarks:

- `55%` pure matchup quality;
- `45%` context and standings stakes.

The score should favor strong, competitively matched teams while allowing a
meaningful division or playoff game to outrank a slightly stronger ordinary
matchup.

## Formula

All inputs are calculated before the selected week.

```text
teamStrength =
  mean(scoringWinRate, offensePercentile, defensePercentile)

homeExpectedPoints =
  mean(homePointsForPerGame, awayPointsAllowedPerGame)

awayExpectedPoints =
  mean(awayPointsForPerGame, homePointsAllowedPerGame)

competitiveCloseness =
  1 - abs(homeExpectedPoints - awayExpectedPoints)
      / max(homeExpectedPoints, awayExpectedPoints, 1)

pairStrength = sqrt(homeTeamStrength × awayTeamStrength)
matchupQuality = pairStrength × competitiveCloseness

context =
  standingsLeverage + (1 - standingsLeverage) × rivalryValue

normalizedScore = 0.55 × matchupQuality + 0.45 × context
displayScore = round(1 + 4 × normalizedScore, 2)
```

Offense percentile ranks points scored per game from worst to best. Defense
percentile ranks points allowed per game from worst to best, so allowing fewer
points is better. Equal values receive equal percentile values.

Weeks 1–5 use a four-game prior from 2024 for both records and scoring rates.
Weeks 6–18 use only 2025 games.

## Tech Stack and Structure

- Python 3.12, FastAPI, Pydantic, Polars, pytest, Ruff.
- Data aggregation: `src/nflviewer/data.py`.
- Matchup-quality calculation: `src/nflviewer/matchup_quality.py`.
- Final composition: `src/nflviewer/ranking.py`.
- Unit and API tests: `tests/`.

## Commands

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run fastapi dev --host 127.0.0.1 --port 8000
```

## Code Style

Use typed, pure functions for scoring logic:

```python
def matchup_quality(
    home_win_rate: float,
    away_win_rate: float,
    home_metrics: TeamMetrics,
    away_metrics: TeamMetrics,
) -> MatchupQuality:
    ...
```

## Testing Strategy

- Unit-test preweek metric aggregation and future-data exclusion.
- Unit-test strength, expected closeness, and the `55/45` composition.
- Prove a competitively matched stronger game beats an ordinary mismatch.
- Prove standings leverage can lift a reasonably competitive divisional game.
- Verify the compact API response remains unchanged except for score values and
  formula-generated reasons.

## Boundaries

- Always: use pregame data only; keep the public score between `1.00` and
  `5.00`; sort using the unrounded normalized score.
- Ask first: add dependencies, change the API response shape, or change the
  user-approved `55/45` split.
- Never: use future results, Vegas lines, headlines as numeric inputs, or
  injury data in this version.

## Success Criteria

- Both-team record, offense, defense, point differential, and expected
  closeness influence matchup quality.
- Rivalry and standings leverage make up exactly `45%` of the normalized score.
- Two evenly matched bad teams do not become highly rated.
- A high-stakes divisional matchup can overcome a modest quality disadvantage.
- Tests, Ruff checks, and a live Week 2025 API request pass.

## Open Questions

None. Injury-adjusted availability and recent-form weighting remain future
work.
