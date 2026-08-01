from collections.abc import Callable
from contextlib import AbstractContextManager

import polars as pl
import pytest
from fastapi.testclient import TestClient

from nflviewer.app import create_app
from nflviewer.data import SeasonData
from nflviewer.headlines import HeadlineRepository


def season_data() -> SeasonData:
    schedules = pl.DataFrame(
        [
            {
                "game_id": "2024_01_BUF_NE",
                "season": 2024,
                "game_type": "REG",
                "week": 1,
                "gameday": "2024-09-08",
                "gametime": "13:00",
                "away_team": "BUF",
                "away_score": 24,
                "home_team": "NE",
                "home_score": 17,
                "div_game": 1,
            },
            {
                "game_id": "2024_01_DAL_NYG",
                "season": 2024,
                "game_type": "REG",
                "week": 1,
                "gameday": "2024-09-08",
                "gametime": "16:25",
                "away_team": "DAL",
                "away_score": 28,
                "home_team": "NYG",
                "home_score": 14,
                "div_game": 1,
            },
            {
                "game_id": "2025_01_NE_BUF",
                "season": 2025,
                "game_type": "REG",
                "week": 1,
                "gameday": "2025-09-07",
                "gametime": "13:00",
                "away_team": "NE",
                "away_score": 14,
                "home_team": "BUF",
                "home_score": 28,
                "div_game": 1,
            },
            {
                "game_id": "2025_01_NYG_DAL",
                "season": 2025,
                "game_type": "REG",
                "week": 1,
                "gameday": "2025-09-07",
                "gametime": "20:20",
                "away_team": "NYG",
                "away_score": 10,
                "home_team": "DAL",
                "home_score": 24,
                "div_game": 1,
            },
            {
                "game_id": "2025_02_BUF_DAL",
                "season": 2025,
                "game_type": "REG",
                "week": 2,
                "gameday": "2025-09-14",
                "gametime": "16:25",
                "away_team": "BUF",
                "away_score": None,
                "home_team": "DAL",
                "home_score": None,
                "div_game": 0,
            },
            {
                "game_id": "2026_01_NE_BUF",
                "season": 2026,
                "game_type": "REG",
                "week": 1,
                "gameday": "2026-09-09",
                "gametime": "20:20",
                "away_team": "NE",
                "away_score": None,
                "home_team": "BUF",
                "home_score": None,
                "div_game": 1,
            },
            {
                "game_id": "2026_01_NYG_DAL",
                "season": 2026,
                "game_type": "REG",
                "week": 1,
                "gameday": "2026-09-13",
                "gametime": "20:20",
                "away_team": "NYG",
                "away_score": None,
                "home_team": "DAL",
                "home_score": None,
                "div_game": 1,
            },
        ]
    )
    teams = pl.DataFrame(
        [
            {
                "team_abbr": team_id,
                "team_name": team_name,
                "team_conf": conference,
                "team_division": division,
                "team_logo_espn": (
                    f"https://a.espncdn.com/i/teamlogos/nfl/500/{team_id.lower()}.png"
                ),
            }
            for team_id, team_name, conference, division in [
                ("BUF", "Buffalo Bills", "AFC", "AFC East"),
                ("NE", "New England Patriots", "AFC", "AFC East"),
                ("DAL", "Dallas Cowboys", "NFC", "NFC East"),
                ("NYG", "New York Giants", "NFC", "NFC East"),
            ]
        ]
    )
    weekly_rosters = pl.DataFrame(
        [
            {
                "season": 2025,
                "week": 2,
                "team": "BUF",
                "espn_id": 1234567,
                "status": "RES",
            },
            {
                "season": 2025,
                "week": 2,
                "team": "DAL",
                "espn_id": 7654321,
                "status": "ACT",
            },
        ]
    )
    return SeasonData.from_frames(schedules, teams, weekly_rosters=weekly_rosters)


class StubRepository:
    def __init__(self, loader: Callable[[], SeasonData]) -> None:
        self.loader = loader

    def get(self) -> SeasonData:
        return self.loader()


def client_for(loader: Callable[[], SeasonData]) -> AbstractContextManager[TestClient]:
    return TestClient(
        create_app(
            StubRepository(loader),
            headline_repository=HeadlineRepository(),
        )
    )


def test_health_reports_loaded_data() -> None:
    with client_for(season_data) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["dataLoaded"] is True


def test_health_keeps_rankings_available_when_player_team_map_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_player_team_map(_: SeasonData) -> dict[str, str]:
        raise ValueError("invalid roster mapping")

    monkeypatch.setattr(SeasonData, "player_team_codes", fail_player_team_map)

    with client_for(season_data) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["dataLoaded"] is True


def test_openapi_uses_leaguewatch_product_name() -> None:
    with client_for(season_data) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "LeagueWatch API"


def test_rankings_returns_all_games_in_rank_order() -> None:
    with client_for(season_data) as client:
        response = client.get("/api/v1/rankings", params={"week": 1})

    assert response.status_code == 200
    assert response.json() == [
        {
            "matchup": "New England Patriots vs Buffalo Bills",
            "records": {"NE": "0-0", "BUF": "0-0"},
            "logos": {
                "NE": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png",
                "BUF": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png",
            },
            "finalScores": {"NE": 14, "BUF": 28},
            "score": 3.73,
            "reasons": ["Divisional matchup"],
            "unavailablePlayerIds": [],
            "playersToWatch": [],
        },
        {
            "matchup": "New York Giants vs Dallas Cowboys",
            "records": {"NYG": "0-0", "DAL": "0-0"},
            "logos": {
                "NYG": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png",
                "DAL": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png",
            },
            "finalScores": {"NYG": 10, "DAL": 24},
            "score": 1.81,
            "reasons": [
                "Divisional matchup",
                "Team profiles indicate elevated blowout risk",
            ],
            "unavailablePlayerIds": [],
            "playersToWatch": [],
        },
    ]


