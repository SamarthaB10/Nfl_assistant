from __future__ import annotations

from collections.abc import Sequence

import polars as pl

from nflviewer.models import PlayerSpotlight

TARGET_SEASON = 2025
PREVIOUS_SEASON = 2024
ELIGIBLE_POSITIONS = {"QB", "RB", "FB", "WR", "TE"}
POSITION_PRIORITY = {"QB": 5, "RB": 4, "WR": 3, "TE": 2, "FB": 1}


def _ordinal(value: int) -> str:
    suffix = "th" if 10 < value % 100 < 14 else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def _position_stats(position: str) -> tuple[str, str, str, str]:
    if position == "QB":
        return ("passing_yards", "passing yards", "passing_tds", "passing TDs")
    if position in {"RB", "FB"}:
        return ("rushing_yards", "rushing yards", "total_tds", "total TDs")
    return ("receiving_yards", "receiving yards", "receiving_tds", "receiving TDs")


def _player_details(
    player: dict[str, object],
    last_game: dict[str, object] | None,
    peer_rows: list[dict[str, object]],
    *,
    source_season: int,
    selected_week: int,
) -> list[str]:
    position = str(player["position"])
    primary_field, primary_label, secondary_field, secondary_label = _position_stats(position)
    primary_value = int(player[primary_field] or 0)
    secondary_value = int(player[secondary_field] or 0)
    season_label = "this season" if source_season == TARGET_SEASON else "in 2024"
    details = [
        f"{primary_value:,} {primary_label} {season_label}",
        f"{secondary_value:,} {secondary_label} {season_label}",
    ]

    rank = 1 + sum(int(peer[primary_field] or 0) > primary_value for peer in peer_rows)
    if primary_value > 0 and rank <= 5:
        details.append(f"Ranked {_ordinal(rank)} among {position}s in {primary_label}")
    elif (
        source_season == TARGET_SEASON
        and last_game is not None
        and int(last_game["week"]) == selected_week - 1
        and int(last_game[primary_field] or 0) > 0
    ):
        details.append(f"{int(last_game[primary_field]):,} {primary_label} last week")
    return details


def _empty_spotlight_stats() -> dict[str, object]:
    return {
        "fantasy_points_ppr": 0.0,
        "passing_yards": 0,
        "passing_tds": 0,
        "rushing_yards": 0,
        "rushing_tds": 0,
        "receiving_yards": 0,
        "receiving_tds": 0,
        "total_tds": 0,
    }


def build_player_spotlights(
    weekly_rosters: pl.DataFrame,
    player_stats: pl.DataFrame,
    *,
    week: int,
    team_ids: Sequence[str],
) -> dict[str, PlayerSpotlight]:
    current_history = player_stats.filter(
        (pl.col("season") == TARGET_SEASON)
        & (pl.col("season_type") == "REG")
        & (pl.col("week") < week)
    )
    source_season = TARGET_SEASON
    history = current_history
    if history.is_empty():
        source_season = PREVIOUS_SEASON
        history = player_stats.filter(
            (pl.col("season") == PREVIOUS_SEASON) & (pl.col("season_type") == "REG")
        )

    numeric_fields = [
        "fantasy_points_ppr",
        "passing_yards",
        "passing_tds",
        "rushing_yards",
        "rushing_tds",
        "receiving_yards",
        "receiving_tds",
    ]
    summary = (
        history.group_by("player_id")
        .agg(
            pl.col("player_display_name").drop_nulls().first(),
            pl.col("position").drop_nulls().last(),
            *(pl.col(field).fill_null(0).sum().alias(field) for field in numeric_fields),
        )
        .with_columns((pl.col("rushing_tds") + pl.col("receiving_tds")).alias("total_tds"))
    )
    stats_by_id = {str(row["player_id"]): row for row in summary.iter_rows(named=True)}
    last_games = {
        str(row["player_id"]): row
        for row in history.sort(["season", "week"])
        .unique(subset=["player_id"], keep="last")
        .iter_rows(named=True)
    }
    peer_rows: dict[str, list[dict[str, object]]] = {}
    for row in summary.iter_rows(named=True):
        peer_rows.setdefault(str(row["position"]), []).append(row)

    active = weekly_rosters.filter(
        (pl.col("season") == TARGET_SEASON)
        & (pl.col("week") == week)
        & pl.col("team").is_in(team_ids)
        & (pl.col("status") == "ACT")
        & pl.col("espn_id").is_not_null()
        & pl.col("gsis_id").is_not_null()
        & pl.col("position").is_in(ELIGIBLE_POSITIONS)
    )
    spotlights: dict[str, PlayerSpotlight] = {}
    for team_id in team_ids:
        candidates: list[tuple[tuple[float, ...], dict[str, object], dict[str, object]]] = []
        for roster in active.filter(pl.col("team") == team_id).iter_rows(named=True):
            player_id = str(roster["gsis_id"])
            stats = stats_by_id.get(player_id, _empty_spotlight_stats())
            primary_field = _position_stats(str(roster["position"]))[0]
            score = (
                1.0 if player_id in stats_by_id else 0.0,
                float(stats["fantasy_points_ppr"] or 0),
                float(stats[primary_field] or 0),
                float(POSITION_PRIORITY.get(str(roster["position"]), 0)),
            )
            candidates.append((score, roster, stats))
        if not candidates:
            continue

        _, roster, stats = max(candidates, key=lambda candidate: candidate[0])
        player_id = str(roster["gsis_id"])
        position = str(roster["position"])
        espn_id = roster["espn_id"]
        name = str(roster["full_name"] or stats.get("player_display_name") or player_id)
        details = _player_details(
            {**stats, "position": position},
            last_games.get(player_id),
            peer_rows.get(position, []),
            source_season=source_season,
            selected_week=week,
        )
        spotlights[team_id] = PlayerSpotlight(
            player_id=player_id,
            team_id=team_id,
            name=name,
            position=position,
            image_url=(f"https://a.espncdn.com/i/headshots/nfl/players/full/{espn_id}.png"),
            profile_url=f"https://www.espn.com/nfl/player/_/id/{espn_id}",
            details=details,
        )
    return spotlights
