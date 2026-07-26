from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class APIModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
    data_loaded: bool
    supported_season: Literal[2025] = 2025
    formula_version: Literal["record-watchability-v1"] = "record-watchability-v1"


class RankingQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    season: int = Field(default=2025, ge=2025, le=2025)
    week: int = Field(ge=1, le=18)
    top: int | None = Field(default=None, ge=1, le=16)


class RecordSummary(APIModel):
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    ties: int = Field(ge=0)


class TeamRating(APIModel):
    team_id: str
    team_name: str
    logo_url: str | None
    previous_record: RecordSummary
    current_record: RecordSummary
    previous_win_rate: float = Field(ge=0, le=1)
    scoring_win_rate: float = Field(ge=0, le=1)
    is_good: bool


RivalryCategory = Literal[
    "DIVISIONAL",
    "CONFERENCE_OR_INTERCONFERENCE",
    "HISTORIC_OR_REGIONAL",
]


class ScoreBreakdown(APIModel):
    record_quality: float = Field(ge=0, le=1)
    rivalry_category: RivalryCategory | None
    rivalry_value: float = Field(ge=0, le=1)
    leverage_value: float = Field(default=0, ge=0, le=1)
    leverage_reason: str | None = None
    raw_score: float = Field(ge=0, le=1)
    display_score: float = Field(ge=0, le=1)


class RankedGame(APIModel):
    rank: int = Field(ge=1)
    game_id: str
    kickoff: datetime
    away_team: TeamRating
    home_team: TeamRating
    watchability_score: float = Field(ge=0, le=1)
    breakdown: ScoreBreakdown
    reasons: list[str]


class GameSummary(APIModel):
    matchup: str
    records: dict[str, str]
    score: float = Field(ge=0, le=1)
    reasons: list[str]
