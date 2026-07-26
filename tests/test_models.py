import pytest
from pydantic import ValidationError

from nflviewer.models import RankingQuery


def test_ranking_query_defaults_to_all_2025_games() -> None:
    query = RankingQuery(week=4)

    assert query.season == 2025
    assert query.week == 4
    assert query.top is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("season", 2026),
        ("week", 0),
        ("week", 19),
        ("top", 0),
        ("top", 17),
    ],
)
def test_ranking_query_rejects_unsupported_values(field: str, value: int) -> None:
    values = {"week": 4, field: value}

    with pytest.raises(ValidationError):
        RankingQuery.model_validate(values)

