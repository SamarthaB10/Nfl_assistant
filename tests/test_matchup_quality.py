import pytest

from nflviewer.data import TeamMetrics
from nflviewer.matchup_quality import calculate_matchup_quality, team_strength


def metrics(
    points_for: float,
    points_allowed: float,
    offense: float,
    defense: float,
    differential: float = 0.50,
) -> TeamMetrics:
    return TeamMetrics(
        points_for_per_game=points_for,
        points_allowed_per_game=points_allowed,
        offense_percentile=offense,
        defense_percentile=defense,
        point_differential_percentile=differential,
    )


def test_team_strength_equally_combines_record_offense_and_defense() -> None:
    result = team_strength(
        0.75,
        metrics(
            points_for=27,
            points_allowed=17,
            offense=0.80,
            defense=0.90,
            differential=0.85,
        ),
    )

    assert result == pytest.approx((0.75 + 0.80 + 0.90 + 0.85) / 4)


def test_compatible_strong_teams_produce_high_matchup_quality() -> None:
    result = calculate_matchup_quality(
        home_win_rate=0.80,
        away_win_rate=0.75,
        home_metrics=metrics(28, 18, 0.90, 0.80, 0.85),
        away_metrics=metrics(27, 17, 0.80, 0.90, 0.80),
    )

    assert result.home_expected_points == pytest.approx(22.5)
    assert result.away_expected_points == pytest.approx(22.5)
    assert result.competitive_closeness == 1
    assert result.value == pytest.approx(
        (result.home_team_strength * result.away_team_strength) ** 0.5
    )
    assert result.value > 0.80


def test_matchup_imbalance_penalizes_an_elite_team_against_a_weak_team() -> None:
    balanced = calculate_matchup_quality(
        home_win_rate=0.80,
        away_win_rate=0.75,
        home_metrics=metrics(28, 18, 0.90, 0.80),
        away_metrics=metrics(27, 17, 0.80, 0.90),
    )
    imbalanced = calculate_matchup_quality(
        home_win_rate=0.90,
        away_win_rate=0.30,
        home_metrics=metrics(30, 16, 1.00, 0.90),
        away_metrics=metrics(16, 30, 0.10, 0.10),
    )

    assert imbalanced.competitive_closeness < balanced.competitive_closeness
    assert imbalanced.value < balanced.value


def test_matchup_quality_weights_pair_strength_65_and_closeness_35() -> None:
    result = calculate_matchup_quality(
        home_win_rate=0.80,
        away_win_rate=0.70,
        home_metrics=metrics(30, 18, 0.90, 0.80, 0.85),
        away_metrics=metrics(21, 20, 0.65, 0.60, 0.60),
    )
    pair_strength = (result.home_team_strength * result.away_team_strength) ** 0.5

    assert result.competitive_closeness < 1
    assert result.value == pytest.approx(
        pair_strength * (0.65 + 0.35 * result.competitive_closeness)
    )


def test_evenly_matched_bad_teams_do_not_receive_high_quality() -> None:
    result = calculate_matchup_quality(
        home_win_rate=0.25,
        away_win_rate=0.25,
        home_metrics=metrics(15, 25, 0.20, 0.20),
        away_metrics=metrics(15, 25, 0.20, 0.20),
    )

    assert result.competitive_closeness == 1
    assert result.value < 0.30
