from dataclasses import dataclass
from math import sqrt

from nflviewer.data import TeamMetrics


@dataclass(frozen=True, slots=True)
class MatchupQuality:
    home_team_strength: float
    away_team_strength: float
    home_expected_points: float
    away_expected_points: float
    competitive_closeness: float
    value: float


def _clamp(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def team_strength(win_rate: float, metrics: TeamMetrics) -> float:
    """Combine record, scoring, defense, and point differential equally."""
    return _clamp(
        (
            win_rate
            + metrics.offense_percentile
            + metrics.defense_percentile
            + metrics.point_differential_percentile
        )
        / 4
    )


def calculate_matchup_quality(
    *,
    home_win_rate: float,
    away_win_rate: float,
    home_metrics: TeamMetrics,
    away_metrics: TeamMetrics,
) -> MatchupQuality:
    home_strength = team_strength(home_win_rate, home_metrics)
    away_strength = team_strength(away_win_rate, away_metrics)
    home_expected_points = (
        home_metrics.points_for_per_game + away_metrics.points_allowed_per_game
    ) / 2
    away_expected_points = (
        away_metrics.points_for_per_game + home_metrics.points_allowed_per_game
    ) / 2
    expected_ceiling = max(home_expected_points, away_expected_points, 1.0)
    competitive_closeness = _clamp(
        1 - abs(home_expected_points - away_expected_points) / expected_ceiling
    )
    pair_strength = sqrt(home_strength * away_strength)
    value = _clamp(pair_strength * competitive_closeness)

    return MatchupQuality(
        home_team_strength=home_strength,
        away_team_strength=away_strength,
        home_expected_points=home_expected_points,
        away_expected_points=away_expected_points,
        competitive_closeness=competitive_closeness,
        value=value,
    )
