import polars as pl

from nflviewer.spotlights import build_player_spotlights


def roster_rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "season": 2025,
                "week": 4,
                "team": "LAC",
                "espn_id": "1",
                "gsis_id": "injured-qb",
                "status": "RES",
                "full_name": "Injured Quarterback",
                "position": "QB",
                "headshot_url": "https://example.test/injured.png",
            },
            {
                "season": 2025,
                "week": 4,
                "team": "LAC",
                "espn_id": "2",
                "gsis_id": "active-wr",
                "status": "ACT",
                "full_name": "Active Receiver",
                "position": "WR",
                "headshot_url": "https://example.test/receiver.png",
            },
            {
                "season": 2025,
                "week": 4,
                "team": "DEN",
                "espn_id": "3",
                "gsis_id": "active-qb",
                "status": "ACT",
                "full_name": "Active Quarterback",
                "position": "QB",
                "headshot_url": "https://example.test/quarterback.png",
            },
        ]
    )


def stat_row(
    player_id: str,
    name: str,
    position: str,
    team: str,
    week: int,
    *,
    fantasy_points: float,
    passing_yards: int = 0,
    passing_tds: int = 0,
    rushing_yards: int = 0,
    rushing_tds: int = 0,
    receiving_yards: int = 0,
    receiving_tds: int = 0,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_display_name": name,
        "position": position,
        "headshot_url": f"https://example.test/{player_id}.png",
        "season": 2025,
        "week": week,
        "season_type": "REG",
        "team": team,
        "passing_yards": passing_yards,
        "passing_tds": passing_tds,
        "rushing_yards": rushing_yards,
        "rushing_tds": rushing_tds,
        "receiving_yards": receiving_yards,
        "receiving_tds": receiving_tds,
        "fantasy_points_ppr": fantasy_points,
    }


def test_selects_one_active_player_per_team_without_future_week_stats() -> None:
    stats = pl.DataFrame(
        [
            stat_row(
                "injured-qb",
                "Injured Quarterback",
                "QB",
                "LAC",
                week,
                fantasy_points=50,
                passing_yards=400,
                passing_tds=4,
            )
            for week in (1, 2, 3)
        ]
        + [
            stat_row(
                "active-wr",
                "Active Receiver",
                "WR",
                "LAC",
                week,
                fantasy_points=20,
                receiving_yards=yards,
                receiving_tds=1 if week < 3 else 0,
            )
            for week, yards in ((1, 100), (2, 120), (3, 80))
        ]
        + [
            stat_row(
                "active-wr",
                "Active Receiver",
                "WR",
                "LAC",
                4,
                fantasy_points=80,
                receiving_yards=500,
                receiving_tds=4,
            ),
            *[
                stat_row(
                    f"peer-wr-{index}",
                    f"Peer Receiver {index}",
                    "WR",
                    "OTH",
                    3,
                    fantasy_points=10,
                    receiving_yards=yards,
                )
                for index, yards in enumerate((450, 350), 1)
            ],
            *[
                stat_row(
                    "active-qb",
                    "Active Quarterback",
                    "QB",
                    "DEN",
                    week,
                    fantasy_points=25,
                    passing_yards=250,
                    passing_tds=2,
                )
                for week in (1, 2, 3)
            ],
        ]
    )

    spotlights = build_player_spotlights(roster_rows(), stats, week=4, team_ids=["LAC", "DEN"])

    assert set(spotlights) == {"LAC", "DEN"}
    assert spotlights["LAC"].name == "Active Receiver"
    assert spotlights["LAC"].details == [
        "300 receiving yards this season",
        "2 receiving TDs this season",
        "Ranked 3rd among WRs in receiving yards",
    ]
    assert spotlights["DEN"].name == "Active Quarterback"
    assert spotlights["DEN"].details == [
        "750 passing yards this season",
        "6 passing TDs this season",
        "Ranked 2nd among QBs in passing yards",
    ]


def test_uses_last_week_detail_when_player_is_outside_top_five() -> None:
    stats = pl.DataFrame(
        [
            stat_row(
                "active-wr",
                "Active Receiver",
                "WR",
                "LAC",
                week,
                fantasy_points=20,
                receiving_yards=yards,
                receiving_tds=1 if week < 3 else 0,
            )
            for week, yards in ((1, 100), (2, 120), (3, 80))
        ]
        + [
            stat_row(
                f"peer-wr-{index}",
                f"Peer Receiver {index}",
                "WR",
                "OTH",
                3,
                fantasy_points=10,
                receiving_yards=yards,
            )
            for index, yards in enumerate((700, 650, 600, 550, 500), 1)
        ]
    )

    spotlight = build_player_spotlights(
        roster_rows(),
        stats,
        week=4,
        team_ids=["LAC"],
    )["LAC"]

    assert spotlight.details == [
        "300 receiving yards this season",
        "2 receiving TDs this season",
        "80 receiving yards last week",
    ]
