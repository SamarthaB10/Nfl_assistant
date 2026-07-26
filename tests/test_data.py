from pathlib import Path

import polars as pl
import pytest

from nflviewer.data import DataValidationError, Record, Repository, SeasonData, normalize_team_id
from nflviewer.sync_data import build_parser


def schedule_rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "game_id": "2024_01_LA_JAC",
                "season": 2024,
                "game_type": "REG",
                "week": 1,
                "gameday": "2024-09-08",
                "gametime": "13:00",
                "away_team": "LA",
                "away_score": 21,
                "home_team": "JAC",
                "home_score": 21,
                "div_game": 0,
            },
            {
                "game_id": "2024_18_JAC_LA",
                "season": 2024,
                "game_type": "REG",
                "week": 18,
                "gameday": "2025-01-05",
                "gametime": "16:25",
                "away_team": "JAC",
                "away_score": 10,
                "home_team": "LA",
                "home_score": 24,
                "div_game": 0,
            },
            {
                "game_id": "2025_01_LA_JAC",
                "season": 2025,
                "game_type": "REG",
                "week": 1,
                "gameday": "2025-09-07",
                "gametime": "13:00",
                "away_team": "LA",
                "away_score": 17,
                "home_team": "JAC",
                "home_score": 14,
                "div_game": 0,
            },
            {
                "game_id": "2025_03_JAC_LA",
                "season": 2025,
                "game_type": "REG",
                "week": 3,
                "gameday": "2025-09-21",
                "gametime": "20:20",
                "away_team": "JAC",
                "away_score": None,
                "home_team": "LA",
                "home_score": None,
                "div_game": 0,
            },
            {
                "game_id": "2025_WC_JAC_LA",
                "season": 2025,
                "game_type": "WC",
                "week": 1,
                "gameday": "2026-01-10",
                "gametime": "16:30",
                "away_team": "JAC",
                "away_score": None,
                "home_team": "LA",
                "home_score": None,
                "div_game": 0,
            },
        ]
    )


def team_rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "team_abbr": "LA",
                "team_name": "Los Angeles Rams",
                "team_conf": "NFC",
                "team_division": "NFC West",
                "team_logo_espn": "https://example.test/lar.png",
            },
            {
                "team_abbr": "JAC",
                "team_name": "Jacksonville Jaguars",
                "team_conf": "AFC",
                "team_division": "AFC South",
                "team_logo_espn": "https://example.test/jax.png",
            },
            {
                "team_abbr": "OAK",
                "team_name": "Oakland Raiders",
                "team_conf": "AFC",
                "team_division": "AFC West",
                "team_logo_espn": None,
            },
        ]
    )


def test_normalizes_known_nflverse_team_aliases() -> None:
    assert normalize_team_id("LA") == "LAR"
    assert normalize_team_id("JAC") == "JAX"
    assert normalize_team_id("BUF") == "BUF"


def test_builds_target_week_matchups_and_filters_postseason() -> None:
    data = SeasonData.from_frames(schedule_rows(), team_rows())

    matchups = data.matchups_for_week(3)

    assert len(matchups) == 1
    assert matchups[0].game_id == "2025_03_JAC_LA"
    assert matchups[0].away_team_id == "JAX"
    assert matchups[0].home_team_id == "LAR"
    assert matchups[0].away_score is None
    assert set(data.teams) == {"JAX", "LAR"}


def test_calculates_previous_and_preweek_records_without_future_leakage() -> None:
    data = SeasonData.from_frames(schedule_rows(), team_rows())

    assert data.previous_records() == {
        "JAX": Record(wins=0, losses=1, ties=1),
        "LAR": Record(wins=1, losses=0, ties=1),
    }
    assert data.current_records_before_week(1) == {
        "JAX": Record(),
        "LAR": Record(),
    }
    assert data.current_records_before_week(3) == {
        "JAX": Record(losses=1),
        "LAR": Record(wins=1),
    }


def test_builds_standings_from_only_games_before_the_selected_week() -> None:
    data = SeasonData.from_frames(schedule_rows(), team_rows())

    week_one = data.current_standings_before_week(1)
    week_three = data.current_standings_before_week(3)

    assert week_one["JAX"].record.wins == 0
    assert week_one["JAX"].point_differential == 0
    assert week_three["JAX"].record.losses == 1
    assert week_three["JAX"].point_differential == -3
    assert week_three["LAR"].record.wins == 1
    assert week_three["LAR"].point_differential == 3


