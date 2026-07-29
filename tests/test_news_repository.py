from __future__ import annotations

import os
from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from psycopg import OperationalError

from nflviewer.news.cursor import InvalidCursorError, NewsCursor, decode_cursor, encode_cursor
from nflviewer.news.feeds import FeedArticle, NewsSource
from nflviewer.news.repository import NewsRepository

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql:///leaguewatch_test")


@pytest.fixture
async def repository() -> AsyncIterator[NewsRepository]:
    news_repository = NewsRepository(TEST_DATABASE_URL)
    try:
        await news_repository.open()
    except OperationalError:
        pytest.fail(
            "PostgreSQL test database is unavailable. Create leaguewatch_test and apply migrations."
        )
    async with news_repository.pool.connection() as connection:
        await connection.execute("TRUNCATE news_articles RESTART IDENTITY")
    yield news_repository
    await news_repository.close()


def article(
    *,
    source: NewsSource,
    source_article_id: str,
    title: str,
    canonical_url: str,
    published_at: datetime,
    team_codes: tuple[str, ...],
) -> FeedArticle:
    return FeedArticle(
        source=source,
        source_article_id=source_article_id,
        title=title,
        author="Reporter",
        excerpt="Current NFL coverage",
        canonical_url=canonical_url,
        image_url=None,
        team_codes=team_codes,
        published_at=published_at,
    )


def test_cursor_round_trip_preserves_timestamp_and_id() -> None:
    cursor = NewsCursor(published_at=datetime(2026, 7, 29, 18, 30, tzinfo=UTC), article_id=42)

    assert decode_cursor(encode_cursor(cursor)) == cursor


@pytest.mark.parametrize("cursor", ["", "not-base64", "e30", "W10"])
def test_cursor_rejects_malformed_values(cursor: str) -> None:
    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor)


@pytest.mark.anyio
async def test_upsert_updates_one_publisher_article_without_duplication(
    repository: NewsRepository,
) -> None:
    published_at = datetime.now(UTC)
    original = article(
        source=NewsSource.ESPN,
        source_article_id="espn-1",
        title="Original headline",
        canonical_url="https://www.espn.com/nfl/story/_/id/1/current",
        published_at=published_at,
        team_codes=("KC",),
    )

    await repository.upsert_articles([original])
    await repository.upsert_articles([replace(original, title="Updated headline")])
    page = await repository.list_articles(limit=20)

    assert len(page.items) == 1
    assert page.items[0].title == "Updated headline"


@pytest.mark.anyio
async def test_canonical_url_deduplicates_a_changed_publisher_guid(
    repository: NewsRepository,
) -> None:
    published_at = datetime.now(UTC)
    original = article(
        source=NewsSource.CBS,
        source_article_id="old-guid",
        title="Original CBS headline",
        canonical_url="https://www.cbssports.com/nfl/news/stable-url/",
        published_at=published_at,
        team_codes=("BUF",),
    )

    await repository.upsert_articles([original])
    await repository.upsert_articles(
        [
            replace(
                original,
                source_article_id="new-guid",
                title="Updated CBS headline",
            )
        ]
    )
    page = await repository.list_articles(limit=20)

    assert len(page.items) == 1
    assert page.items[0].title == "Updated CBS headline"


@pytest.mark.anyio
async def test_separate_publishers_covering_one_event_remain_visible(
    repository: NewsRepository,
) -> None:
    published_at = datetime.now(UTC)
    await repository.upsert_articles(
        [
            article(
                source=NewsSource.ESPN,
                source_article_id="espn-event",
                title="ESPN coverage",
                canonical_url="https://www.espn.com/nfl/story/_/id/2/current",
                published_at=published_at,
                team_codes=("BUF",),
            ),
            article(
                source=NewsSource.CBS,
                source_article_id="cbs-event",
                title="CBS coverage",
                canonical_url="https://www.cbssports.com/nfl/news/current-event/",
                published_at=published_at,
                team_codes=("BUF",),
            ),
        ]
    )

    page = await repository.list_articles(limit=20)

    assert {item.source for item in page.items} == {NewsSource.ESPN, NewsSource.CBS}


@pytest.mark.anyio
async def test_cursor_pagination_uses_id_to_break_equal_timestamps(
    repository: NewsRepository,
) -> None:
    published_at = datetime.now(UTC)
    await repository.upsert_articles(
        [
            article(
                source=NewsSource.ESPN,
                source_article_id=f"espn-{number}",
                title=f"Headline {number}",
                canonical_url=f"https://www.espn.com/nfl/story/_/id/{number}/current",
                published_at=published_at,
                team_codes=("KC",),
            )
            for number in range(1, 4)
        ]
    )

    first_page = await repository.list_articles(limit=2)
    second_page = await repository.list_articles(limit=2, cursor=first_page.next_cursor)

    first_ids = [item.id for item in first_page.items]
    second_ids = [item.id for item in second_page.items]
    assert first_page.has_more is True
    assert first_page.next_cursor is not None
    assert not set(first_ids) & set(second_ids)
    assert first_ids + second_ids == sorted(first_ids + second_ids, reverse=True)


@pytest.mark.anyio
async def test_source_and_team_filters_are_combined(
    repository: NewsRepository,
) -> None:
    published_at = datetime.now(UTC)
    await repository.upsert_articles(
        [
            article(
                source=NewsSource.ESPN,
                source_article_id="espn-kc",
                title="ESPN Chiefs",
                canonical_url="https://www.espn.com/nfl/story/_/id/4/current",
                published_at=published_at,
                team_codes=("KC",),
            ),
            article(
                source=NewsSource.CBS,
                source_article_id="cbs-kc",
                title="CBS Chiefs",
                canonical_url="https://www.cbssports.com/nfl/news/chiefs-current/",
                published_at=published_at,
                team_codes=("KC",),
            ),
            article(
                source=NewsSource.ESPN,
                source_article_id="espn-buf",
                title="ESPN Bills",
                canonical_url="https://www.espn.com/nfl/story/_/id/5/current",
                published_at=published_at,
                team_codes=("BUF",),
            ),
        ]
    )

    page = await repository.list_articles(
        limit=20,
        source=NewsSource.ESPN,
        team="KC",
    )

    assert [item.title for item in page.items] == ["ESPN Chiefs"]


@pytest.mark.anyio
async def test_retention_deletes_articles_older_than_one_year(
    repository: NewsRepository,
) -> None:
    now = datetime.now(UTC)
    await repository.upsert_articles(
        [
            article(
                source=NewsSource.FOX,
                source_article_id="fox-old",
                title="Expired story",
                canonical_url="https://www.foxsports.com/stories/nfl/expired",
                published_at=now - timedelta(days=366),
                team_codes=(),
            ),
            article(
                source=NewsSource.FOX,
                source_article_id="fox-current",
                title="Current story",
                canonical_url="https://www.foxsports.com/stories/nfl/current",
                published_at=now,
                team_codes=(),
            ),
        ]
    )

    deleted = await repository.delete_before(now - timedelta(days=365))
    page = await repository.list_articles(limit=20)

    assert deleted == 1
    assert [item.title for item in page.items] == ["Current story"]


@pytest.mark.anyio
async def test_sync_lock_allows_only_one_repository_instance(
    repository: NewsRepository,
) -> None:
    competing_repository = NewsRepository(TEST_DATABASE_URL)
    await competing_repository.open()
    try:
        async with (
            repository.sync_lock() as first_acquired,
            competing_repository.sync_lock() as second_acquired,
        ):
            assert first_acquired is True
            assert second_acquired is False
    finally:
        await competing_repository.close()
