from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

LOOKBACK_DAYS = 14
EXCLUDED_TERMS = ("betting", "odds", "picks", "prediction")

TEAM_ALIASES: dict[str, tuple[str, ...]] = {
    "ARI": ("cardinals", "arizona"),
    "ATL": ("falcons", "atlanta"),
    "BAL": ("ravens", "baltimore"),
    "BUF": ("bills", "buffalo"),
    "CAR": ("panthers", "carolina"),
    "CHI": ("bears", "chicago"),
    "CIN": ("bengals", "cincinnati"),
    "CLE": ("browns", "cleveland"),
    "DAL": ("cowboys", "dallas"),
    "DEN": ("broncos", "denver"),
    "DET": ("lions", "detroit"),
    "GB": ("packers", "green bay"),
    "HOU": ("texans", "houston"),
    "IND": ("colts", "indianapolis"),
    "JAX": ("jaguars", "jags", "jacksonville"),
    "KC": ("chiefs", "kansas city"),
    "LAC": ("chargers",),
    "LAR": ("rams",),
    "LV": ("raiders", "las vegas"),
    "MIA": ("dolphins", "miami"),
    "MIN": ("vikings", "minnesota"),
    "NE": ("patriots", "new england"),
    "NO": ("saints", "new orleans"),
    "NYG": ("giants",),
    "NYJ": ("jets",),
    "PHI": ("eagles", "philadelphia"),
    "PIT": ("steelers", "pittsburgh"),
    "SEA": ("seahawks", "seattle"),
    "SF": ("49ers", "niners", "san francisco"),
    "TB": ("buccaneers", "bucs", "tampa bay"),
    "TEN": ("titans", "tennessee"),
    "WAS": ("commanders", "washington"),
}


@dataclass(frozen=True, slots=True)
class Headline:
    game_id: str
    title: str
    published_at: datetime
    url: str


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _mentions_team(title: str, team_id: str) -> bool:
    normalized = _normalized(title)
    return any(
        re.search(rf"\b{re.escape(_normalized(alias))}\b", normalized)
        for alias in TEAM_ALIASES[team_id]
    )


def _is_nfl_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.endswith("espn.com") and "/nfl/" in parsed.path


def select_relevant_headline(
    candidates: list[Headline],
    *,
    away_team_id: str,
    home_team_id: str,
    kickoff: datetime,
) -> Headline | None:
    """Select one ESPN pregame headline without leaking the game result."""
    window_start = kickoff - timedelta(days=LOOKBACK_DAYS)
    relevant = [
        candidate
        for candidate in candidates
        if window_start <= candidate.published_at < kickoff
        and _is_nfl_url(candidate.url)
        and _mentions_team(candidate.title, away_team_id)
        and _mentions_team(candidate.title, home_team_id)
        and not any(term in candidate.title.lower() for term in EXCLUDED_TERMS)
        and "/betting/" not in candidate.url.lower()
    ]
    if not relevant:
        return None
    return max(
        relevant,
        key=lambda item: (
            "/preview" in item.url.lower(),
            item.published_at,
            item.title,
        ),
    )


class HeadlineRepository:
    """Read-only lookup for the checked-in 2025 pregame headline cache."""

    def __init__(self, path: Path | None = None) -> None:
        self._headlines: dict[str, Headline] = {}
        if path is not None and path.exists():
            self._headlines = self._load(path)

    @staticmethod
    def _load(path: Path) -> dict[str, Headline]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("Headline cache must contain a JSON list")

        headlines: dict[str, Headline] = {}
        for item in raw:
            headline = Headline(
                game_id=item["gameId"],
                title=item["headline"].strip(),
                published_at=_parse_datetime(item["publishedAt"]),
                url=item["url"],
            )
            if not headline.game_id.startswith("2025_"):
                raise ValueError(f"Unexpected headline game ID: {headline.game_id}")
            if not headline.title:
                raise ValueError(f"Headline is empty for {headline.game_id}")
            if headline.game_id in headlines:
                raise ValueError(f"Duplicate headline game ID: {headline.game_id}")
            headlines[headline.game_id] = headline
        return headlines

    def get(self, game_id: str) -> Headline | None:
        return self._headlines.get(game_id)

    def reason_for(self, game_id: str) -> str | None:
        headline = self.get(game_id)
        return f"Headline: {headline.title}" if headline else None
