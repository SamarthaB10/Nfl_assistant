# Dynamic 55/45 Formula Tasks

- [x] Task 1: Add pregame team scoring metrics
  - Acceptance: points for/allowed and league-relative offense/defense values
    exclude the target and future weeks.
  - Verify: `uv run pytest tests/test_data.py -q`
  - Files: `src/nflviewer/data.py`, `tests/test_data.py`

- [x] Task 2: Calculate pure matchup quality
  - Acceptance: team strength, opposing offense-defense projections, and
    closeness produce a bounded matchup-quality value.
  - Verify: `uv run pytest tests/test_matchup_quality.py -q`
  - Files: `src/nflviewer/matchup_quality.py`,
    `tests/test_matchup_quality.py`

- [x] Task 3: Integrate the 55/45 scoring formula
  - Acceptance: final normalized score is exactly `55%` matchup quality and
    `45%` context; raw sorting remains deterministic.
  - Verify: `uv run pytest tests/test_ranking.py tests/test_api.py -q`
  - Files: `src/nflviewer/ranking.py`, `src/nflviewer/models.py`,
    `src/nflviewer/app.py`, ranking/API tests

- [x] Task 4: Document and verify formula v4
  - Acceptance: docs contain every variable and live Week 2025 output uses the
    new formula.
  - Verify: full pytest, Ruff, formatting, and live HTTP request
  - Files: `ELOformula.md`, `README.md`, health test
