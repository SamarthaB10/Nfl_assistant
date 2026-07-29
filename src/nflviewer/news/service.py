from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from nflviewer.news.feeds import FeedArticle, NewsSource

logger = logging.getLogger(__name__)

REFRESH_INTERVAL = timedelta(hours=1)
FAILED_REFRESH_RETRY_INTERVAL = timedelta(minutes=1)


class FeedClient(Protocol):
    async def fetch(self, source: NewsSource) -> list[FeedArticle]: ...


class NewsStore(Protocol):
    def sync_lock(self) -> AbstractAsyncContextManager[bool]: ...

    async def latest_refreshed_at(self, source: NewsSource) -> datetime | None: ...

    async def upsert_articles(self, articles: list[FeedArticle]) -> int: ...

    async def delete_before(self, cutoff: datetime) -> int: ...


@dataclass(frozen=True, slots=True)
class SyncResult:
    lock_acquired: bool
    stored_articles: int = 0
    skipped_sources: tuple[NewsSource, ...] = ()
    failed_sources: tuple[NewsSource, ...] = ()


def one_year_before(value: datetime) -> datetime:
    try:
        return value.replace(year=value.year - 1)
    except ValueError:
        return value.replace(year=value.year - 1, day=28)


class NewsSyncService:
    def __init__(
        self,
        repository: NewsStore,
        client: FeedClient,
        *,
        now: Callable[[], datetime] | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        refresh_interval: timedelta = REFRESH_INTERVAL,
        failed_refresh_retry_interval: timedelta = FAILED_REFRESH_RETRY_INTERVAL,
    ) -> None:
        self._repository = repository
        self._client = client
        self._now = now or (lambda: datetime.now(UTC))
        self._sleep = sleep
        self._refresh_interval = refresh_interval
        self._failed_refresh_retry_interval = failed_refresh_retry_interval

    async def _refresh_source(self, source: NewsSource) -> tuple[NewsSource, int, bool]:
        try:
            articles = await self._client.fetch(source)
            stored = await self._repository.upsert_articles(articles)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Unable to refresh %s NFL news", source.value)
            return source, 0, False
        return source, stored, True

    async def synchronize_once(self) -> SyncResult:
        async with self._repository.sync_lock() as acquired:
            if not acquired:
                return SyncResult(lock_acquired=False)

            now = self._now().astimezone(UTC)
            freshness_cutoff = now - self._refresh_interval
            refresh_sources: list[NewsSource] = []
            skipped_sources: list[NewsSource] = []
            for source in NewsSource:
                refreshed_at = await self._repository.latest_refreshed_at(source)
                if refreshed_at is not None and refreshed_at > freshness_cutoff:
                    skipped_sources.append(source)
                else:
                    refresh_sources.append(source)

            results = await asyncio.gather(
                *(self._refresh_source(source) for source in refresh_sources)
            )
            await self._repository.delete_before(one_year_before(now))

        return SyncResult(
            lock_acquired=True,
            stored_articles=sum(stored for _, stored, succeeded in results if succeeded),
            skipped_sources=tuple(skipped_sources),
            failed_sources=tuple(source for source, _, succeeded in results if not succeeded),
        )

    async def run_forever(self) -> None:
        while True:
            sleep_interval = self._refresh_interval
            try:
                result = await self.synchronize_once()
                if result.failed_sources:
                    sleep_interval = self._failed_refresh_retry_interval
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("NFL news synchronization cycle failed")
                sleep_interval = self._failed_refresh_retry_interval
            await self._sleep(sleep_interval.total_seconds())
