from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from nflviewer.data import Repository, SeasonData
from nflviewer.headlines import (
    TEAM_ALIASES,
    Headline,
    select_relevant_headline,
)

logger = logging.getLogger(__name__)

SEARCH_URL = "https://site.web.api.espn.com/apis/search/v2"
DEFAULT_OUTPUT = Path("data/headlines-2025.json")
Search = Callable[[str], list[Headline]]


def _published_at(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_search_response(payload: Mapping[str, Any]) -> list[Headline]:
    candidates: list[Headline] = []
    for result in payload.get("results", []):
        for content in result.get("contents", []):
            title = content.get("displayName")
            published_at = content.get("date")
            url = content.get("link", {}).get("web")
            if not all(isinstance(value, str) and value for value in (title, published_at, url)):
                continue
            try:
                parsed_date = _published_at(published_at)
            except ValueError:
                continue
            candidates.append(
                Headline(
                    game_id="",
                    title=title.strip(),
                    published_at=parsed_date,
                    url=url.replace("http://", "https://", 1),
                )
            )
    return candidates


class EspnSearchClient:
    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout

    def search(self, query: str) -> list[Headline]:
        url = f"{SEARCH_URL}?{urlencode({'limit': 100, 'query': query})}"
        request = Request(url, headers={"User-Agent": "NFLViewer/0.1"})
        with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
            payload = json.load(response)
        return parse_search_response(payload)


def _queries(
    *,
    week: int,
    away_team_id: str,
    away_team_name: str,
    home_team_id: str,
    home_team_name: str,
    kickoff: datetime,
) -> tuple[str, ...]:
    away_nickname = TEAM_ALIASES[away_team_id][0]
    home_nickname = TEAM_ALIASES[home_team_id][0]
    month = kickoff.strftime("%B")
    return (
        f"{away_nickname} {home_nickname} {month} 2025",
        f"{away_team_name} {home_team_name} Week {week} 2025",
    )


def search_matchup(
    *,
    game_id: str,
    week: int,
    away_team_id: str,
    away_team_name: str,
    home_team_id: str,
    home_team_name: str,
    kickoff: datetime,
    search: Search,
) -> Headline | None:
    candidates: list[Headline] = []
    for query in _queries(
        week=week,
        away_team_id=away_team_id,
        away_team_name=away_team_name,
        home_team_id=home_team_id,
        home_team_name=home_team_name,
        kickoff=kickoff,
    ):
        try:
            candidates.extend(search(query))
        except Exception:
            logger.exception("Headline search failed for %s", game_id)
            continue
        selected = select_relevant_headline(
            candidates,
            away_team_id=away_team_id,
            home_team_id=home_team_id,
            kickoff=kickoff,
        )
        if selected is not None:
            return Headline(
                game_id=game_id,
                title=selected.title,
                published_at=selected.published_at,
                url=selected.url,
            )
    return None


def backfill_headlines(
    data: SeasonData,
    *,
    search: Search,
    workers: int = 6,
) -> list[Headline]:
    games = [game for week in range(1, 19) for game in data.matchups_for_week(week)]

    def find(game_id: str, week: int) -> Headline | None:
        game = next(game for game in games if game.game_id == game_id)
        return search_matchup(
            game_id=game.game_id,
            week=week,
            away_team_id=game.away_team_id,
            away_team_name=data.teams[game.away_team_id].name,
            home_team_id=game.home_team_id,
            home_team_name=data.teams[game.home_team_id].name,
            kickoff=game.kickoff,
            search=search,
        )

    headlines: list[Headline] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(find, game.game_id, game.week): game for game in games}
        for future in as_completed(futures):
            game = futures[future]
            try:
                headline = future.result()
            except Exception:
                logger.exception("Unable to backfill headline for %s", game.game_id)
                continue
            if headline:
                headlines.append(headline)
            else:
                logger.warning("No pregame headline found for %s", game.game_id)
    return sorted(headlines, key=lambda item: item.game_id)


def write_headlines(headlines: list[Headline], path: Path) -> None:
    payload = [
        {
            "gameId": headline.game_id,
            "headline": headline.title,
            "publishedAt": headline.published_at.isoformat().replace("+00:00", "Z"),
            "url": headline.url,
        }
        for headline in headlines
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill 2025 ESPN pregame headlines")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        parser.error("--workers must be between 1 and 12")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    data = Repository().get()
    headlines = backfill_headlines(
        data,
        search=EspnSearchClient().search,
        workers=args.workers,
    )
    write_headlines(headlines, args.output)
    logger.info("Wrote %d headlines to %s", len(headlines), args.output)


if __name__ == "__main__":
    main()
