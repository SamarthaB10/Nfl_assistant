from __future__ import annotations

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from enum import StrEnum
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx

from nflviewer.headlines import TEAM_ALIASES

logger = logging.getLogger(__name__)

DC_CREATOR = "{http://purl.org/dc/elements/1.1/}creator"
MEDIA_CONTENT = "{http://search.yahoo.com/mrss/}content"
MEDIA_THUMBNAIL = "{http://search.yahoo.com/mrss/}thumbnail"
ATOM_NAMESPACE = "{http://www.w3.org/2005/Atom}"
MAX_ITEMS_PER_FEED = 100
DEFAULT_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
NBC_ARTICLE_DELAY_SECONDS = 10.0
NBC_JSON_LD_PATTERN = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
NBC_TEAM_PATTERN = re.compile(r"['\"]Team['\"]\s*:\s*['\"]([^'\"]*)['\"]")
NBC_OG_IMAGE_PATTERN = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


class NewsSource(StrEnum):
    ESPN = "ESPN"
    CBS = "CBS"
    FOX = "FOX"
    NBC = "NBC"


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
    NewsSource.NBC: FeedConfig(
        url="https://www.nbcsports.com/nfl.atom",
        article_hosts=frozenset({"www.nbcsports.com"}),
        image_hosts=frozenset({"nbcsports.brightspotcdn.com"}),
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


@dataclass(frozen=True, slots=True)
class NbcArticleMetadata:
    author: str | None
    excerpt: str | None
    image_url: str | None
    team_codes: tuple[str, ...]


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


def _atom_published_at(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
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


def _team_codes(
    title: str,
    excerpt: str | None,
    *,
    player_team_codes: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    content = _normalized(f"{title} {excerpt or ''}")
    padded_content = f" {content} "
    team_codes = {
        team_id
        for team_id, aliases in TEAM_ALIASES.items()
        if any(re.search(rf"\b{re.escape(_normalized(alias))}\b", content) for alias in aliases)
    }
    if player_team_codes:
        team_codes.update(
            team_id
            for player_name, team_id in player_team_codes.items()
            if f" {player_name} " in padded_content
        )
    return tuple(sorted(team_codes))


def _parse_atom(
    source: NewsSource,
    root: ET.Element,
    *,
    player_team_codes: Mapping[str, str] | None = None,
) -> list[FeedArticle]:
    config = FEED_CONFIGS[source]
    feed_author = _text(root, f"{ATOM_NAMESPACE}author/{ATOM_NAMESPACE}name")
    articles: list[FeedArticle] = []
    for entry in root.findall(f"{ATOM_NAMESPACE}entry")[:MAX_ITEMS_PER_FEED]:
        title = _text(entry, f"{ATOM_NAMESPACE}title")
        link = next(
            (
                candidate
                for candidate in entry.findall(f"{ATOM_NAMESPACE}link")
                if candidate.get("rel", "alternate") == "alternate"
            ),
            None,
        )
        canonical_url = link.get("href") if link is not None else None
        published_at = _atom_published_at(
            _text(entry, f"{ATOM_NAMESPACE}published") or _text(entry, f"{ATOM_NAMESPACE}updated")
        )
        if (
            title is None
            or canonical_url is None
            or published_at is None
            or not _is_allowed_https_url(canonical_url, config.article_hosts)
        ):
            continue
        excerpt = _text(entry, f"{ATOM_NAMESPACE}summary")
        articles.append(
            FeedArticle(
                source=source,
                source_article_id=(_text(entry, f"{ATOM_NAMESPACE}id") or canonical_url),
                title=title,
                author=(
                    _text(entry, f"{ATOM_NAMESPACE}author/{ATOM_NAMESPACE}name") or feed_author
                ),
                excerpt=excerpt,
                canonical_url=canonical_url,
                image_url=None,
                team_codes=_team_codes(
                    title,
                    excerpt,
                    player_team_codes=player_team_codes,
                ),
                published_at=published_at,
            )
        )
    return articles


def _nbc_article_metadata(payload: bytes) -> NbcArticleMetadata:
    document = payload.decode("utf-8", errors="replace")
    article_schema: dict[str, object] = {}
    for match in NBC_JSON_LD_PATTERN.finditer(document):
        try:
            candidate = json.loads(unescape(match.group(1)))
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("@type") == "Article":
            article_schema = candidate
            break

    author: str | None = None
    raw_authors = article_schema.get("author")
    if isinstance(raw_authors, dict):
        raw_authors = [raw_authors]
    if isinstance(raw_authors, list):
        author = next(
            (
                candidate["name"].strip()
                for candidate in raw_authors
                if isinstance(candidate, dict)
                and isinstance(candidate.get("name"), str)
                and candidate["name"].strip()
            ),
            None,
        )

    excerpt_value = article_schema.get("description")
    excerpt = (
        unescape(excerpt_value).strip()
        if isinstance(excerpt_value, str) and excerpt_value.strip()
        else None
    )
    image_match = NBC_OG_IMAGE_PATTERN.search(document)
    image_url = unescape(image_match.group(1)).strip() if image_match else None
    if image_url and not _is_allowed_https_url(
        image_url,
        FEED_CONFIGS[NewsSource.NBC].image_hosts,
    ):
        image_url = None

    team_match = NBC_TEAM_PATTERN.search(document)
    team_codes = _team_codes(team_match.group(1), None) if team_match else ()
    return NbcArticleMetadata(
        author=author,
        excerpt=excerpt,
        image_url=image_url,
        team_codes=team_codes,
    )


def parse_feed(
    source: NewsSource,
    payload: bytes,
    *,
    player_team_codes: Mapping[str, str] | None = None,
) -> list[FeedArticle]:
    upper_payload = payload.upper()
    if b"<!DOCTYPE" in upper_payload or b"<!ENTITY" in upper_payload:
        raise ValueError("Unsafe XML declaration")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as error:
        raise ValueError("Invalid RSS XML") from error

    if root.tag == f"{ATOM_NAMESPACE}feed":
        return _parse_atom(
            source,
            root,
            player_team_codes=player_team_codes,
        )

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
                team_codes=_team_codes(title, excerpt, player_team_codes=player_team_codes),
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
        player_team_codes: Mapping[str, str] | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        nbc_article_delay_seconds: float = NBC_ARTICLE_DELAY_SECONDS,
    ) -> None:
        self._http_client = http_client
        self._max_response_bytes = max_response_bytes
        self._player_team_codes = dict(player_team_codes or {})
        self._sleep = sleep
        self._nbc_article_delay_seconds = nbc_article_delay_seconds

    async def _fetch_bytes(
        self,
        url: str,
        *,
        approved_host: str | None,
        label: str,
    ) -> bytes:
        current_url = url
        for _ in range(3):
            content = bytearray()
            async with self._http_client.stream(
                "GET",
                current_url,
                follow_redirects=False,
                headers={"User-Agent": "Drizzle/0.1 (NFL news aggregator)"},
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    redirected_url = urljoin(current_url, location or "")
                    parsed_redirect = urlparse(redirected_url)
                    if (
                        location is None
                        or parsed_redirect.scheme != "https"
                        or parsed_redirect.hostname != approved_host
                        or parsed_redirect.username is not None
                    ):
                        raise UnsafeFeedRedirectError(f"Unsafe {label} redirect")
                    current_url = redirected_url
                    continue
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > self._max_response_bytes:
                        raise FeedResponseTooLargeError(
                            f"{label} exceeded {self._max_response_bytes} bytes"
                        )
            return bytes(content)
        raise UnsafeFeedRedirectError(f"Too many {label} redirects")

    async def _enrich_nbc_articles(
        self,
        articles: list[FeedArticle],
    ) -> list[FeedArticle]:
        enriched: list[FeedArticle] = []
        for article in articles:
            if self._nbc_article_delay_seconds:
                await self._sleep(self._nbc_article_delay_seconds)
            try:
                payload = await self._fetch_bytes(
                    article.canonical_url,
                    approved_host="www.nbcsports.com",
                    label="NBC article",
                )
                metadata = _nbc_article_metadata(payload)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning(
                    "Unable to enrich NBC article metadata for %s",
                    article.canonical_url,
                    exc_info=True,
                )
                enriched.append(article)
                continue
            enriched.append(
                replace(
                    article,
                    author=metadata.author or article.author,
                    excerpt=metadata.excerpt or article.excerpt,
                    image_url=metadata.image_url or article.image_url,
                    team_codes=tuple(sorted(set(article.team_codes) | set(metadata.team_codes))),
                )
            )
        return enriched

    async def fetch(self, source: NewsSource) -> list[FeedArticle]:
        config = FEED_CONFIGS[source]
        payload = await self._fetch_bytes(
            config.url,
            approved_host=urlparse(config.url).hostname,
            label=f"{source.value} feed",
        )
        articles = parse_feed(
            source,
            payload,
            player_team_codes=self._player_team_codes,
        )
        if source is NewsSource.NBC:
            return await self._enrich_nbc_articles(articles)
        return articles
