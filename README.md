# NFL Viewer

FastAPI backend that ranks 2025 NFL regular-season matchups by record quality
and rivalry context. Swagger UI is the MVP interface.

## Setup

```bash
cd /Users/samarthab/NFLviewer
uv sync
uv run python -m nflviewer.sync_data --force
uv run fastapi dev
```

Open <http://127.0.0.1:8000/docs>, expand `GET /api/v1/rankings`, and enter:

- `season`: `2025`
- `week`: an integer from `1` to `18`
- `top`: an optional integer from `1` to `16`; omit it for every game

For example, `week=4&top=5` returns the five highest-rated Week 4 games.

## Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

The scoring model is documented in [ELOformula.md](ELOformula.md).
