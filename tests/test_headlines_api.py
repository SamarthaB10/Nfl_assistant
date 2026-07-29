from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from nflviewer.app import create_app
from nflviewer.news.cursor import NewsCursor, encode_cursor
from nflviewer.news.feeds import NewsSource
from nflviewer.news.repository import NewsArticleRecord, NewsPage


class StubNewsRepository:
    def __init__(self, page: NewsPage) -> None:
        self.page = page
        self.list_calls: list[dict[str, object]] = []

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    @asynccontextmanager
    async def sync_lock(self) -> AsyncIterator[bool]:
        yield False

    async def list_articles(self, **kwargs: object) -> NewsPage:
        self.list_calls.append(kwargs)
        return self.page


def current_article() -> NewsArticleRecord:
    return NewsArticleRecord(
        id=42,
        source=NewsSource.ESPN,
        title="Current NFL training-camp headline",
        author="Example Reporter",
        excerpt="Current offseason reporting.",
        canonical_url="https://www.espn.com/nfl/story/_/id/42/current",
        image_url="https://a.espncdn.com/current.jpg",
        team_codes=("BUF", "KC"),
        published_at=datetime(2026, 7, 29, 19, 2, tzinfo=UTC),
    )


def test_headlines_returns_current_articles_with_default_pagination() -> None:
    repository = StubNewsRepository(
        NewsPage(items=(current_article(),), next_cursor=None, has_more=False)
    )

    with TestClient(create_app(news_repository=repository)) as client:
        response = client.get("/api/v1/headlines")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 42,
                "source": "ESPN",
                "title": "Current NFL training-camp headline",
                "author": "Example Reporter",
                "excerpt": "Current offseason reporting.",
                "url": "https://www.espn.com/nfl/story/_/id/42/current",
                "imageUrl": "https://a.espncdn.com/current.jpg",
                "teamCodes": ["BUF", "KC"],
                "publishedAt": "2026-07-29T19:02:00Z",
            }
        ],
        "nextCursor": None,
        "hasMore": False,
    }
    assert repository.list_calls == [
        {
            "limit": 20,
            "cursor": None,
            "source": None,
            "team": None,
        }
    ]


def test_headlines_passes_valid_cursor_source_and_team_filters() -> None:
    cursor = encode_cursor(
        NewsCursor(
            published_at=datetime(2026, 7, 29, 19, 2, tzinfo=UTC),
            article_id=42,
        )
    )
    repository = StubNewsRepository(NewsPage(items=(), next_cursor=None, has_more=False))

    with TestClient(create_app(news_repository=repository)) as client:
        response = client.get(
            "/api/v1/headlines",
            params={
                "limit": 35,
                "cursor": cursor,
                "source": "CBS",
                "team": "NE",
            },
        )

    assert response.status_code == 200
    assert repository.list_calls == [
        {
            "limit": 35,
            "cursor": cursor,
            "source": NewsSource.CBS,
            "team": "NE",
        }
    ]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 51},
        {"cursor": "invalid"},
        {"source": "NFL_NETWORK"},
        {"team": "XYZ"},
    ],
)
def test_headlines_rejects_invalid_queries(params: dict[str, object]) -> None:
    repository = StubNewsRepository(NewsPage(items=(), next_cursor=None, has_more=False))

    with TestClient(create_app(news_repository=repository)) as client:
        response = client.get("/api/v1/headlines", params=params)

    assert response.status_code == 422
    assert repository.list_calls == []


def test_headlines_returns_503_when_news_storage_is_not_configured() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/headlines")

    assert response.status_code == 503
    assert response.json() == {"detail": "Current NFL headlines are temporarily unavailable."}
