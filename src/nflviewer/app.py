import logging
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import Annotated, Protocol

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from nflviewer.data import Record, Repository, SeasonData
from nflviewer.models import GameSummary, HealthResponse, RankingQuery, RecordSummary
from nflviewer.ranking import MatchupInput, rank_matchups

logger = logging.getLogger(__name__)


class DataRepository(Protocol):
    def get(self) -> SeasonData: ...


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


def _ranking_response(data: SeasonData, query: RankingQuery) -> list[GameSummary]:
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
        top=query.top,
    )
    return [
        GameSummary(
            matchup=f"{game.away_team.team_name} vs {game.home_team.team_name}",
            records={
                game.away_team.team_id: _display_record(game.away_team.current_record),
                game.home_team.team_id: _display_record(game.home_team.current_record),
            },
            score=game.watchability_score,
            reasons=game.reasons,
        )
        for game in games
    ]


def create_app(repository: DataRepository | None = None) -> FastAPI:
    data_repository = repository or Repository()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            app.state.season_data = data_repository.get()
        except Exception:
            logger.exception("Unable to load NFL season data")
            app.state.season_data = None
        yield

    application = FastAPI(
        title="NFL Viewer API",
        description="Rank 2025 NFL regular-season matchups by watchability.",
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
        return _ranking_response(data, query)

    return application


app = create_app()
