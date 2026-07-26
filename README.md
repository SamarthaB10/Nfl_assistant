# NFL Viewer

FastAPI backend that ranks 2025 NFL regular-season matchups using `55%` pure
matchup quality and `45%` context and standings stakes. Relevant historical
ESPN headlines are included as explanatory context. Swagger UI is the MVP
interface.

## Setup

```bash
cd /Users/samarthab/NFLviewer
uv sync
uv run python -m nflviewer.sync_data --force
uv run python -m nflviewer.sync_headlines
uv run fastapi dev
```

The repository includes a validated 2025 headline cache, so running
`sync_headlines` is optional. Use it only to rebuild that cache.

Open <http://127.0.0.1:8000/docs>, expand `GET /api/v1/rankings`, and enter:

- `season`: `2025`
- `week`: an integer from `1` to `18`
- `top`: optionally return the highest-rated `1` to `16` games
- `bottom`: optionally return the lowest-rated `1` to `16` games, worst first

For example, `week=4&top=5` returns the five highest-rated Week 4 games.
`week=4&bottom=5` returns the five lowest-rated games. `top` and `bottom`
cannot be used together; omit both to return the complete slate.
The response contains only the information needed to display each game:

```json
[
  {
    "matchup": "Seattle Seahawks vs San Francisco 49ers",
    "records": {
      "SEA": "13-3",
      "SF": "12-4"
    },
    "score": 8.06,
    "reasons": [
      "Both teams have winning records",
      "Divisional matchup",
      "Direct division race matchup",
      "Strong, competitive team matchup",
      "Headline: 49ers host the Seahawks in the season finale with the division title and top NFC seed on the line"
    ]
  }
]
```

Scores use only information available before the selected game's week.
Headlines are display-only reasons: they never change a score or ranking.
The API reads both nflverse data and the headline JSON from local cache, so a
ranking request does not call an external service.

The watchability score uses a `1.00–10.00` scale and is rounded to two decimal
places. A `1.00` game has no scoring boost; a `10.00` game reaches the model's
maximum possible value.

Pure matchup quality combines both teams' pregame records, offense percentile,
defense percentile, point-differential percentile, and expected
offense-versus-defense closeness. Context combines rivalry value with pregame
division, playoff-cutoff, and top-seed leverage. Injuries are not part of v5.

## Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

The scoring model is documented in [ELOformula.md](ELOformula.md).