def test_builds_weekly_scoring_metrics_with_early_season_prior() -> None:
    data = SeasonData.from_frames(schedule_rows(), team_rows())

    week_one = data.team_metrics_before_week(1)
    week_three = data.team_metrics_before_week(3)

    assert week_one["JAX"].points_for_per_game == pytest.approx(15.5)
    assert week_one["JAX"].points_allowed_per_game == pytest.approx(22.5)
    assert week_one["JAX"].offense_percentile == 0
    assert week_one["JAX"].defense_percentile == 0
    assert week_one["JAX"].point_differential_percentile == 0
    assert week_one["LAR"].offense_percentile == 1
    assert week_one["LAR"].defense_percentile == 1
    assert week_one["LAR"].point_differential_percentile == 1
    assert week_three["JAX"].points_for_per_game == pytest.approx(15.2)
    assert week_three["JAX"].points_allowed_per_game == pytest.approx(21.4)


def test_weekly_scoring_metrics_exclude_target_week_results() -> None:
    schedules = schedule_rows().with_columns(
        pl.when(pl.col("game_id") == "2025_03_JAC_LA")
        .then(50)
        .otherwise(pl.col("away_score"))
        .alias("away_score"),
        pl.when(pl.col("game_id") == "2025_03_JAC_LA")
        .then(0)
        .otherwise(pl.col("home_score"))
        .alias("home_score"),
    )
    data = SeasonData.from_frames(schedules, team_rows())

    metrics = data.team_metrics_before_week(3)

    assert metrics["JAX"].points_for_per_game == pytest.approx(15.2)
    assert metrics["LAR"].points_allowed_per_game == pytest.approx(15.2)


def test_scoring_metrics_use_only_current_season_after_week_five() -> None:
    data = SeasonData.from_frames(schedule_rows(), team_rows())

    metrics = data.team_metrics_before_week(6)

    assert metrics["JAX"].points_for_per_game == 14
    assert metrics["JAX"].points_allowed_per_game == 17
    assert metrics["LAR"].points_for_per_game == 17
    assert metrics["LAR"].points_allowed_per_game == 14


def test_missing_completed_game_does_not_create_a_record_or_bye() -> None:
    schedules = schedule_rows().with_columns(
        pl.when(pl.col("game_id") == "2025_01_LA_JAC")
        .then(None)
        .otherwise(pl.col("away_score"))
        .alias("away_score"),
        pl.when(pl.col("game_id") == "2025_01_LA_JAC")
        .then(None)
        .otherwise(pl.col("home_score"))
        .alias("home_score"),
    )
    data = SeasonData.from_frames(schedules, team_rows())

    assert data.current_records_before_week(3) == {
        "JAX": Record(),
        "LAR": Record(),
    }
    assert len(data.matchups_for_week(3)) == 1


def test_rejects_a_game_with_only_one_score() -> None:
    schedules = schedule_rows().with_columns(
        pl.when(pl.col("game_id") == "2025_01_LA_JAC")
        .then(None)
        .otherwise(pl.col("away_score"))
        .alias("away_score")
    )

    with pytest.raises(DataValidationError, match="exactly one score"):
        SeasonData.from_frames(schedules, team_rows())


def test_rejects_duplicate_game_ids() -> None:
    schedules = pl.concat([schedule_rows(), schedule_rows().slice(0, 1)])

    with pytest.raises(DataValidationError, match="Duplicate game_id"):
        SeasonData.from_frames(schedules, team_rows())


def test_parquet_round_trip_uses_local_cache(tmp_path: Path) -> None:
    data = SeasonData.from_frames(schedule_rows(), team_rows())
    schedule_path = tmp_path / "schedules-2024-2025.parquet"
    team_path = tmp_path / "teams-2025.parquet"

    data.write_cache(schedule_path, team_path)
    restored = SeasonData.from_cache(schedule_path, team_path)

    assert restored.matchups_for_week(3) == data.matchups_for_week(3)
    assert restored.previous_records() == data.previous_records()


def test_repository_refreshes_and_then_loads_local_parquet(tmp_path: Path) -> None:
    repository = Repository(tmp_path, require_32_teams=False)

    refreshed = repository.refresh(
        schedule_loader=lambda _: schedule_rows(),
        team_loader=team_rows,
    )
    loaded = repository.load()

    assert repository.is_cached
    assert refreshed.matchups_for_week(3) == loaded.matchups_for_week(3)


def test_repository_requires_32_teams_by_default(tmp_path: Path) -> None:
    repository = Repository(tmp_path)

    with pytest.raises(DataValidationError, match="Expected 32 current teams"):
        repository.refresh(
            schedule_loader=lambda _: schedule_rows(),
            team_loader=team_rows,
        )


def test_sync_cli_accepts_force_refresh_and_cache_directory(tmp_path: Path) -> None:
    args = build_parser().parse_args(["--force", "--cache-dir", str(tmp_path)])

    assert args.force is True
    assert args.cache_dir == tmp_path
