import asyncio
import logging
import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Annotated, Protocol

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from psycopg import Error as PsycopgError
from psycopg_pool import PoolClosed, PoolTimeout

from nflviewer.data import Record, Repository, SeasonData
from nflviewer.headlines import HeadlineRepository
from nflviewer.models import (
    GameSummary,
    HeadlineItem,
    HeadlinesPage,
    HeadlinesQuery,
    HealthResponse,
    RankingQuery,
    RecordSummary,
)
from nflviewer.news.feeds import NewsSource, RssFeedClient
from nflviewer.news.repository import NewsPage, NewsRepository
from nflviewer.news.service import FeedClient, NewsStore, NewsSyncService
from nflviewer.ranking import MatchupInput, rank_matchups

logger = logging.getLogger(__name__)


class DataRepository(Protocol):
    def get(self) -> SeasonData: ...


class NewsRuntimeRepository(NewsStore, Protocol):
    async def open(self) -> None: ...

    async def close(self) -> None: ...

    async def list_articles(
        self,
        *,
        limit: int,
        cursor: str | None = None,
        source: NewsSource | None = None,
        team: str | None = None,
    ) -> NewsPage: ...


def _record_summaries(records: Mapping[str, Record]) -> dict[str, RecordSummary]:
    return {
        team_id: RecordSummary(wins=record.wins, losses=record.losses, ties=record.ties)
        for team_id, record in records.items()
    }


def _display_record(record: RecordSummary) -> str:
    record_parts = [record.wins, record.losses]
    if record.ties:
        record_parts.append(record.ties)
    return "-".join(str(value) for value in record_parts)


def _ranking_response(
    data: SeasonData,
    query: RankingQuery,
    headline_repository: HeadlineRepository,
) -> list[GameSummary]:
    matchups = data.matchups_for_week(query.week)
    inputs = [
        MatchupInput(
            game_id=matchup.game_id,
            week=matchup.week,
            kickoff=matchup.kickoff,
            home_team_id=matchup.home_team_id,
            home_team_name=data.teams[matchup.home_team_id].name,
            home_logo_url=data.teams[matchup.home_team_id].logo_url,
            away_team_id=matchup.away_team_id,
            away_team_name=data.teams[matchup.away_team_id].name,
            away_logo_url=data.teams[matchup.away_team_id].logo_url,
            is_divisional=matchup.is_divisional,
        )
        for matchup in matchups
    ]
    games = rank_matchups(
        inputs,
        _record_summaries(data.previous_records()),
        _record_summaries(data.current_records_before_week(query.week)),
        standings=data.current_standings_before_week(query.week),
        team_metrics=data.team_metrics_before_week(query.week),
        top=query.top,
        bottom=query.bottom,
    )
    player_spotlights = data.player_spotlights_before_week(
        query.week,
        list(data.teams),
    )
    summaries: list[GameSummary] = []
    for game in games:
        reasons = list(game.reasons)
        headline_reason = headline_repository.reason_for(game.game_id)
        if headline_reason:
            reasons.append(headline_reason)
        summaries.append(
            GameSummary(
                matchup=f"{game.away_team.team_name} vs {game.home_team.team_name}",
                records={
                    game.away_team.team_id: _display_record(game.away_team.current_record),
                    game.home_team.team_id: _display_record(game.home_team.current_record),
                },
                logos={
                    game.away_team.team_id: game.away_team.logo_url,
                    game.home_team.team_id: game.home_team.logo_url,
                },
                score=game.watchability_score,
                reasons=reasons,
                unavailable_player_ids=data.unavailable_player_ids_for_matchup(
                    query.week,
                    game.away_team.team_id,
                    game.home_team.team_id,
                ),
                players_to_watch=[
                    player_spotlights[team_id]
                    for team_id in (game.away_team.team_id, game.home_team.team_id)
                    if team_id in player_spotlights
                ],
            )
        )
    return summaries


def create_app(
    repository: DataRepository | None = None,
    *,
    headline_repository: HeadlineRepository | None = None,
    news_repository: NewsRuntimeRepository | None = None,
    news_feed_client: FeedClient | None = None,
) -> FastAPI:
    data_repository = repository or Repository()
    headlines = headline_repository or HeadlineRepository(Path("data/headlines-2025.json"))

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        news_task: asyncio.Task[None] | None = None
        http_client: httpx.AsyncClient | None = None
        news_repository_open = False
        try:
            app.state.season_data = data_repository.get()
        except Exception:
            logger.exception("Unable to load NFL season data")
            app.state.season_data = None
        app.state.news_repository = None
        if news_repository is not None:
            try:
                await news_repository.open()
                news_repository_open = True
                app.state.news_repository = news_repository
                active_feed_client = news_feed_client
                if active_feed_client is None:
                    http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
                    active_feed_client = RssFeedClient(http_client)
                news_service = NewsSyncService(news_repository, active_feed_client)
                news_task = asyncio.create_task(
                    news_service.run_forever(),
                    name="leaguewatch-news-sync",
                )
            except Exception:
                logger.exception("Unable to start NFL news synchronization")
                app.state.news_repository = None
        try:
            yield
        finally:
            if news_task is not None:
                news_task.cancel()
                with suppress(asyncio.CancelledError):
                    await news_task
            if http_client is not None:
                await http_client.aclose()
            if news_repository is not None and news_repository_open:
                await news_repository.close()

    application = FastAPI(
        title="LeagueWatch API",
        description=("Rank 2025 NFL matchups and retrieve current multi-publisher NFL news."),
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @application.get("/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        data_loaded = getattr(request.app.state, "season_data", None) is not None
        return HealthResponse(data_loaded=data_loaded)

    @application.get(
        "/api/v1/rankings",
        response_model=list[GameSummary],
        summary="Rank a week of 2025 NFL matchups",
    )
    def rankings(
        request: Request,
        query: Annotated[RankingQuery, Query()],
    ) -> list[GameSummary]:
        data = getattr(request.app.state, "season_data", None)
        if data is None:
            raise HTTPException(
                status_code=503,
                detail="NFL data is unavailable. Run the data sync command and retry.",
            )
        return _ranking_response(data, query, headlines)

    @application.get(
        "/api/v1/headlines",
        response_model=HeadlinesPage,
        summary="List current NFL headlines",
    )
    async def current_headlines(
        request: Request,
        query: Annotated[HeadlinesQuery, Query()],
    ) -> HeadlinesPage:
        news = getattr(request.app.state, "news_repository", None)
        if news is None:
            raise HTTPException(
                status_code=503,
                detail="Current NFL headlines are temporarily unavailable.",
            )
        try:
            page = await news.list_articles(
                limit=query.limit,
                cursor=query.cursor,
                source=NewsSource(query.source) if query.source else None,
                team=query.team,
            )
        except (PoolClosed, PoolTimeout, PsycopgError):
            logger.exception("Unable to read current NFL headlines")
            raise HTTPException(
                status_code=503,
                detail="Current NFL headlines are temporarily unavailable.",
            ) from None
        return HeadlinesPage(
            items=[
                HeadlineItem(
                    id=item.id,
                    source=item.source.value,
                    title=item.title,
                    author=item.author,
                    excerpt=item.excerpt,
                    url=item.canonical_url,
                    image_url=item.image_url,
                    team_codes=list(item.team_codes),
                    published_at=item.published_at,
                )
                for item in page.items
            ],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
        )

    return application


database_url = os.getenv("DATABASE_URL")
app = create_app(
    news_repository=NewsRepository(database_url) if database_url else None,
)
