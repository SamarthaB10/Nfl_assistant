from datetime import UTC
from pathlib import Path

import httpx
import pytest

from nflviewer.news.feeds import (
    FEED_CONFIGS,
    FeedResponseTooLargeError,
    NewsSource,
    RssFeedClient,
    UnsafeFeedRedirectError,
    parse_feed,
)

FIXTURES = Path(__file__).parent / "fixtures" / "news"


@pytest.mark.parametrize(
    ("source", "fixture", "expected"),
    [
        (
            NewsSource.ESPN,
            "espn.xml",
            {
                "source_article_id": "US-EN-123",
                "author": "Example ESPN Reporter",
                "image_url": None,
                "team_codes": ("BUF", "KC"),
            },
        ),
        (
            NewsSource.CBS,
            "cbs.xml",
            {
                "source_article_id": "cbs-article-123",
                "author": "Example CBS Reporter",
                "image_url": "https://sportshub.cbsistatic.com/i/example/bengals.jpg",
                "team_codes": ("CIN",),
            },
        ),
        (
            NewsSource.FOX,
            "fox.xml",
            {
                "source_article_id": "https://www.foxsports.com/stories/nfl/49ers-training-camp",
                "author": None,
                "image_url": "https://statics.foxsports.com/example/49ers.jpg",
                "team_codes": ("SF",),
            },
        ),
        (
            NewsSource.NBC,
            "nbc.atom",
            {
                "source_article_id": "urn:uuid:nbc-article-123",
                "author": "NBC Sports",
                "image_url": None,
                "team_codes": ("NE",),
            },
        ),
    ],
)
def test_parse_feed_normalizes_current_publisher_metadata(
    source: NewsSource,
    fixture: str,
    expected: dict[str, object],
) -> None:
    articles = parse_feed(source, (FIXTURES / fixture).read_bytes())

    assert len(articles) == 1
    article = articles[0]
    assert article.source is source
    assert article.source_article_id == expected["source_article_id"]
    assert article.author == expected["author"]
    assert article.image_url == expected["image_url"]
    assert article.team_codes == expected["team_codes"]
    assert article.published_at.tzinfo is UTC
    assert article.published_at.year == 2026


def test_parse_feed_rejects_non_publisher_article_urls() -> None:
    payload = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel><item>
      <title>Patriots training camp update</title>
      <link>http://127.0.0.1/internal</link>
      <pubDate>Wed, 29 Jul 2026 18:18:09 +0000</pubDate>
      <guid>unsafe</guid>
    </item></channel></rss>"""

    assert parse_feed(NewsSource.ESPN, payload) == []


def test_parse_feed_tags_a_player_only_article_with_the_latest_roster_team() -> None:
    payload = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel><item>
      <title>Patrick Mahomes returns to practice</title>
      <description>The quarterback is expected to be ready for camp.</description>
      <link>https://www.espn.com/nfl/story/_/id/456/mahomes-returns</link>
      <pubDate>Wed, 29 Jul 2026 18:18:09 +0000</pubDate>
      <guid>mahomes-returns</guid>
    </item></channel></rss>"""

    articles = parse_feed(
        NewsSource.ESPN,
        payload,
        player_team_codes={"patrick mahomes": "KC"},
    )

    assert articles[0].team_codes == ("KC",)


def test_parse_feed_preserves_explicit_team_tags_alongside_player_tags() -> None:
    payload = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel><item>
      <title>Patrick Mahomes watches the Bills open camp</title>
      <link>https://www.espn.com/nfl/story/_/id/789/mahomes-bills</link>
      <pubDate>Wed, 29 Jul 2026 18:18:09 +0000</pubDate>
      <guid>mahomes-bills</guid>
    </item></channel></rss>"""

    articles = parse_feed(
        NewsSource.ESPN,
        payload,
        player_team_codes={"patrick mahomes": "KC"},
    )

    assert articles[0].team_codes == ("BUF", "KC")


def test_parse_feed_does_not_match_player_surnames_without_the_full_name() -> None:
    payload = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel><item>
      <title>Mahomes returns to practice</title>
      <link>https://www.espn.com/nfl/story/_/id/101/mahomes-returns</link>
      <pubDate>Wed, 29 Jul 2026 18:18:09 +0000</pubDate>
      <guid>surname-only</guid>
    </item></channel></rss>"""

    articles = parse_feed(
        NewsSource.ESPN,
        payload,
        player_team_codes={"patrick mahomes": "KC"},
    )

    assert articles[0].team_codes == ()


