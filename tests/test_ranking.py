from datetime import UTC, datetime

import pytest

from nflviewer.models import RecordSummary
from nflviewer.ranking import MatchupInput, rank_matchups, score_matchup


def record(wins: int, losses: int, ties: int = 0) -> RecordSummary:
    return RecordSummary(wins=wins, losses=losses, ties=ties)


def matchup(
    game_id: str,
    home: str,
    away: str,
    *,
    kickoff_hour: int = 18,
    is_divisional: bool = False,
) -> MatchupInput:
    return MatchupInput(
        game_id=game_id,
        kickoff=datetime(2025, 9, 7, kickoff_hour, tzinfo=UTC),
        home_team_id=home,
        home_team_name=home,
        home_logo_url=None,
        away_team_id=away,
        away_team_name=away,
        away_logo_url=None,
        is_divisional=is_divisional,
    )


def test_two_bad_teams_receive_no_record_quality_or_score() -> None:
    game = matchup("bad", "CAR", "TEN")
    previous = {"CAR": record(8, 8), "TEN": record(8, 8)}
    current = {"CAR": record(2, 6), "TEN": record(2, 6)}

    result = score_matchup(game, previous, current)

    assert result.breakdown.record_quality == 0
    assert result.watchability_score == 0


def test_bad_divisional_matchup_only_receives_rivalry_value() -> None:
    game = matchup("bad-division", "NE", "BUF", is_divisional=True)
    previous = {"NE": record(8, 8), "BUF": record(8, 8)}
    current = {"NE": record(2, 6), "BUF": record(2, 6)}

    result = score_matchup(game, previous, current)

    assert result.breakdown.record_quality == 0
    assert result.watchability_score == 0.20


def test_two_good_teams_use_weaker_adjusted_record_as_quality() -> None:
    game = matchup("good", "A", "B")
    previous = {"A": record(8, 8), "B": record(8, 8)}
    current = {"A": record(5, 3), "B": record(6, 2)}

    result = score_matchup(game, previous, current)

    assert result.breakdown.record_quality == pytest.approx(7 / 12)
    assert result.watchability_score == 0.58
    assert result.reasons == ["Both teams have adjusted winning records"]


def test_divisional_value_saturates_instead_of_adding_directly() -> None:
    game = matchup("good-division", "A", "B", is_divisional=True)
    previous = {"A": record(8, 8), "B": record(8, 8)}
    current = {"A": record(5, 3), "B": record(6, 2)}

    result = score_matchup(game, previous, current)

    quality = 7 / 12
    assert result.breakdown.raw_score == pytest.approx(quality + (1 - quality) * 0.20)
    assert result.watchability_score == 0.67
    assert result.reasons == [
        "Both teams have adjusted winning records",
        "Divisional matchup",
    ]


def test_elite_records_score_above_moderate_winning_records() -> None:
    moderate = matchup("moderate", "A", "B")
    elite = matchup("elite", "C", "D")
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
