from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from nflviewer.standings import TeamStanding, build_standings

TARGET_SEASON = 2025
PREVIOUS_SEASON = 2024
TEAM_ALIASES = {"LA": "LAR", "JAC": "JAX"}

SCHEDULE_COLUMNS = {
    "game_id",
    "season",
    "game_type",
    "week",
    "gameday",
    "gametime",
    "away_team",
    "away_score",
    "home_team",
    "home_score",
    "div_game",
}
TEAM_COLUMNS = {
    "team_abbr",
    "team_name",
    "team_conf",
    "team_division",
    "team_logo_espn",
}


class DataValidationError(ValueError):
    """Raised when nflverse data cannot safely be used for rankings."""


@dataclass(frozen=True, slots=True)
class Record:
    wins: int = 0
    losses: int = 0
    ties: int = 0


@dataclass(frozen=True, slots=True)
class Team:
    team_id: str
    name: str
    conference: str
    division: str
    logo_url: str | None


@dataclass(frozen=True, slots=True)
class Matchup:
    game_id: str
    season: int
    week: int
    kickoff: datetime
    away_team_id: str
    home_team_id: str
    away_score: int | None
    home_score: int | None
    is_divisional: bool


def normalize_team_id(team_id: str) -> str:
    """Return the current canonical identifier used throughout the service."""
    return TEAM_ALIASES.get(team_id, team_id)


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise DataValidationError(f"{label} data is missing required columns: {names}")


def _kickoff(gameday: str, gametime: str) -> datetime:
    try:
        local = datetime.fromisoformat(f"{gameday}T{gametime}").replace(
            tzinfo=ZoneInfo("America/New_York")
        )
    except (TypeError, ValueError) as exc:
        raise DataValidationError(f"Invalid kickoff date/time: {gameday} {gametime}") from exc
    return local.astimezone(UTC)


