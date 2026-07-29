from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from nflviewer.models import PlayerSpotlight
from nflviewer.records import ADJUSTED_RATE_MAX_WEEK, PRIOR_GAMES
from nflviewer.spotlights import build_player_spotlights
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
WEEKLY_ROSTER_COLUMNS = {
    "season",
    "week",
    "team",
    "espn_id",
    "status",
}
SPOTLIGHT_ROSTER_COLUMNS = WEEKLY_ROSTER_COLUMNS | {
    "full_name",
    "gsis_id",
    "position",
}
PLAYER_STAT_COLUMNS = {
    "fantasy_points_ppr",
    "passing_tds",
    "passing_yards",
    "player_display_name",
    "player_id",
    "position",
    "receiving_tds",
    "receiving_yards",
    "rushing_tds",
    "rushing_yards",
    "season",
    "season_type",
    "team",
    "week",
}


class DataValidationError(ValueError):
    """Raised when nflverse data cannot safely be used for rankings."""


@dataclass(frozen=True, slots=True)
class Record:
    wins: int = 0
    losses: int = 0
    ties: int = 0


@dataclass(frozen=True, slots=True)
class TeamMetrics:
    points_for_per_game: float
    points_allowed_per_game: float
    offense_percentile: float
    defense_percentile: float
    point_differential_percentile: float = 0.5


@dataclass(frozen=True, slots=True)
class _ScoringTotals:
    games: int = 0
    points_for: int = 0
    points_allowed: int = 0


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


def _empty_weekly_rosters() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "espn_id": pl.String,
            "full_name": pl.String,
            "gsis_id": pl.String,
            "position": pl.String,
            "season": pl.Int64,
            "status": pl.String,
            "team": pl.String,
            "week": pl.Int64,
        }
    )


def _empty_player_stats() -> pl.DataFrame:
    numeric_types = {
        "fantasy_points_ppr": pl.Float64,
        "passing_tds": pl.Int64,
        "passing_yards": pl.Int64,
        "receiving_tds": pl.Int64,
        "receiving_yards": pl.Int64,
        "rushing_tds": pl.Int64,
        "rushing_yards": pl.Int64,
        "season": pl.Int64,
        "week": pl.Int64,
    }
    return pl.DataFrame(
        schema={
            column: numeric_types.get(column, pl.String) for column in sorted(PLAYER_STAT_COLUMNS)
        }
    )


