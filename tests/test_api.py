from collections.abc import Callable
from contextlib import AbstractContextManager

import polars as pl
from fastapi.testclient import TestClient

from nflviewer.app import create_app
from nflviewer.data import SeasonData


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
                "away_score": None,
                "home_team": "BUF",
                "home_score": None,
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
                "team_logo_espn": None,
            }
            for team_id, team_name, conference, division in [
                ("BUF", "Buffalo Bills", "AFC", "AFC East"),
                ("NE", "New England Patriots", "AFC", "AFC East"),
                ("DAL", "Dallas Cowboys", "NFC", "NFC East"),
                ("NYG", "New York Giants", "NFC", "NFC East"),
            ]
        ]
    )
    return SeasonData.from_frames(schedules, teams)


class StubRepository:
    def __init__(self, loader: Callable[[], SeasonData]) -> None:
        self.loader = loader

    def get(self) -> SeasonData:
        return self.loader()


def client_for(loader: Callable[[], SeasonData]) -> AbstractContextManager[TestClient]:
    return TestClient(create_app(StubRepository(loader)))


def test_health_reports_loaded_data() -> None:
    with client_for(season_data) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["dataLoaded"] is True


def test_rankings_returns_all_games_in_rank_order() -> None:
    with client_for(season_data) as client:
        response = client.get("/api/v1/rankings", params={"week": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["season"] == 2025
    assert body["week"] == 1
    assert body["requestedTop"] is None
    assert body["totalMatchups"] == 2
    assert body["returnedMatchups"] == 2
    assert [game["rank"] for game in body["games"]] == [1, 2]
    assert body["games"][0]["gameId"] == "2025_01_NE_BUF"


def test_rankings_applies_top_after_scoring_all_games() -> None:
    with client_for(season_data) as client:
        response = client.get("/api/v1/rankings", params={"week": 1, "top": 1})

    assert response.status_code == 200
    assert response.json()["totalMatchups"] == 2
    assert response.json()["returnedMatchups"] == 1
    assert response.json()["requestedTop"] == 1


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
