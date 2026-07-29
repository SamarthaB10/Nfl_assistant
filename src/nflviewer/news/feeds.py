from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from enum import StrEnum
from urllib.parse import urljoin, urlparse

import httpx

from nflviewer.headlines import TEAM_ALIASES

DC_CREATOR = "{http://purl.org/dc/elements/1.1/}creator"
MEDIA_CONTENT = "{http://search.yahoo.com/mrss/}content"
MEDIA_THUMBNAIL = "{http://search.yahoo.com/mrss/}thumbnail"
MAX_ITEMS_PER_FEED = 100
DEFAULT_MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class NewsSource(StrEnum):
    ESPN = "ESPN"
    CBS = "CBS"
    FOX = "FOX"


@dataclass(frozen=True, slots=True)
class FeedConfig:
    url: str
    article_hosts: frozenset[str]
    image_hosts: frozenset[str]


FEED_CONFIGS: dict[NewsSource, FeedConfig] = {
    NewsSource.ESPN: FeedConfig(
        url="https://www.espn.com/espn/rss/nfl/news",
        article_hosts=frozenset({"www.espn.com"}),
        image_hosts=frozenset({"a.espncdn.com"}),
    ),
    NewsSource.CBS: FeedConfig(
        url="https://www.cbssports.com/rss/headlines/nfl",
        article_hosts=frozenset({"www.cbssports.com"}),
        image_hosts=frozenset({"sportshub.cbsistatic.com"}),
    ),
    NewsSource.FOX: FeedConfig(
        url=(
            "https://api.foxsports.com/v2/content/optimized-rss"
            "?partnerKey=MB0Wehpmuj2lUhuRhQaafhBjAJqaPU244mlTDK1i"
            "&size=30&tags=fs%2Fnfl"
        ),
        article_hosts=frozenset({"www.foxsports.com"}),
        image_hosts=frozenset({"a57.foxsports.com", "statics.foxsports.com"}),
    ),
}


@dataclass(frozen=True, slots=True)
class FeedArticle:
    source: NewsSource
    source_article_id: str
    title: str
    author: str | None
    excerpt: str | None
    canonical_url: str
    image_url: str | None
    team_codes: tuple[str, ...]
    published_at: datetime


class FeedResponseTooLargeError(ValueError):
    """Raised before an oversized publisher response is parsed."""


class UnsafeFeedRedirectError(ValueError):
    """Raised when a feed redirects outside its approved HTTPS host."""


def _text(item: ET.Element, tag: str) -> str | None:
    element = item.find(tag)
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def _is_allowed_https_url(value: str, hosts: frozenset[str]) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname in hosts and not parsed.username


def _published_at(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _image_url(item: ET.Element, config: FeedConfig) -> str | None:
    candidates: list[str] = []
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.get("type", "").startswith("image/"):
        candidates.append(enclosure.get("url", ""))
    for tag in (MEDIA_THUMBNAIL, MEDIA_CONTENT):
        element = item.find(tag)
        if element is not None:
            candidates.append(element.get("url", ""))
    return next(
        (url for url in candidates if _is_allowed_https_url(url, config.image_hosts)),
        None,
    )


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _team_codes(title: str, excerpt: str | None) -> tuple[str, ...]:
    content = _normalized(f"{title} {excerpt or ''}")
    return tuple(
        sorted(
            team_id
            for team_id, aliases in TEAM_ALIASES.items()
            if any(re.search(rf"\b{re.escape(_normalized(alias))}\b", content) for alias in aliases)
        )
    )


def parse_feed(source: NewsSource, payload: bytes) -> list[FeedArticle]:
    upper_payload = payload.upper()
    if b"<!DOCTYPE" in upper_payload or b"<!ENTITY" in upper_payload:
        raise ValueError("Unsafe XML declaration")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as error:
        raise ValueError("Invalid RSS XML") from error

    config = FEED_CONFIGS[source]
    articles: list[FeedArticle] = []
    for item in root.findall(".//item")[:MAX_ITEMS_PER_FEED]:
        title = _text(item, "title")
        canonical_url = _text(item, "link")
        published_at = _published_at(_text(item, "pubDate"))
        if (
            title is None
            or canonical_url is None
            or published_at is None
            or not _is_allowed_https_url(canonical_url, config.article_hosts)
        ):
            continue
        source_article_id = _text(item, "guid") or canonical_url
        excerpt = _text(item, "description")
        articles.append(
            FeedArticle(
                source=source,
                source_article_id=source_article_id,
                title=title,
                author=_text(item, DC_CREATOR),
                excerpt=excerpt,
                canonical_url=canonical_url,
                image_url=_image_url(item, config),
                team_codes=_team_codes(title, excerpt),
                published_at=published_at,
            )
        )
    return articles


class RssFeedClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    ) -> None:
        self._http_client = http_client
        self._max_response_bytes = max_response_bytes

    async def fetch(self, source: NewsSource) -> list[FeedArticle]:
        config = FEED_CONFIGS[source]
        approved_feed_host = urlparse(config.url).hostname
        current_url = config.url
        for _ in range(3):
            content = bytearray()
            async with self._http_client.stream(
                "GET",
                current_url,
                follow_redirects=False,
                headers={"User-Agent": "LeagueWatch/0.1 (NFL news aggregator)"},
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    redirected_url = urljoin(current_url, location or "")
                    parsed_redirect = urlparse(redirected_url)
                    if (
                        location is None
                        or parsed_redirect.scheme != "https"
                        or parsed_redirect.hostname != approved_feed_host
                        or parsed_redirect.username is not None
                    ):
                        raise UnsafeFeedRedirectError(f"Unsafe {source} feed redirect")
                    current_url = redirected_url
                    continue
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > self._max_response_bytes:
                        raise FeedResponseTooLargeError(
                            f"{source} feed exceeded {self._max_response_bytes} bytes"
                        )
            return parse_feed(source, bytes(content))
        raise UnsafeFeedRedirectError(f"Too many {source} feed redirects")