class SeasonData:
    """Validated, normalized 2024/2025 nflverse data held in memory."""

    def __init__(
        self,
        schedules: pl.DataFrame,
        team_frame: pl.DataFrame,
        weekly_rosters: pl.DataFrame,
        player_stats: pl.DataFrame,
        teams: dict[str, Team],
    ) -> None:
        self._schedules = schedules
        self._team_frame = team_frame
        self._weekly_rosters = weekly_rosters
        self._player_stats = player_stats
        self.teams = teams

    @classmethod
    def from_frames(
        cls,
        schedules: pl.DataFrame,
        teams: pl.DataFrame,
        *,
        weekly_rosters: pl.DataFrame | None = None,
        player_stats: pl.DataFrame | None = None,
        require_32_teams: bool = False,
    ) -> SeasonData:
        _require_columns(schedules, SCHEDULE_COLUMNS, "Schedule")
        _require_columns(teams, TEAM_COLUMNS, "Team")
        if weekly_rosters is not None:
            _require_columns(weekly_rosters, WEEKLY_ROSTER_COLUMNS, "Weekly roster")
        if player_stats is not None:
            _require_columns(player_stats, PLAYER_STAT_COLUMNS, "Player stat")

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
        normalized_weekly_rosters = _empty_weekly_rosters()
        if weekly_rosters is not None:
            missing_spotlight_columns = SPOTLIGHT_ROSTER_COLUMNS.difference(weekly_rosters.columns)
            weekly_rosters = weekly_rosters.with_columns(
                *(pl.lit(None).alias(column) for column in missing_spotlight_columns)
            )
            normalized_weekly_rosters = (
                weekly_rosters.select(sorted(SPOTLIGHT_ROSTER_COLUMNS))
                .with_columns(
                    pl.col("espn_id").cast(pl.String, strict=False),
                    pl.col("full_name").cast(pl.String, strict=False),
                    pl.col("gsis_id").cast(pl.String, strict=False),
                    pl.col("position").cast(pl.String, strict=False).str.to_uppercase(),
                    pl.col("season").cast(pl.Int64, strict=False),
                    pl.col("status").cast(pl.String, strict=False).str.to_uppercase(),
                    pl.col("team").cast(pl.String, strict=False).replace(TEAM_ALIASES),
                    pl.col("week").cast(pl.Int64, strict=False),
                )
                .filter(pl.col("season") == TARGET_SEASON)
            )
        normalized_player_stats = _empty_player_stats()
        if player_stats is not None:
            normalized_player_stats = (
                player_stats.select(sorted(PLAYER_STAT_COLUMNS))
                .with_columns(
                    pl.col("player_id").cast(pl.String, strict=False),
                    pl.col("position").cast(pl.String, strict=False).str.to_uppercase(),
                    pl.col("season").cast(pl.Int64, strict=False),
                    pl.col("team").cast(pl.String, strict=False).replace(TEAM_ALIASES),
                    pl.col("week").cast(pl.Int64, strict=False),
                )
                .filter(pl.col("season").is_in([PREVIOUS_SEASON, TARGET_SEASON]))
            )
        return cls(
            regular,
            filtered_team_frame,
            normalized_weekly_rosters,
            normalized_player_stats,
            metadata,
        )

    @classmethod
    def from_cache(
        cls,
        schedule_path: Path,
        team_path: Path,
        weekly_roster_path: Path | None = None,
        player_stats_path: Path | None = None,
        *,
        require_32_teams: bool = False,
    ) -> SeasonData:
        if not schedule_path.exists() or not team_path.exists():
            raise FileNotFoundError("NFL data cache is incomplete")
        return cls.from_frames(
            pl.read_parquet(schedule_path),
            pl.read_parquet(team_path),
            weekly_rosters=(
                pl.read_parquet(weekly_roster_path)
                if weekly_roster_path is not None and weekly_roster_path.exists()
                else None
            ),
            player_stats=(
                pl.read_parquet(player_stats_path)
                if player_stats_path is not None and player_stats_path.exists()
                else None
            ),
            require_32_teams=require_32_teams,
        )

    def write_cache(
        self,
        schedule_path: Path,
        team_path: Path,
        weekly_roster_path: Path | None = None,
        player_stats_path: Path | None = None,
    ) -> None:
        schedule_path.parent.mkdir(parents=True, exist_ok=True)
        team_path.parent.mkdir(parents=True, exist_ok=True)
        self._schedules.write_parquet(schedule_path)
        self._team_frame.write_parquet(team_path)
        if weekly_roster_path is not None:
            weekly_roster_path.parent.mkdir(parents=True, exist_ok=True)
            self._weekly_rosters.write_parquet(weekly_roster_path)
        if player_stats_path is not None:
            player_stats_path.parent.mkdir(parents=True, exist_ok=True)
            self._player_stats.write_parquet(player_stats_path)

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

    def unavailable_player_ids_for_matchup(
        self,
        week: int,
        away_team_id: str,
        home_team_id: str,
    ) -> list[str]:
        unavailable = self._weekly_rosters.filter(
            (pl.col("week") == week)
            & pl.col("team").is_in(
                [normalize_team_id(away_team_id), normalize_team_id(home_team_id)]
            )
            & (pl.col("status").fill_null("") != "ACT")
            & pl.col("espn_id").is_not_null()
        )
        return sorted(set(unavailable["espn_id"].to_list()))

    def player_team_codes(self) -> dict[str, str]:
        """Return conservative normalized player-name to latest roster-team mappings."""
        roster = (
            self._weekly_rosters.filter(
                pl.col("full_name").is_not_null() & pl.col("team").is_not_null()
            )
            .with_columns(
                pl.when(pl.col("gsis_id").fill_null("").str.strip_chars() != "")
                .then(pl.concat_str([pl.lit("gsis:"), pl.col("gsis_id")]))
                .when(pl.col("espn_id").fill_null("").str.strip_chars() != "")
                .then(pl.concat_str([pl.lit("espn:"), pl.col("espn_id")]))
                .otherwise(None)
                .alias("player_id"),
                pl.col("full_name")
                .str.to_lowercase()
                .str.replace_all(r"[^a-z0-9]+", " ")
                .str.strip_chars()
                .alias("player_name")
            )
            .filter(pl.col("player_id").is_not_null() & (pl.col("player_name") != ""))
        )
        if roster.is_empty():
            return {}

        latest_week = roster.group_by("player_id").agg(pl.col("week").max().alias("week"))
        latest_roster = roster.join(latest_week, on=["player_id", "week"], how="inner")
        unambiguous_players = (
            latest_roster.group_by("player_id")
            .agg(pl.col("team").n_unique().alias("team_count"))
            .filter(pl.col("team_count") == 1)
            .select("player_id")
        )
        unambiguous = (
            latest_roster.join(unambiguous_players, on="player_id", how="inner")
            .group_by("player_name")
            .agg(
                pl.col("player_id").n_unique().alias("player_count"),
                pl.col("team").n_unique().alias("team_count"),
                pl.col("team").first().alias("team"),
            )
            .filter((pl.col("player_count") == 1) & (pl.col("team_count") == 1))
        )
        return dict(unambiguous.select("player_name", "team").iter_rows())

    def player_spotlights_before_week(
        self,
        week: int,
        team_ids: list[str],
    ) -> dict[str, PlayerSpotlight]:
        return build_player_spotlights(
            self._weekly_rosters,
            self._player_stats,
            week=week,
            team_ids=team_ids,
        )

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

    def team_metrics_before_week(self, week: int) -> dict[str, TeamMetrics]:
        previous = self._scoring_totals(self._schedules.filter(pl.col("season") == PREVIOUS_SEASON))
        current = self._scoring_totals(
            self._schedules.filter((pl.col("season") == TARGET_SEASON) & (pl.col("week") < week))
        )

        scoring_rates: dict[str, tuple[float, float]] = {}
        for team_id in self.teams:
            current_team = current[team_id]
            previous_team = previous[team_id]
            if week <= ADJUSTED_RATE_MAX_WEEK and previous_team.games:
                previous_for_rate = previous_team.points_for / previous_team.games
                previous_allowed_rate = previous_team.points_allowed / previous_team.games
                games = PRIOR_GAMES + current_team.games
                points_for_rate = (
                    PRIOR_GAMES * previous_for_rate + current_team.points_for
                ) / games
                points_allowed_rate = (
                    PRIOR_GAMES * previous_allowed_rate + current_team.points_allowed
                ) / games
            elif current_team.games:
                points_for_rate = current_team.points_for / current_team.games
                points_allowed_rate = current_team.points_allowed / current_team.games
            else:
                points_for_rate = 0.0
                points_allowed_rate = 0.0
            scoring_rates[team_id] = (points_for_rate, points_allowed_rate)

        offense_values = [rates[0] for rates in scoring_rates.values()]
        defense_values = [rates[1] for rates in scoring_rates.values()]
        differential_values = [
            points_for - points_allowed for points_for, points_allowed in scoring_rates.values()
        ]
        return {
            team_id: TeamMetrics(
                points_for_per_game=rates[0],
                points_allowed_per_game=rates[1],
                offense_percentile=_percentile(rates[0], offense_values),
                defense_percentile=_percentile(
                    rates[1],
                    defense_values,
                    higher_is_better=False,
                ),
                point_differential_percentile=_percentile(
                    rates[0] - rates[1],
                    differential_values,
                ),
            )
            for team_id, rates in scoring_rates.items()
        }

    def _scoring_totals(self, games: pl.DataFrame) -> dict[str, _ScoringTotals]:
        totals = {
            team_id: {"games": 0, "points_for": 0, "points_allowed": 0} for team_id in self.teams
        }
        completed = games.filter(
            pl.col("away_score").is_not_null() & pl.col("home_score").is_not_null()
        )
        for game in completed.iter_rows(named=True):
            away = totals[game["away_team"]]
            home = totals[game["home_team"]]
            away["games"] += 1
            home["games"] += 1
            away["points_for"] += game["away_score"]
            away["points_allowed"] += game["home_score"]
            home["points_for"] += game["home_score"]
            home["points_allowed"] += game["away_score"]
        return {team_id: _ScoringTotals(**values) for team_id, values in totals.items()}

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


