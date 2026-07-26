# Dynamic Watchability Formula v5

The API displays an absolute `1.00–10.00` watchability rating, not a win
probability. The formula first calculates a normalized `0.00–1.00` value using
two benchmarks:

```text
55% Pure Matchup Quality
45% Context and Standings Stakes
```

Despite this file's historical name, the prototype does not calculate Elo.

## Variables

| Variable | Meaning | Range |
| --- | --- | ---: |
| `W_i` | Pregame scoring win rate for team `i` | `0.00–1.00` |
| `O_i` | Points-scored percentile | `0.00–1.00` |
| `D_i` | Points-allowed defensive percentile | `0.00–1.00` |
| `P_i` | Point-differential percentile | `0.00–1.00` |
| `T_i` | Overall team strength | `0.00–1.00` |
| `C` | Expected competitive closeness | `0.00–1.00` |
| `Q` | Pure matchup quality | `0.00–1.00` |
| `R` | Rivalry value | `0.00–0.20` |
| `L` | Weekly standings leverage | `0.00–0.82` |
| `X` | Combined context and stakes | `0.00–1.00` |
| `N` | Unrounded normalized watchability | `0.00–1.00` |
| `S` | Displayed watchability score | `1.00–10.00` |

## 1. Pregame data boundary

A Week `K` calculation uses completed regular-season games satisfying:

```text
gameWeek < K
```

Target-week and future results are excluded even though the historical cache
contains them. This boundary applies to records, points scored, points allowed,
point differential, and standings.

## 2. Early-season prior

### Record formula

During Weeks 1–5:

```text
previousWinRate =
  (previousWins + 0.5 × previousTies) / previousGames

W_i =
  (4 × previousWinRate + currentWins + 0.5 × currentTies)
  / (4 + currentGames)
```

During Weeks 6–18:

```text
W_i =
  (currentWins + 0.5 × currentTies) / currentGames
```

### Scoring-rate formula

The same four-game prior applies independently to points scored and allowed:

```text
earlyPointsRate =
  (4 × previousSeasonRate + currentSeasonPoints)
  / (4 + currentGames)
```

From Week 6 onward, only current-season scoring is used.

### Meaning

The prior prevents Week 1 from treating every team as identical. It disappears
once the current season has enough evidence. The displayed API record is always
the actual current-season record, never an adjusted record.

## 3. League-relative scoring values

For every team, the backend calculates:

```text
pointsForPerGame
pointsAllowedPerGame
pointDifferentialPerGame =
  pointsForPerGame - pointsAllowedPerGame
```

Each value is converted into a weekly league percentile. Higher offense and
point differential are better; fewer points allowed is better.

For a value with tied teams:

```text
percentile =
  (numberOfWorseTeams + 0.5 × numberOfOtherTiedTeams)
  / (numberOfTeams - 1)
```

This makes the features relative to that week's league environment rather than
depending on arbitrary fixed scoring bands.

## 4. Team strength (`T_i`)

### Formula

```text
T_i = (W_i + O_i + D_i + P_i) / 4
```

### Meaning

Team strength gives equal, transparent weight to:

- results;
- offensive scoring;
- defensive scoring prevention;
- overall scoring margin.

### How it is used

An elite record alone is insufficient when the team's underlying scoring
profile is weak. Likewise, strong underlying statistics cannot completely
erase a poor record.

## 5. Offense-versus-defense projection

### Formula

```text
homeExpectedPoints =
  (homePointsForPerGame + awayPointsAllowedPerGame) / 2

awayExpectedPoints =
  (awayPointsForPerGame + homePointsAllowedPerGame) / 2
```

### Meaning

Each offense is evaluated against the opposing defense. This is a simple
matchup projection, not a betting line or predicted final score.

## 6. Competitive closeness (`C`)

### Formula

```text
C =
  1 - abs(homeExpectedPoints - awayExpectedPoints)
      / max(homeExpectedPoints, awayExpectedPoints, 1)
```

The result is clamped to `0.00–1.00`.

### Meaning

