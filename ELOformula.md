# Record Watchability Formula v1

The score is an absolute `0.00–1.00` index, not a probability. It uses only
pregame records and rivalry context. Despite this file's original "ELO" name,
the MVP does not calculate Elo ratings; that would add complexity beyond the
prototype's scope.

## Adjusted win rate

### Formula

```text
previousWinRate =
  (previousWins + 0.5 × previousTies) / previousGames

adjustedWinRate =
  (4 × previousWinRate + currentWins + 0.5 × currentTies)
  / (4 + currentGames)
```

### Meaning

The previous season provides a four-game prior so Week 1 has useful context.
Current-season results progressively take over as games are played. A tie
counts as half a win.

### How it is used

The service calculates this value immediately before the selected week. A team
is considered good only when `adjustedWinRate > 0.500`.

## Record quality

### Formula

```text
recordQuality =
  min(homeAdjustedWinRate, awayAdjustedWinRate)
  when both teams are good

recordQuality = 0 otherwise
```

### Meaning

The weaker good team controls the matchup's record value. Two equally bad
teams receive no record boost merely because they are evenly matched.

### How it is used

This is the primary watchability component. A matchup only receives it when
both teams clear the strict good-team threshold.

## Rivalry value

### Formula

Use the strongest applicable category without stacking:

| Category | Value |
| --- | ---: |
| Same division | `0.20` |
| Named conference/interconference rivalry | `0.12` |
| Historic/regional rivalry | `0.06` |
| None | `0.00` |

### Meaning

Rivalries create Week 1 value before current records exist. Divisional games
receive the largest boost because they carry recurring standings context.

### How it is used

The schedule's divisional flag is checked first. Otherwise, the service looks
for the team pair in the curated rivalry dataset. Only one boost applies.

## Final value

### Formula

```text
rawScore = recordQuality + (1 - recordQuality) × rivalryValue
displayScore = round(clamp(rawScore, 0, 1), 2)
```

### Meaning

The rivalry term fills some of the score not already supplied by record
quality. This saturation prevents two strong teams from receiving an
unbounded additive bonus.

### How it is used

Sorting uses the unrounded score, then record quality, rivalry value, kickoff,
and game ID. The `top` parameter is applied only after every game is scored and
sorted.

## Data boundary

A Week `W` score uses only completed regular-season games with `week < W`.
Target-week and future results are excluded even when the historical dataset
already contains them. Week 1 uses the final 2024 regular-season record.
