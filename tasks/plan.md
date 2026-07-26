# NFL Viewer Backend MVP Plan

Build a FastAPI-only service that ranks 2025 regular-season matchups using
pregame records and rivalry context. Swagger at `/docs` is the user interface.

## Slices

1. Scaffold the Python package, health route, and typed API contract.
2. Load and normalize 2024–2025 nflverse schedules and team metadata.
3. Calculate adjusted records and record/rivalry watchability scores.
4. Expose `GET /api/v1/rankings` with validated `season`, `week`, and `top`.
5. Verify Week 1, Week 4, top-result slicing, leakage prevention, and docs.

## Done when

- `season=2025&week=4&top=5` returns the top five of all Week 4 games.
- Omitting `top` returns the complete slate.
- Target-week and future results never affect scores.
- Tests, Ruff checks, runtime API checks, and documentation pass.