def _percentile(
    value: float,
    values: list[float],
    *,
    higher_is_better: bool = True,
) -> float:
    if len(values) <= 1:
        return 0.5
    worse = sum(
        candidate < value if higher_is_better else candidate > value for candidate in values
    )
    ties = sum(candidate == value for candidate in values) - 1
    return (worse + 0.5 * ties) / (len(values) - 1)


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
        self.weekly_roster_path = cache_dir / "rosters-weekly-2025-v2.parquet"
        self.player_stats_path = cache_dir / "player-stats-2024-2025.parquet"
        self.require_32_teams = require_32_teams

    @property
    def is_cached(self) -> bool:
        return (
            self.schedule_path.exists()
            and self.team_path.exists()
            and self.weekly_roster_path.exists()
            and self.player_stats_path.exists()
        )

    def load(self) -> SeasonData:
        return SeasonData.from_cache(
            self.schedule_path,
            self.team_path,
            self.weekly_roster_path,
            self.player_stats_path,
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
        weekly_roster_loader: Callable[[list[int]], pl.DataFrame] | None = None,
        player_stat_loader: Callable[..., pl.DataFrame] | None = None,
    ) -> SeasonData:
        use_production_loaders = schedule_loader is None and team_loader is None
        if schedule_loader is None or team_loader is None:
            import nflreadpy as nfl

            schedule_loader = schedule_loader or nfl.load_schedules
            team_loader = team_loader or nfl.load_teams
            if use_production_loaders:
                weekly_roster_loader = weekly_roster_loader or nfl.load_rosters_weekly
                player_stat_loader = player_stat_loader or nfl.load_player_stats

        data = SeasonData.from_frames(
            schedule_loader([PREVIOUS_SEASON, TARGET_SEASON]),
            team_loader(),
            weekly_rosters=(
                weekly_roster_loader([TARGET_SEASON]) if weekly_roster_loader is not None else None
            ),
            player_stats=(
                player_stat_loader(
                    [PREVIOUS_SEASON, TARGET_SEASON],
                    summary_level="week",
                )
                if player_stat_loader is not None
                else None
            ),
            require_32_teams=self.require_32_teams,
        )
        data.write_cache(
            self.schedule_path,
            self.team_path,
            self.weekly_roster_path,
            self.player_stats_path,
        )
        return data
