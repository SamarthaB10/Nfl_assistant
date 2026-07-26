import pytest

from nflviewer.models import RecordSummary
from nflviewer.records import adjusted_win_rate, build_team_rating, scoring_win_rate, win_rate


def record(wins: int, losses: int, ties: int = 0) -> RecordSummary:
    return RecordSummary(wins=wins, losses=losses, ties=ties)


def test_win_rate_counts_ties_as_half_a_win() -> None:
    assert win_rate(record(8, 8, 1)) == pytest.approx(0.5)


def test_win_rate_defaults_to_neutral_when_no_games_exist() -> None:
    assert win_rate(record(0, 0)) == 0.5


def test_week_one_adjusted_rate_equals_previous_season_rate() -> None:
    previous = record(12, 5)

    assert adjusted_win_rate(previous, record(0, 0)) == pytest.approx(12 / 17)


def test_previous_season_acts_as_four_prior_games() -> None:
    previous = record(12, 5)
    current = record(0, 1)

    assert adjusted_win_rate(previous, current) == pytest.approx((4 * (12 / 17)) / 5)


def test_current_results_progressively_outweigh_previous_season() -> None:
    previous = record(12, 5)

    after_four_games = adjusted_win_rate(previous, record(0, 4))
    after_eight_games = adjusted_win_rate(previous, record(0, 8))

    assert after_eight_games < after_four_games


def test_week_five_uses_adjusted_win_rate() -> None:
    previous = record(12, 4)
    current = record(2, 2)

    assert scoring_win_rate(previous, current, week=5) == pytest.approx(0.625)


def test_week_six_uses_only_current_win_rate() -> None:
    previous = record(15, 2)
    current = record(2, 3)

    assert scoring_win_rate(previous, current, week=6) == pytest.approx(0.4)


def test_good_team_gate_uses_strictly_greater_than_half() -> None:
    rating = build_team_rating(
        team_id="DAL",
        team_name="Dallas Cowboys",
        logo_url=None,
        previous_record=record(8, 8),
        current_record=record(0, 0),
        week=1,
    )

    assert rating.scoring_win_rate == 0.5
    assert rating.is_good is False