@pytest.mark.parametrize("declaration", [b"<!DOCTYPE rss>", b"<!ENTITY x 'unsafe'>"])
def test_parse_feed_rejects_xml_declarations_that_can_expand_entities(
    declaration: bytes,
) -> None:
    payload = b"<?xml version='1.0'?>" + declaration + b"<rss />"

    with pytest.raises(ValueError, match="Unsafe XML declaration"):
        parse_feed(NewsSource.ESPN, payload)


@pytest.mark.anyio
async def test_feed_client_fetches_only_the_configured_official_url() -> None:
    requested_urls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200, content=(FIXTURES / "espn.xml").read_bytes())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        articles = await RssFeedClient(http_client).fetch(NewsSource.ESPN)

    assert requested_urls == [FEED_CONFIGS[NewsSource.ESPN].url]
    assert len(articles) == 1


@pytest.mark.anyio
async def test_nbc_feed_uses_article_metadata_for_author_image_and_team() -> None:
    requested_urls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if request.url.path == "/nfl.atom":
            return httpx.Response(200, content=(FIXTURES / "nbc.atom").read_bytes())
        return httpx.Response(200, content=(FIXTURES / "nbc-article.html").read_bytes())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        articles = await RssFeedClient(
            http_client,
            nbc_article_delay_seconds=0,
        ).fetch(NewsSource.NBC)

    assert requested_urls == [
        "https://www.nbcsports.com/nfl.atom",
        (
            "https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/"
            "drake-maye-returns-to-practice"
        ),
    ]
    assert articles[0].author == "Example NBC Reporter"
    assert articles[0].image_url == ("https://nbcsports.brightspotcdn.com/example/drake-maye.jpg")
    assert articles[0].excerpt == ("The Patriots welcomed their quarterback back to practice.")
    assert articles[0].team_codes == ("NE",)


@pytest.mark.anyio
async def test_nbc_feed_keeps_atom_metadata_when_article_enrichment_fails() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/nfl.atom":
            return httpx.Response(200, content=(FIXTURES / "nbc.atom").read_bytes())
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        articles = await RssFeedClient(
            http_client,
            nbc_article_delay_seconds=0,
        ).fetch(NewsSource.NBC)

    assert articles
    assert articles[0].source is NewsSource.NBC
    assert articles[0].author == "NBC Sports"
    assert articles[0].image_url is None
    assert articles[0].team_codes == ("NE",)


@pytest.mark.anyio
async def test_feed_client_rejects_oversized_responses() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * 129)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = RssFeedClient(http_client, max_response_bytes=128)

        with pytest.raises(FeedResponseTooLargeError):
            await client.fetch(NewsSource.ESPN)


@pytest.mark.anyio
async def test_feed_client_follows_only_same_publisher_https_redirects() -> None:
    requested_urls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if request.url.path.endswith("/news"):
            return httpx.Response(302, headers={"location": "/espn/rss/nfl/current"})
        return httpx.Response(200, content=(FIXTURES / "espn.xml").read_bytes())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        articles = await RssFeedClient(http_client).fetch(NewsSource.ESPN)

    assert len(articles) == 1
    assert requested_urls[-1] == "https://www.espn.com/espn/rss/nfl/current"


@pytest.mark.anyio
async def test_feed_client_rejects_redirects_to_unapproved_hosts() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "http://127.0.0.1/internal"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(UnsafeFeedRedirectError):
            await RssFeedClient(http_client).fetch(NewsSource.ESPN)


def test_feed_configs_target_current_nfl_feeds() -> None:
    assert set(FEED_CONFIGS) == {
        NewsSource.ESPN,
        NewsSource.CBS,
        NewsSource.FOX,
        NewsSource.NBC,
    }
    assert all(config.url.startswith("https://") for config in FEED_CONFIGS.values())
    assert all("2025" not in config.url for config in FEED_CONFIGS.values())
