# Implementation Plan: Dynamic 55/45 Watchability Formula

## Overview

Replace the record-first composition with the approved `55%` matchup-quality
and `45%` context formula while preserving the compact API response and
pregame-only data boundary.

## Architecture Decisions

- Derive scoring metrics from the existing nflverse schedule cache; add no
  dependency or network request.
- Put pure matchup math in `matchup_quality.py` and keep weekly aggregation in
  `data.py`.
- Preserve normalized raw values for sorting and convert only the displayed
  score to `1.00–5.00`.

## Task List

### Phase 1: Pregame quality foundation

- [x] Add leakage-safe weekly offense and defense metrics.
- [x] Add pure team-strength and matchup-closeness calculations.

### Checkpoint: Quality

- [x] Focused data and matchup-quality tests pass.
- [x] Commit the working quality slice.

### Phase 2: Formula integration

- [x] Compose `55%` matchup quality and `45%` context in rankings.
- [x] Add meaningful quality reasons without changing the response shape.
- [x] Update formula version and expected API scores.

### Checkpoint: Integration

- [x] Ranking and API tests pass.
- [x] Commit the formula integration slice.

### Phase 3: Documentation and runtime

- [x] Update `ELOformula.md` and `README.md`.
- [x] Run the full test, lint, formatting, and live API checks.
- [ ] Push the feature branch.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Future results leak into metrics | High | Filter every aggregate to `week < selectedWeek` and test it |
| Early weeks have no sample | High | Reuse the existing four-game 2024 prior through Week 5 |
| Similar displayed scores hide ordering | Medium | Sort on unrounded normalized values |
| Correlated team inputs overstate strength | Medium | Use a transparent equal-weight team benchmark and document it |

## Open Questions

None.
