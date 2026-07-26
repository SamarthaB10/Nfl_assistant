from datetime import UTC, datetime

from nflviewer.headlines import Headline
from nflviewer.sync_headlines import parse_search_response, search_matchup


def test_parse_search_response_extracts_valid_articles() -> None:
    payload = {
        "results": [
            {
                "contents": [
                    {
                        "displayName": "Ravens at Bills: Week 1 preview",
                        "date": "2025-09-04T21:11:00.000+00:00",
                        "link": {"web": "http://www.espn.com/nfl/preview?gameId=401772918"},
                    },
                    {"displayName": "Incomplete result"},
                ]
            }
        ]
    }

    assert parse_search_response(payload) == [
        Headline(
            game_id="",
            title="Ravens at Bills: Week 1 preview",
            published_at=datetime(2025, 9, 4, 21, 11, tzinfo=UTC),
            url="https://www.espn.com/nfl/preview?gameId=401772918",
        )
    ]


def test_search_matchup_uses_fallback_query_until_a_valid_headline_is_found() -> None:
    queries: list[str] = []

    def search(query: str) -> list[Headline]:
        queries.append(query)
        if len(queries) == 1:
            return []
        return [
            Headline(
                game_id="",
                title="Ravens prepare to visit Bills again",
                published_at=datetime(2025, 9, 4, 21, 11, tzinfo=UTC),
                url="https://www.espn.com/nfl/preview?gameId=401772918",
            )
        ]

    selected = search_matchup(
        game_id="2025_01_BAL_BUF",
        week=1,
        away_team_id="BAL",
        away_team_name="Baltimore Ravens",
        home_team_id="BUF",
        home_team_name="Buffalo Bills",
        kickoff=datetime(2025, 9, 8, 0, 20, tzinfo=UTC),
        search=search,
    )

    assert len(queries) == 2
    assert selected is not None
    assert selected.game_id == "2025_01_BAL_BUF"