class SeasonData:
    """Validated, normalized 2024/2025 nflverse data held in memory."""

    def __init__(
        self,
        schedules: pl.DataFrame,
        team_frame: pl.DataFrame,
        teams: dict[str, Team],
    ) -> None:
        self._schedules = schedules
        self._team_frame = team_frame
        self.teams = teams

    @classmethod
    def from_frames(
        cls,
        schedules: pl.DataFrame,
        teams: pl.DataFrame,
        *,
        require_32_teams: bool = False,
    ) -> SeasonData:
        _require_columns(schedules, SCHEDULE_COLUMNS, "Schedule")
        _require_columns(teams, TEAM_COLUMNS, "Team")

        regular = schedules.filter(
            (pl.col("game_type") == "REG")
            & pl.col("season").is_in([PREVIOUS_SEASON, TARGET_SEASON])
        ).select(sorted(SCHEDULE_COLUMNS))

        duplicate_ids = (
            regular.group_by("game_id").len().filter(pl.col("len") > 1)["game_id"].to_list()
        )
        if duplicate_ids:
            raise DataValidationError(f"Duplicate game_id values: {', '.join(duplicate_ids)}")

        one_score_missing = regular.filter(
            pl.col("away_score").is_null() != pl.col("home_score").is_null()
        )
        if not one_score_missing.is_empty():
            game_ids = ", ".join(one_score_missing["game_id"].to_list())
            raise DataValidationError(f"Games with exactly one score are invalid: {game_ids}")

        regular = regular.with_columns(
            pl.col("away_team").replace(TEAM_ALIASES),
            pl.col("home_team").replace(TEAM_ALIASES),
        )
        current_schedule = regular.filter(pl.col("season") == TARGET_SEASON)
        current_ids = set(current_schedule["away_team"]).union(current_schedule["home_team"])
        if require_32_teams and len(current_ids) != 32:
            raise DataValidationError(
                f"Expected 32 current teams in {TARGET_SEASON} schedule, found {len(current_ids)}"
            )

        team_frame = teams.select(sorted(TEAM_COLUMNS)).with_columns(
            pl.col("team_abbr").replace(TEAM_ALIASES)
        )
        metadata: dict[str, Team] = {}
        for row in team_frame.iter_rows(named=True):
            team_id = row["team_abbr"]
            if team_id in current_ids:
                metadata[team_id] = Team(
                    team_id=team_id,
                    name=row["team_name"],
                    conference=row["team_conf"],
                    division=row["team_division"],
                    logo_url=row["team_logo_espn"],
                )

        missing_metadata = current_ids.difference(metadata)
        if missing_metadata:
            names = ", ".join(sorted(missing_metadata))
            raise DataValidationError(f"Team metadata missing for: {names}")

        filtered_team_frame = team_frame.filter(pl.col("team_abbr").is_in(current_ids)).unique(
            subset=["team_abbr"], keep="last"
        )
        return cls(regular, filtered_team_frame, metadata)

    @classmethod
    def from_cache(
        cls,
        schedule_path: Path,
        team_path: Path,
        *,
        require_32_teams: bool = False,
    ) -> SeasonData:
        if not schedule_path.exists() or not team_path.exists():
            raise FileNotFoundError("NFL data cache is incomplete")
        return cls.from_frames(
            pl.read_parquet(schedule_path),
            pl.read_parquet(team_path),
            require_32_teams=require_32_teams,
        )

    def write_cache(self, schedule_path: Path, team_path: Path) -> None:
        schedule_path.parent.mkdir(parents=True, exist_ok=True)
        team_path.parent.mkdir(parents=True, exist_ok=True)
        self._schedules.write_parquet(schedule_path)
        self._team_frame.write_parquet(team_path)

    def matchups_for_week(self, week: int) -> list[Matchup]:
        rows = self._schedules.filter(
            (pl.col("season") == TARGET_SEASON) & (pl.col("week") == week)
        ).sort(["gameday", "gametime", "game_id"])
        return [
            Matchup(
                game_id=row["game_id"],
                season=row["season"],
                week=row["week"],
                kickoff=_kickoff(row["gameday"], row["gametime"]),
                away_team_id=row["away_team"],
                home_team_id=row["home_team"],
                away_score=row["away_score"],
                home_score=row["home_score"],
                is_divisional=bool(row["div_game"]),
            )
            for row in rows.iter_rows(named=True)
        ]

    def previous_records(self) -> dict[str, Record]:
        return self._records_for(self._schedules.filter(pl.col("season") == PREVIOUS_SEASON))

    def current_records_before_week(self, week: int) -> dict[str, Record]:
        return self._records_for(
            self._schedules.filter((pl.col("season") == TARGET_SEASON) & (pl.col("week") < week))
        )

    def current_standings_before_week(self, week: int) -> dict[str, TeamStanding]:
        games = self._schedules.filter(
            (pl.col("season") == TARGET_SEASON) & (pl.col("week") < week)
        )
        point_differentials = {team_id: 0 for team_id in self.teams}
        completed = games.filter(
            pl.col("away_score").is_not_null() & pl.col("home_score").is_not_null()
        )
        for game in completed.iter_rows(named=True):
            margin = game["away_score"] - game["home_score"]
            point_differentials[game["away_team"]] += margin
            point_differentials[game["home_team"]] -= margin
        return build_standings(
            self.teams,
            self._records_for(games),
            point_differentials,
        )

    def _records_for(self, games: pl.DataFrame) -> dict[str, Record]:
        totals = {team_id: {"wins": 0, "losses": 0, "ties": 0} for team_id in self.teams}
        completed = games.filter(
            pl.col("away_score").is_not_null() & pl.col("home_score").is_not_null()
        )
        for game in completed.iter_rows(named=True):
            away = totals[game["away_team"]]
            home = totals[game["home_team"]]
            if game["away_score"] > game["home_score"]:
                away["wins"] += 1
                home["losses"] += 1
            elif game["home_score"] > game["away_score"]:
                home["wins"] += 1
                away["losses"] += 1
            else:
                away["ties"] += 1
                home["ties"] += 1
        return {team_id: Record(**values) for team_id, values in totals.items()}


class Repository:
    """Loads nflverse once, caches normalized Parquet, and serves in-memory data."""

    def __init__(
        self,
        cache_dir: Path = Path("data/processed"),
        *,
        require_32_teams: bool = True,
    ) -> None:
        self.cache_dir = cache_dir
        self.schedule_path = cache_dir / "schedules-2024-2025.parquet"
        self.team_path = cache_dir / "teams-2025.parquet"
        self.require_32_teams = require_32_teams

    @property
    def is_cached(self) -> bool:
        return self.schedule_path.exists() and self.team_path.exists()

    def load(self) -> SeasonData:
        return SeasonData.from_cache(
            self.schedule_path,
            self.team_path,
            require_32_teams=self.require_32_teams,
        )

    def get(self, *, force_refresh: bool = False) -> SeasonData:
        if self.is_cached and not force_refresh:
            return self.load()
        return self.refresh()

    def refresh(
        self,
        *,
        schedule_loader: Callable[[list[int]], pl.DataFrame] | None = None,
        team_loader: Callable[[], pl.DataFrame] | None = None,
    ) -> SeasonData:
        if schedule_loader is None or team_loader is None:
            import nflreadpy as nfl

            schedule_loader = schedule_loader or nfl.load_schedules
            team_loader = team_loader or nfl.load_teams

        data = SeasonData.from_frames(
            schedule_loader([PREVIOUS_SEASON, TARGET_SEASON]),
            team_loader(),
            require_32_teams=self.require_32_teams,
        )
        data.write_cache(self.schedule_path, self.team_path)
        return data
