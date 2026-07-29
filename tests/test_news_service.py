from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from nflviewer.app import create_app
from nflviewer.news.feeds import FeedArticle, NewsSource
from nflviewer.news.service import NewsSyncService, one_year_before


class FakeFeedClient:
    def __init__(self, *, failing_source: NewsSource | None = None) -> None:
        self.calls: list[NewsSource] = []
        self.failing_source = failing_source

    async def fetch(self, source: NewsSource) -> list[FeedArticle]:
        self.calls.append(source)
        if source is self.failing_source:
            raise RuntimeError("publisher unavailable")
        return [
            FeedArticle(
                source=source,
                source_article_id=f"{source.value}-current",
                title=f"Current {source.value} training-camp story",
                author=None,
                excerpt=None,
                canonical_url=f"https://example.test/{source.value.lower()}",
                image_url=None,
                team_codes=(),
                published_at=datetime(2026, 7, 29, tzinfo=UTC),
            )
        ]


class FakeRepository:
    def __init__(
        self,
        *,
        refreshed_at: datetime | None = None,
        lock_acquired: bool = True,
    ) -> None:
        self.refreshed_at = refreshed_at
        self.lock_acquired = lock_acquired
        self.upserts: list[list[FeedArticle]] = []
        self.retention_cutoffs: list[datetime] = []
        self.opened = False
        self.closed = False

    async def open(self) -> None:
        self.opened = True

    async def close(self) -> None:
        self.closed = True

    @asynccontextmanager
    async def sync_lock(self) -> AsyncIterator[bool]:
        yield self.lock_acquired

    async def latest_refreshed_at(self, _: NewsSource) -> datetime | None:
        return self.refreshed_at

    async def upsert_articles(self, articles: list[FeedArticle]) -> int:
        self.upserts.append(articles)
        return len(articles)

    async def delete_before(self, cutoff: datetime) -> int:
        self.retention_cutoffs.append(cutoff)
        return 0


@pytest.mark.anyio
async def test_fresh_sources_are_not_requested_again_before_one_hour() -> None:
    now = datetime(2026, 7, 29, 18, tzinfo=UTC)
    repository = FakeRepository(refreshed_at=now - timedelta(minutes=30))
    client = FakeFeedClient()
    service = NewsSyncService(repository, client, now=lambda: now)

    result = await service.synchronize_once()

    assert client.calls == []
    assert result.skipped_sources == tuple(NewsSource)
    assert repository.retention_cutoffs == [datetime(2025, 7, 29, 18, tzinfo=UTC)]


@pytest.mark.anyio
async def test_one_publisher_failure_does_not_block_other_sources() -> None:
    now = datetime(2026, 7, 29, 18, tzinfo=UTC)
    repository = FakeRepository()
    client = FakeFeedClient(failing_source=NewsSource.CBS)
    service = NewsSyncService(repository, client, now=lambda: now)

    result = await service.synchronize_once()

    assert set(client.calls) == set(NewsSource)
    assert {articles[0].source for articles in repository.upserts} == {
        NewsSource.ESPN,
        NewsSource.FOX,
    }
    assert result.failed_sources == (NewsSource.CBS,)
    assert result.stored_articles == 2
    assert repository.retention_cutoffs == [datetime(2025, 7, 29, 18, tzinfo=UTC)]


@pytest.mark.anyio
async def test_competing_scheduler_does_no_work_without_the_lock() -> None:
    repository = FakeRepository(lock_acquired=False)
    client = FakeFeedClient()
    service = NewsSyncService(repository, client)

    result = await service.synchronize_once()

    assert result.lock_acquired is False
    assert client.calls == []
    assert repository.retention_cutoffs == []


def test_one_year_before_handles_leap_day() -> None:
    assert one_year_before(datetime(2024, 2, 29, 12, tzinfo=UTC)) == datetime(
        2023,
        2,
        28,
        12,
        tzinfo=UTC,
    )


@pytest.mark.anyio
async def test_scheduler_task_can_be_cancelled_cleanly() -> None:
    sleep_started = asyncio.Event()

    async def blocked_sleep(_: float) -> None:
        sleep_started.set()
        await asyncio.Future()

    service = NewsSyncService(
        FakeRepository(lock_acquired=False),
        FakeFeedClient(),
        sleep=blocked_sleep,
    )
    task = asyncio.create_task(service.run_forever())
    await sleep_started.wait()

    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task


def test_app_lifespan_opens_and_closes_the_news_runtime() -> None:
    repository = FakeRepository(lock_acquired=False)

    with TestClient(
        create_app(
            news_repository=repository,
            news_feed_client=FakeFeedClient(),
        )
    ):
        assert repository.opened is True
        assert repository.closed is False

    assert repository.closed is True
