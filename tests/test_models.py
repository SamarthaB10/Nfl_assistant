import pytest
from pydantic import ValidationError

from nflviewer.models import GameSummary, RankingQuery


def test_ranking_query_defaults_to_all_2025_games() -> None:
    query = RankingQuery(week=4)

    assert query.season == 2025
    assert query.week == 4
    assert query.top is None
    assert query.bottom is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("season", 2026),
        ("week", 0),
        ("week", 19),
        ("top", 0),
        ("top", 17),
        ("bottom", 0),
        ("bottom", 17),
    ],
)
def test_ranking_query_rejects_unsupported_values(field: str, value: int) -> None:
    values = {"week": 4, field: value}

    with pytest.raises(ValidationError):
        RankingQuery.model_validate(values)


def test_ranking_query_rejects_top_and_bottom_together() -> None:
    with pytest.raises(ValidationError, match="mutually exclusive"):
        RankingQuery(week=4, top=3, bottom=3)


def test_game_summary_accepts_ten_point_watchability_score() -> None:
    game = GameSummary(
        matchup="Team A vs Team B",
        records={"A": "10-2", "B": "11-1"},
        score=10,
        reasons=[],
    )

    assert game.score == 10
    assert game.logos == {}