def test_2026_schedule_returns_games_without_scores_or_rankings() -> None:
    with client_for(season_data) as client:
        response = client.get("/api/v1/rankings", params={"season": 2026, "week": 1})

    assert response.status_code == 200
    games = response.json()
    assert [game["gameId"] for game in games] == [
        "2026_01_NE_BUF",
        "2026_01_NYG_DAL",
    ]
    assert games[0]["matchup"] == "New England Patriots vs Buffalo Bills"
    assert games[0]["records"] == {"NE": "Scheduled", "BUF": "Scheduled"}
    assert games[0]["kickoff"] == "2026-09-10T00:20:00Z"
    assert "score" not in games[0]
    assert "reasons" not in games[0]


def test_rankings_applies_top_after_scoring_all_games() -> None:
    with client_for(season_data) as client:
        response = client.get(
            "/api/v1/rankings",
            params={"season": 2025, "week": 1, "top": 1},
        )

    assert response.status_code == 200
    assert response.json() == [
        {
            "matchup": "New England Patriots vs Buffalo Bills",
            "records": {"NE": "0-0", "BUF": "0-0"},
            "logos": {
                "NE": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png",
                "BUF": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png",
            },
            "finalScores": {"NE": 14, "BUF": 28},
            "score": 3.73,
            "reasons": ["Divisional matchup"],
            "unavailablePlayerIds": [],
            "playersToWatch": [],
        }
    ]


def test_rankings_returns_bottom_games_worst_first() -> None:
    with client_for(season_data) as client:
        response = client.get(
            "/api/v1/rankings",
            params={"season": 2025, "week": 1, "bottom": 1},
        )

    assert response.status_code == 200
    assert response.json() == [
        {
            "matchup": "New York Giants vs Dallas Cowboys",
            "records": {"NYG": "0-0", "DAL": "0-0"},
            "logos": {
                "NYG": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png",
                "DAL": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png",
            },
            "finalScores": {"NYG": 10, "DAL": 24},
            "score": 1.81,
            "reasons": [
                "Divisional matchup",
                "Team profiles indicate elevated blowout risk",
            ],
            "unavailablePlayerIds": [],
            "playersToWatch": [],
        }
    ]


def test_rankings_rejects_top_and_bottom_together() -> None:
    with client_for(season_data) as client:
        response = client.get(
            "/api/v1/rankings",
            params={"week": 1, "top": 1, "bottom": 1},
        )

    assert response.status_code == 422


def test_rankings_show_each_current_record_before_the_selected_week() -> None:
    with client_for(season_data) as client:
        response = client.get("/api/v1/rankings", params={"week": 2})

    assert response.status_code == 200
    assert response.json()[0]["records"] == {"BUF": "1-0", "DAL": "1-0"}
    assert response.json()[0]["finalScores"] == {}
    assert response.json()[0]["unavailablePlayerIds"] == ["1234567"]


def test_rankings_include_final_scores_for_completed_games() -> None:
    with client_for(season_data) as client:
        response = client.get("/api/v1/rankings", params={"week": 1})

    assert response.status_code == 200
    games_by_matchup = {game["matchup"]: game for game in response.json()}
    assert games_by_matchup["New England Patriots vs Buffalo Bills"]["finalScores"] == {
        "NE": 14,
        "BUF": 28,
    }
    assert games_by_matchup["New York Giants vs Dallas Cowboys"]["finalScores"] == {
        "NYG": 10,
        "DAL": 24,
    }


def test_rankings_adds_cached_headline_without_changing_score(tmp_path) -> None:
    path = tmp_path / "headlines.json"
    path.write_text(
        """
        [
          {
            "gameId": "2025_01_NE_BUF",
            "headline": "Patriots and Bills renew AFC East rivalry",
            "publishedAt": "2025-09-05T12:00:00Z",
            "url": "https://www.espn.com/nfl/story/_/id/1/example"
          }
        ]
        """,
        encoding="utf-8",
    )
    application = create_app(
        StubRepository(season_data),
        headline_repository=HeadlineRepository(path),
    )

    with TestClient(application) as client:
        response = client.get("/api/v1/rankings", params={"week": 1, "top": 1})

    assert response.status_code == 200
    assert response.json()[0]["score"] == 3.73
    assert response.json()[0]["logos"] == {
        "NE": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png",
        "BUF": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png",
    }
    assert response.json()[0]["reasons"] == [
        "Divisional matchup",
        "Headline: Patriots and Bills renew AFC East rivalry",
    ]


def test_rankings_validates_query_fields() -> None:
    with client_for(season_data) as client:
        missing_week = client.get("/api/v1/rankings")
        invalid_week = client.get("/api/v1/rankings", params={"week": 19})
        invalid_top = client.get("/api/v1/rankings", params={"week": 1, "top": 0})
        invalid_season = client.get(
            "/api/v1/rankings",
            params={"season": 2024, "week": 1},
        )

    assert missing_week.status_code == 422
    assert invalid_week.status_code == 422
    assert invalid_top.status_code == 422
    assert invalid_season.status_code == 422


def test_rankings_returns_503_when_startup_data_load_fails() -> None:
    def fail() -> SeasonData:
        raise RuntimeError("offline")

    with client_for(fail) as client:
        health = client.get("/health")
        rankings = client.get("/api/v1/rankings", params={"week": 1})

    assert health.status_code == 200
    assert health.json()["dataLoaded"] is False
    assert rankings.status_code == 503
    assert rankings.json() == {
        "detail": "NFL data is unavailable. Run the data sync command and retry."
    }
