from datetime import datetime
from typing import ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
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
    formula_version: Literal["dynamic-watchability-v6"] = "dynamic-watchability-v6"


class RankingQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    season: int = Field(default=2025, ge=2025, le=2025)
    week: int = Field(ge=1, le=18)
    top: int | None = Field(
        default=None,
        ge=1,
        le=16,
        description="Return only the highest-rated games. Cannot be combined with bottom.",
    )
    bottom: int | None = Field(
        default=None,
        ge=1,
        le=16,
        description="Return only the lowest-rated games, worst first. Cannot be combined with top.",
    )

    @model_validator(mode="after")
    def validate_selection(self) -> Self:
        if self.top is not None and self.bottom is not None:
            raise ValueError("top and bottom are mutually exclusive")
        return self


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
    home_team_strength: float = Field(ge=0, le=1)
    away_team_strength: float = Field(ge=0, le=1)
    competitive_closeness: float = Field(ge=0, le=1)
    matchup_quality: float = Field(ge=0, le=1)
    rivalry_category: RivalryCategory | None
    rivalry_value: float = Field(ge=0, le=1)
    leverage_value: float = Field(default=0, ge=0, le=1)
    leverage_reason: str | None = None
    context_value: float = Field(ge=0, le=1)
    raw_score: float = Field(ge=0, le=1)
    display_score: float = Field(ge=1, le=10)


class RankedGame(APIModel):
    rank: int = Field(ge=1)
    game_id: str
    kickoff: datetime
    away_team: TeamRating
    home_team: TeamRating
    watchability_score: float = Field(ge=1, le=10)
    breakdown: ScoreBreakdown
    reasons: list[str]


class PlayerSpotlight(APIModel):
    player_id: str
    team_id: str
    name: str
    position: str
    image_url: str
    profile_url: str
    details: list[str] = Field(min_length=2, max_length=3)


class GameSummary(APIModel):
    matchup: str
    records: dict[str, str]
    logos: dict[str, str | None] = Field(default_factory=dict)
    score: float = Field(ge=1, le=10)
    reasons: list[str]
    unavailable_player_ids: list[str] = Field(default_factory=list)
    players_to_watch: list[PlayerSpotlight] = Field(default_factory=list)
