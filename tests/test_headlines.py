from datetime import UTC, datetime, timedelta

from nflviewer.headlines import (
    Headline,
    HeadlineRepository,
    select_relevant_headline,
)

KICKOFF = datetime(2025, 9, 7, 17, tzinfo=UTC)


def candidate(
    title: str,
    *,
    published_at: datetime | None = None,
    url: str = "https://www.espn.com/nfl/story/_/id/1/example",
) -> Headline:
    return Headline(
        game_id="",
        title=title,
        published_at=published_at or KICKOFF - timedelta(days=1),
        url=url,
    )


def test_select_relevant_headline_prefers_pregame_preview() -> None:
    selected = select_relevant_headline(
        [
            candidate("Bills and Ravens meet again in anticipated rematch"),
            candidate(
                "Ravens at Bills: Week 1 preview",
                published_at=KICKOFF - timedelta(days=2),
                url="https://www.espn.com/nfl/preview?gameId=401772510",
            ),
        ],
        away_team_id="BAL",
        home_team_id="BUF",
        kickoff=KICKOFF,
    )

    assert selected is not None
    assert selected.title == "Ravens at Bills: Week 1 preview"


def test_select_relevant_headline_rejects_leakage_and_irrelevant_results() -> None:
    selected = select_relevant_headline(
        [
            candidate(
                "Bills beat Ravens in Week 1 thriller",
                published_at=KICKOFF + timedelta(hours=4),
            ),
            candidate("Bills enter Week 1 with Super Bowl expectations"),
            candidate("Ravens-Bills odds, betting picks and predictions"),
            candidate(
                "Ravens and Bills renew rivalry",
                published_at=KICKOFF - timedelta(days=20),
            ),
        ],
        away_team_id="BAL",
        home_team_id="BUF",
        kickoff=KICKOFF,
    )

    assert selected is None


def test_headline_repository_loads_cached_reason(tmp_path) -> None:
    path = tmp_path / "headlines.json"
    path.write_text(
        """
        [
          {
            "gameId": "2025_01_BAL_BUF",
            "headline": "Ravens at Bills: Week 1 preview",
            "publishedAt": "2025-09-05T12:00:00Z",
            "url": "https://www.espn.com/nfl/preview?gameId=401772510"
          }
        ]
        """,
        encoding="utf-8",
    )

    repository = HeadlineRepository(path)

    assert repository.reason_for("2025_01_BAL_BUF") == ("Headline: Ravens at Bills: Week 1 preview")
    assert repository.reason_for("2025_01_TB_ATL") is None


def test_missing_headline_cache_is_neutral(tmp_path) -> None:
    repository = HeadlineRepository(tmp_path / "missing.json")

    assert repository.reason_for("2025_01_BAL_BUF") is None
