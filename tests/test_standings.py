import pytest

from nflviewer.data import Team
from nflviewer.models import RecordSummary
from nflviewer.standings import build_standings, matchup_leverage


def record(wins: int, losses: int, ties: int = 0) -> RecordSummary:
    return RecordSummary(wins=wins, losses=losses, ties=ties)


def team(team_id: str, conference: str, division: str) -> Team:
    return Team(
        team_id=team_id,
        name=team_id,
        conference=conference,
        division=division,
        logo_url=None,
    )


def test_builds_deterministic_conference_and_division_ranks() -> None:
    teams = {
        "BUF": team("BUF", "AFC", "AFC East"),
        "MIA": team("MIA", "AFC", "AFC East"),
        "BAL": team("BAL", "AFC", "AFC North"),
        "PIT": team("PIT", "AFC", "AFC North"),
    }
    records = {
        "BUF": record(7, 2),
        "MIA": record(5, 4),
        "BAL": record(6, 3),
        "PIT": record(5, 4),
    }
    point_differentials = {"BUF": 40, "MIA": 12, "BAL": 25, "PIT": -3}

    standings = build_standings(teams, records, point_differentials)

    assert standings["BUF"].conference_rank == 1
    assert standings["BAL"].conference_rank == 2
    assert standings["MIA"].conference_rank == 3
    assert standings["PIT"].conference_rank == 4
    assert standings["BUF"].division_rank == 1
    assert standings["MIA"].division_rank == 2
    assert standings["BAL"].division_rank == 1
    assert standings["PIT"].division_rank == 2


def test_week_one_has_no_standings_leverage() -> None:
    teams = {
        "BAL": team("BAL", "AFC", "AFC North"),
        "PIT": team("PIT", "AFC", "AFC North"),
    }
    standings = build_standings(
        teams,
        {"BAL": record(0, 0), "PIT": record(0, 0)},
        {"BAL": 0, "PIT": 0},
    )

    leverage = matchup_leverage("BAL", "PIT", week=1, standings=standings)

    assert leverage.value == 0
    assert leverage.reason is None


def test_week_eighteen_direct_division_race_reaches_maximum_leverage() -> None:
    teams = {
        "BAL": team("BAL", "AFC", "AFC North"),
        "PIT": team("PIT", "AFC", "AFC North"),
        "CLE": team("CLE", "AFC", "AFC North"),
        "CIN": team("CIN", "AFC", "AFC North"),
    }
    standings = build_standings(
        teams,
        {
            "BAL": record(8, 8),
            "PIT": record(9, 7),
            "CLE": record(4, 12),
            "CIN": record(3, 13),
        },
        {"BAL": 10, "PIT": 20, "CLE": -50, "CIN": -80},
    )

    leverage = matchup_leverage("BAL", "PIT", week=18, standings=standings)

    assert leverage.value == pytest.approx(0.82)
    assert leverage.reason == "Direct division race matchup"
