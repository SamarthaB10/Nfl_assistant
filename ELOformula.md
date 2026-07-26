# Standings Watchability Formula v3

The displayed score is an absolute `1.00–5.00` watchability rating, not a
probability. The formula calculates a normalized value internally and converts
it to the five-point scale at the end. It uses only information available
before the selected week. Despite this file's original "ELO" name, the MVP
does not calculate Elo ratings.

## Variables

| Variable | Meaning | Range |
| --- | --- | ---: |
| `Q` | Record quality of two good teams | `0.00–1.00` |
| `R` | Strongest rivalry value | `0.00–0.20` |
| `B` | Base value after record and rivalry saturation | `0.00–1.00` |
| `I` | Estimated impact on a standings objective | `0.00–1.00` |
| `M` | Season maturity | `0.00–1.00` |
| `L` | Weekly standings leverage | `0.00–0.82` |
| `N` | Normalized final value used for sorting | `0.00–1.00` |
| `S` | Displayed watchability score | `1.00–5.00` |

## 1. Team scoring win rate

### Formula

For Weeks 1–5:

```text
previousWinRate =
  (previousWins + 0.5 × previousTies) / previousGames

teamWinRate =
  (4 × previousWinRate + currentWins + 0.5 × currentTies)
  / (4 + currentGames)
```

For Weeks 6–18:

```text
teamWinRate =
  (currentWins + 0.5 × currentTies) / currentGames
```

### Meaning

The previous season acts as a four-game prior while the current season has
little evidence. From Week 6 onward, only the current season is used. A tie
counts as half a win.

### How it is used

A team is good when its active `teamWinRate` is strictly greater than `0.500`.
The API displays the real current-season record, never the adjusted value.

## 2. Record quality (`Q`)

### Formula

```text
Q = min(homeTeamWinRate, awayTeamWinRate)  when both teams are good
Q = 0                                      otherwise
```

### Meaning

The weaker good team controls the matchup's record value. Two evenly matched
bad teams receive no record-quality boost.

### How it is used

This gives games such as `10-2 vs 11-1` substantial value while keeping
`2-6 vs 2-6` at zero unless another factor makes the game important.

## 3. Rivalry value (`R`)

### Formula

Use only the strongest applicable category:

| Category | `R` |
| --- | ---: |
| Same division | `0.20` |
| Named conference/interconference rivalry | `0.12` |
| Historic/regional rivalry | `0.06` |
| None | `0.00` |

### Meaning

Rivalries create value before reliable current-season records exist.
Divisional games receive the largest amount because they also recur in the
standings race.

### How it is used

The nflverse divisional flag is checked first. Otherwise, the service checks
the curated rivalry file. Categories do not stack.

## 4. Base value (`B`)

### Formula

```text
B = Q + (1 - Q) × R
```

### Meaning

Rivalry value fills some of the space not already supplied by record quality,
instead of acting as an unbounded additive bonus.

### How it is used

This is the complete Week 1 formula. Weekly standings leverage begins in
Week 2 and grows as playoff consequences become clearer.

## 5. Pregame weekly standings

### Formula

For a requested Week `W`, standings use only completed 2025 regular-season
games where:

```text
gameWeek < W
```

Teams are ordered within their division and conference by:

```text
win rate, then point differential, then team ID
```

### Meaning

The standings are a deterministic MVP approximation of the table immediately
before the selected week. Point differential is a stable tie fallback; the
prototype does not reproduce the NFL's complete multi-step tiebreaker rules.

### How it is used

Each team is compared with the boundary team for three objectives:

- division lead;
- seventh-place conference playoff cutoff;
- conference top seed.

The model evaluates how the team's margin relative to that boundary differs
between a win and a loss. Direct games against the boundary team receive the
largest possible swing.

## 6. Standings leverage (`L`)

### Formula

For each team and objective:

```text
remainingGames = max(1, 17 - gamesPlayed)

proximity =
  max(0, 1 - min(|marginAfterWin|, |marginAfterLoss|) / remainingGames)

consequence =
  1.0  when the result crosses the boundary or creates a two-win swing
  0.5  otherwise

objectiveImpact = min(1, proximity × consequence)
```

Use the strongest objective for each team, then combine both teams:

```text
I = 1 - (1 - homeImpact) × (1 - awayImpact)
M = clamp((week - 1) / 17, 0, 1)
L = 0.82 × M × I
```

### Meaning

`I` increases when the result can move either team across a meaningful
standings boundary. `M` prevents early-season standings from looking as
decisive as late-season races. The `0.82` ceiling preserves room for the base
game quality and keeps the result bounded.

### How it is used

The strongest applicable reason is displayed as division race, playoff cutoff,
or conference top-seed implications. A direct late-season division race can
meaningfully lift an otherwise ordinary game.

## 7. Final score (`N` and `S`)

### Formula

```text
N = B + (1 - B) × L
S = round(1 + 4 × clamp(N, 0, 1), 2)
```

### Meaning

Standings leverage fills some of the score not already supplied by team
quality and rivalry. The linear conversion maps normalized `0.00` to displayed
`1.00` and normalized `1.00` to displayed `5.00`:

| Normalized value | Displayed score |
| ---: | ---: |
| `0.00` | `1.00` |
| `0.25` | `2.00` |
| `0.50` | `3.00` |
| `0.75` | `4.00` |
| `1.00` | `5.00` |

### How it is used

The displayed score is rounded to two decimal places. Sorting continues to use
the unrounded normalized value, so changing the display scale does not change
the matchup order. Ties are resolved by record quality, leverage, rivalry,
kickoff, and game ID. `top` is applied only after every game is scored.

## 8. Headline reasons

### Formula

```text
headlineScoreImpact = 0
```

### Meaning

A relevant ESPN pregame headline explains the narrative around a game but is
not reliable enough to change the numeric MVP score.

### How it is used

The checked-in cache contains at most one headline per game. A headline must:

- be published during the 14 days before kickoff;
- mention both teams;
- link to ESPN's NFL coverage;
- not be betting, odds, picks, or prediction content.

The API appends it as `Headline: …`. Missing headlines are neutral. Ranking
requests never call ESPN.

## Data boundary

Target-week and future results are excluded even though the historical dataset
contains them. Week 1 uses the final 2024 regular-season record. No Vegas line,
future result, or postgame headline is part of the score.
