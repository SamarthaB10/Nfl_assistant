from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from nflviewer.news.cursor import NewsCursor, decode_cursor, encode_cursor
from nflviewer.news.feeds import FeedArticle, NewsSource

NEWS_SYNC_LOCK_ID = int.from_bytes(b"LW_NEWS", byteorder="big")


@dataclass(frozen=True, slots=True)
class NewsArticleRecord:
    id: int
    source: NewsSource
    title: str
    author: str | None
    excerpt: str | None
    canonical_url: str
    image_url: str | None
    team_codes: tuple[str, ...]
    published_at: datetime


@dataclass(frozen=True, slots=True)
class NewsPage:
    items: tuple[NewsArticleRecord, ...]
    next_cursor: str | None
    has_more: bool


class NewsRepository:
    """Parameterized PostgreSQL access for current NFL news."""

    def __init__(
        self,
        database_url: str,
        *,
        min_pool_size: int = 1,
        max_pool_size: int = 5,
    ) -> None:
        self.pool = AsyncConnectionPool(
            conninfo=database_url,
            min_size=min_pool_size,
            max_size=max_pool_size,
            open=False,
            timeout=5,
            kwargs={"row_factory": dict_row},
        )

    async def open(self) -> None:
        await self.pool.open(wait=True, timeout=5)

    async def close(self) -> None:
        await self.pool.close()

    async def upsert_articles(self, articles: list[FeedArticle]) -> int:
        if not articles:
            return 0
        insert_statement = """
            INSERT INTO news_articles (
                source,
                source_article_id,
                title,
                author,
                excerpt,
                canonical_url,
                image_url,
                team_codes,
                published_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """
        update_statement = """
            UPDATE news_articles SET
                source = %s,
                source_article_id = %s,
                title = %s,
                author = %s,
                excerpt = %s,
                canonical_url = %s,
                image_url = %s,
                team_codes = %s,
                published_at = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE
                (source = %s AND source_article_id = %s)
                OR canonical_url = %s
        """
        async with self.pool.connection() as connection:
            for article in articles:
                values = (
                    article.source.value,
                    article.source_article_id,
                    article.title,
                    article.author,
                    article.excerpt,
                    article.canonical_url,
                    article.image_url,
                    list(article.team_codes),
                    article.published_at,
                )
                await connection.execute(insert_statement, values)
                await connection.execute(
                    update_statement,
                    (
                        *values,
                        article.source.value,
                        article.source_article_id,
                        article.canonical_url,
                    ),
                )
        return len(articles)

    async def delete_before(self, cutoff: datetime) -> int:
        async with self.pool.connection() as connection:
            result = await connection.execute(
                "DELETE FROM news_articles WHERE published_at < %s",
                (cutoff,),
            )
        return result.rowcount or 0

    async def latest_refreshed_at(self, source: NewsSource) -> datetime | None:
        async with self.pool.connection() as connection:
            result = await connection.execute(
                """
                SELECT MAX(updated_at) AS refreshed_at
                FROM news_articles
                WHERE source = %s
                """,
                (source.value,),
            )
            row = await result.fetchone()
        return row["refreshed_at"] if row else None

    @asynccontextmanager
    async def sync_lock(self) -> AsyncIterator[bool]:
        async with self.pool.connection() as connection:
            result = await connection.execute(
                "SELECT pg_try_advisory_lock(%s) AS acquired",
                (NEWS_SYNC_LOCK_ID,),
            )
            row = await result.fetchone()
            acquired = bool(row and row["acquired"])
            try:
                yield acquired
            finally:
                if acquired:
                    await connection.execute(
                        "SELECT pg_advisory_unlock(%s)",
                        (NEWS_SYNC_LOCK_ID,),
                    )

    async def list_articles(
        self,
        *,
        limit: int,
        cursor: str | None = None,
        source: NewsSource | None = None,
        team: str | None = None,
    ) -> NewsPage:
        clauses = ["published_at >= CURRENT_TIMESTAMP - INTERVAL '1 year'"]
        parameters: list[object] = []
        if source is not None:
            clauses.append("source = %s")
            parameters.append(source.value)
        if team is not None:
            clauses.append("team_codes @> ARRAY[%s]::text[]")
            parameters.append(team)
        if cursor is not None:
            decoded = decode_cursor(cursor)
            clauses.append("(published_at, id) < (%s, %s)")
            parameters.extend((decoded.published_at, decoded.article_id))
        parameters.append(limit + 1)

        # Every clause above is a constant owned by this module. External values
        # are passed separately through psycopg parameters.
        query = f"""
            SELECT
                id,
                source,
                title,
                author,
                excerpt,
                canonical_url,
                image_url,
                team_codes,
                published_at
            FROM news_articles
            WHERE {" AND ".join(clauses)}
            ORDER BY published_at DESC, id DESC
            LIMIT %s
        """
        async with self.pool.connection() as connection:
            result = await connection.execute(query, parameters)
            rows = await result.fetchall()

        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        items = tuple(
            NewsArticleRecord(
                id=row["id"],
                source=NewsSource(row["source"]),
                title=row["title"],
                author=row["author"],
                excerpt=row["excerpt"],
                canonical_url=row["canonical_url"],
                image_url=row["image_url"],
                team_codes=tuple(row["team_codes"]),
                published_at=row["published_at"],
            )
            for row in visible_rows
        )
        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = encode_cursor(
                NewsCursor(published_at=last.published_at, article_id=last.id)
            )
        return NewsPage(items=items, next_cursor=next_cursor, has_more=has_more)