Similar expected scoring produces a value near `1.00`. A projected mismatch
reduces the value. Closeness alone cannot make two bad teams highly rated
because it is multiplied by their team quality next.

## 7. Pure matchup quality (`Q`)

### Formula

```text
pairStrength = sqrt(homeTeamStrength × awayTeamStrength)
Q = pairStrength × C
```

### Meaning

The geometric mean requires both teams to contribute meaningful strength. The
closeness multiplier then penalizes blowout risk.

### How it is used

`Q` supplies exactly `55%` of normalized watchability. This favors two strong,
compatible teams over an elite team facing a weak opponent. Two evenly matched
bad teams remain low because their `pairStrength` is low.

## 8. Rivalry value (`R`)

Only the strongest applicable category is used:

| Category | `R` |
| --- | ---: |
| Same division | `0.20` |
| Named conference/interconference rivalry | `0.12` |
| Historic/regional rivalry | `0.06` |
| None | `0.00` |

Categories do not stack. The nflverse divisional flag takes precedence over the
curated rivalry list.

## 9. Weekly standings leverage (`L`)

Standings are reconstructed before the selected week and ordered within each
division and conference by:

```text
win rate, then point differential, then team ID
```

This is a deterministic prototype approximation, not the NFL's complete
official tiebreaker procedure.

For each team, the model evaluates three objectives:

- division lead;
- seventh-place conference playoff cutoff;
- conference top seed.

For each objective:

```text
remainingGames = max(1, 17 - gamesPlayed)

proximity =
  max(0, 1 - min(|marginAfterWin|, |marginAfterLoss|) / remainingGames)

consequence =
  1.0  when the result crosses the boundary or creates a two-win swing
  0.5  otherwise

objectiveImpact = min(1, proximity × consequence)
```

Use the strongest objective for each team and combine both teams:

```text
impact = 1 - (1 - homeImpact) × (1 - awayImpact)
seasonMaturity = clamp((week - 1) / 17, 0, 1)
L = 0.82 × seasonMaturity × impact
```

The maturity term prevents early standings from looking as decisive as late
division and playoff races.

## 10. Context and stakes (`X`)

### Formula

```text
X = L + (1 - L) × R
```

### Meaning

Standings leverage is the primary context signal. Rivalry fills some of the
remaining context space without stacking beyond `1.00`.

### How it is used

`X` supplies exactly `45%` of normalized watchability. This is strong enough
for a competitive division-title game to overcome a modest pure-quality
disadvantage, but rivalry alone cannot make two poor teams an elite matchup.

## 11. Final score (`N` and `S`)

### Formula

```text
N = 0.55 × Q + 0.45 × X
S = round(1 + 9 × clamp(N, 0, 1), 2)
```

### Scale

| Normalized value | Displayed score |
| ---: | ---: |
| `0.00` | `1.00` |
| `0.25` | `3.25` |
| `0.50` | `5.50` |
| `0.75` | `7.75` |
| `1.00` | `10.00` |

The API returns a number rounded to two-decimal precision. A JSON consumer may
render `8.50` as `8.5`; a UI should format it to two places.

## 12. Ranking tiebreakers

Games are sorted using the following attributes:

```text
1. Unrounded normalized score
2. Context and stakes
3. Pure matchup quality
4. Competitive closeness
5. Record quality
6. Standings leverage
7. Rivalry value
8. Kickoff time
9. Game ID
```

Therefore, games with the same displayed score are still ordered using more
precise and football-relevant information.

## 13. Top and bottom selection

The API applies selection only after every matchup is scored and sorted:

```text
top=x     returns the x highest-rated games
bottom=x  returns the x lowest-rated games, worst first
```

The parameters are mutually exclusive. Omitting both returns the complete
slate in highest-to-lowest order.

## 14. Reasons, headlines, and injuries

The response may explain:

- winning records;
- rivalry or divisional status;
- standings implications;
- strong competitive quality;
- offense-defense closeness;
- one cached pregame headline.

Headlines have exactly zero numeric impact. Injuries are intentionally excluded
from v4 until starter status, availability timing, and replacement quality can
be modeled without double-counting information already reflected in team
performance.
