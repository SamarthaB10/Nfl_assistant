from datetime import UTC, datetime

import pytest

from nflviewer.data import TeamMetrics
from nflviewer.matchup_quality import calculate_matchup_quality
from nflviewer.models import RecordSummary
from nflviewer.ranking import MatchupInput, rank_matchups, score_matchup
from nflviewer.standings import TeamStanding


def record(wins: int, losses: int, ties: int = 0) -> RecordSummary:
    return RecordSummary(wins=wins, losses=losses, ties=ties)


def matchup(
    game_id: str,
    home: str,
    away: str,
    *,
    week: int = 1,
    kickoff_hour: int = 18,
    is_divisional: bool = False,
) -> MatchupInput:
    return MatchupInput(
        game_id=game_id,
        week=week,
        kickoff=datetime(2025, 9, 7, kickoff_hour, tzinfo=UTC),
        home_team_id=home,
        home_team_name=home,
        home_logo_url=None,
        away_team_id=away,
        away_team_name=away,
        away_logo_url=None,
        is_divisional=is_divisional,
    )


def performance(
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


def test_final_score_uses_55_percent_quality_and_45_percent_context() -> None:
    game = matchup("weighted", "A", "B", week=9, is_divisional=True)
    previous = {"A": record(8, 8), "B": record(8, 8)}
    current = {"A": record(7, 1), "B": record(6, 2)}
    team_metrics = {
        "A": performance(28, 17, 0.90, 0.85),
        "B": performance(27, 18, 0.85, 0.80),
    }
    quality = calculate_matchup_quality(
        home_win_rate=7 / 8,
        away_win_rate=6 / 8,
        home_metrics=team_metrics["A"],
        away_metrics=team_metrics["B"],
    ).value

    result = score_matchup(
        game,
        previous,
        current,
        team_metrics=team_metrics,
    )

    expected_context = 0.20
    expected_raw = 0.55 * quality + 0.45 * expected_context
    assert result.breakdown.matchup_quality == pytest.approx(quality)
    assert result.breakdown.context_value == expected_context
    assert result.breakdown.raw_score == pytest.approx(expected_raw)
    assert result.watchability_score == round(1 + 9 * expected_raw, 2)


def test_two_bad_teams_receive_low_quality_even_when_evenly_matched() -> None:
    game = matchup("bad", "CAR", "TEN", week=9)
    previous = {"CAR": record(8, 8), "TEN": record(8, 8)}
    current = {"CAR": record(2, 6), "TEN": record(2, 6)}
    team_metrics = {
        "CAR": performance(14, 27, 0.10, 0.10, 0.10),
        "TEN": performance(14, 27, 0.10, 0.10, 0.10),
    }

    result = score_matchup(game, previous, current, team_metrics=team_metrics)

    assert result.breakdown.record_quality == 0
    assert result.breakdown.competitive_closeness == 1
    assert result.watchability_score == 1.68


def test_bad_divisional_matchup_only_receives_rivalry_value() -> None:
    game = matchup("bad-division", "NE", "BUF", week=9, is_divisional=True)
    previous = {"NE": record(8, 8), "BUF": record(8, 8)}
    current = {"NE": record(2, 6), "BUF": record(2, 6)}
    team_metrics = {
        "NE": performance(14, 27, 0.10, 0.10, 0.10),
        "BUF": performance(14, 27, 0.10, 0.10, 0.10),
    }

    result = score_matchup(game, previous, current, team_metrics=team_metrics)

    assert result.breakdown.record_quality == 0
    assert result.breakdown.context_value == 0.20
    assert result.watchability_score == 2.49


def test_two_good_teams_use_weaker_current_record_after_week_five() -> None:
    game = matchup("good", "A", "B", week=9)
    previous = {"A": record(8, 8), "B": record(8, 8)}
    current = {"A": record(5, 3), "B": record(6, 2)}
    team_metrics = {
        "A": performance(24, 20, 0.65, 0.60, 0.65),
        "B": performance(26, 18, 0.75, 0.70, 0.75),
    }

    result = score_matchup(game, previous, current, team_metrics=team_metrics)

    assert result.breakdown.record_quality == pytest.approx(5 / 8)
    assert result.breakdown.matchup_quality > 0.60
    assert result.reasons == [
        "Both teams have winning records",
        "Offense-defense profiles project a close game",
    ]


def test_divisional_value_saturates_instead_of_adding_directly() -> None:
    game = matchup("good-division", "A", "B", week=9, is_divisional=True)
    previous = {"A": record(8, 8), "B": record(8, 8)}
    current = {"A": record(5, 3), "B": record(6, 2)}
    team_metrics = {
        "A": performance(24, 20, 0.65, 0.60, 0.65),
        "B": performance(26, 18, 0.75, 0.70, 0.75),
    }

    result = score_matchup(game, previous, current, team_metrics=team_metrics)

    expected_raw = 0.55 * result.breakdown.matchup_quality + 0.45 * 0.20
    assert result.breakdown.raw_score == pytest.approx(expected_raw)
    assert result.watchability_score == round(1 + 9 * expected_raw, 2)
    assert result.reasons == [
        "Both teams have winning records",
        "Divisional matchup",
        "Offense-defense profiles project a close game",
    ]


def test_elite_records_score_above_moderate_winning_records() -> None:
    moderate = matchup("moderate", "A", "B", week=13)
    elite = matchup("elite", "C", "D", week=13)
    previous = {
        "A": record(8, 8),
        "B": record(8, 8),
        "C": record(8, 8),
        "D": record(8, 8),
    }
    current = {
        "A": record(5, 3),
        "B": record(6, 2),
        "C": record(10, 2),
        "D": record(11, 1),
    }

    moderate_score = score_matchup(moderate, previous, current).watchability_score
    elite_score = score_matchup(elite, previous, current).watchability_score

    assert elite_score > moderate_score


def test_week_eighteen_ignores_previous_season_strength() -> None:
    game = matchup(
        "2025_18_BAL_PIT",
        "PIT",
        "BAL",
        week=18,
        is_divisional=True,
    )
    previous = {"BAL": record(12, 5), "PIT": record(10, 7)}
    current = {"BAL": record(8, 8), "PIT": record(9, 7)}
    team_metrics = {
        "BAL": performance(21, 21, 0.50, 0.50),
        "PIT": performance(22, 20, 0.55, 0.55),
    }

    result = score_matchup(game, previous, current, team_metrics=team_metrics)
    weaker_previous = {"BAL": record(3, 14), "PIT": record(4, 13)}
    comparison = score_matchup(
        game,
        weaker_previous,
        current,
        team_metrics=team_metrics,
    )

    assert result.breakdown.record_quality == 0
    assert result.watchability_score == comparison.watchability_score


def test_week_eighteen_division_title_context_raises_watchability() -> None:
    game = matchup(
        "2025_18_BAL_PIT",
        "PIT",
        "BAL",
        week=18,
        is_divisional=True,
    )
    previous = {"BAL": record(12, 5), "PIT": record(10, 7)}
    current = {"BAL": record(8, 8), "PIT": record(9, 7)}
    team_metrics = {
        "BAL": performance(21, 21, 0.50, 0.50),
        "PIT": performance(22, 20, 0.55, 0.55),
    }
    standings = {
        "BAL": TeamStanding(
            team_id="BAL",
            conference="AFC",
            division="AFC North",
            record=current["BAL"],
            point_differential=10,
            conference_rank=7,
            division_rank=2,
        ),
        "PIT": TeamStanding(
            team_id="PIT",
            conference="AFC",
            division="AFC North",
            record=current["PIT"],
            point_differential=20,
            conference_rank=5,
            division_rank=1,
        ),
    }

    result = score_matchup(
        game,
        previous,
        current,
        standings=standings,
        team_metrics=team_metrics,
    )
    without_standings = score_matchup(
        game,
        previous,
        current,
        team_metrics=team_metrics,
    )

    assert result.watchability_score > without_standings.watchability_score
    assert "Direct division race matchup" in result.reasons


def test_high_stakes_divisional_game_can_overcome_modest_quality_gap() -> None:
    ordinary = matchup("ordinary", "A", "B", week=18)
    high_stakes = matchup("stakes", "C", "D", week=18, is_divisional=True)
    previous = {team: record(8, 8) for team in ("A", "B", "C", "D")}
    current = {
        "A": record(12, 4),
        "B": record(11, 5),
        "C": record(9, 7),
        "D": record(8, 8),
    }
    team_metrics = {
        "A": performance(28, 18, 0.90, 0.85),
        "B": performance(27, 19, 0.85, 0.80),
        "C": performance(23, 21, 0.60, 0.55),
        "D": performance(22, 22, 0.55, 0.50),
    }
    standings = {
        "C": TeamStanding("C", "AFC", "AFC North", current["C"], 12, 5, 1),
        "D": TeamStanding("D", "AFC", "AFC North", current["D"], 2, 7, 2),
    }

    ranked = rank_matchups(
        [ordinary, high_stakes],
        previous,
        current,
        standings=standings,
        team_metrics=team_metrics,
    )

    assert ranked[0].game_id == "stakes"


def test_ranking_uses_raw_score_and_applies_top_after_sorting() -> None:
    games = [
        matchup("low", "CAR", "TEN", kickoff_hour=17),
        matchup("high", "BUF", "KC", kickoff_hour=20),
        matchup("middle", "A", "B", kickoff_hour=19),
    ]
    previous = {
        "CAR": record(8, 8),
        "TEN": record(8, 8),
        "BUF": record(13, 3),
        "KC": record(14, 2),
        "A": record(10, 6),
        "B": record(10, 6),
    }
    current = {team: record(0, 0) for team in previous}

    full = rank_matchups(games, previous, current)
    top_two = rank_matchups(games, previous, current, top=2)

    assert [game.game_id for game in full] == ["high", "middle", "low"]
    assert [game.game_id for game in top_two] == ["high", "middle"]
    assert [game.rank for game in top_two] == [1, 2]


def test_bottom_returns_lowest_scored_games_worst_first() -> None:
    games = [
        matchup("low", "CAR", "TEN", kickoff_hour=17),
        matchup("high", "BUF", "KC", kickoff_hour=20),
        matchup("middle", "A", "B", kickoff_hour=19),
    ]
    previous = {
        "CAR": record(3, 13),
        "TEN": record(4, 12),
        "BUF": record(13, 3),
        "KC": record(14, 2),
        "A": record(10, 6),
        "B": record(10, 6),
    }
    current = {team: record(0, 0) for team in previous}

    bottom_two = rank_matchups(games, previous, current, bottom=2)

    assert [game.game_id for game in bottom_two] == ["low", "middle"]


def test_ranking_rejects_top_and_bottom_together() -> None:
    games = [matchup("only", "A", "B")]
    previous = {"A": record(8, 8), "B": record(8, 8)}
    current = {"A": record(0, 0), "B": record(0, 0)}

    with pytest.raises(ValueError, match="mutually exclusive"):
        rank_matchups(games, previous, current, top=1, bottom=1)


def test_sorting_is_deterministic_for_equal_scores() -> None:
    games = [
        matchup("later-a", "A", "B", kickoff_hour=20),
        matchup("earlier-z", "C", "D", kickoff_hour=18),
        matchup("earlier-a", "E", "F", kickoff_hour=18),
    ]
    previous = {team: record(8, 8) for team in ("A", "B", "C", "D", "E", "F")}
    current = {team: record(0, 0) for team in previous}

    ranked = rank_matchups(games, previous, current)

    assert [game.game_id for game in ranked] == ["earlier-a", "earlier-z", "later-a"]
