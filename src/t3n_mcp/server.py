"""MCP server: unofficial read-only access to t3n — digital pioneers
(t3n.de), Germany's well-known tech magazine (yeebase media) — via
its two official RSS feeds (rss.xml, 20 items, plus /news/feed/,
10 items, de-duplicated) and article pages (full text from the
JSON-LD NewsArticle articleBody inside @graph; the
server-rendered <article> paragraphs are the fallback). No key,
no login."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for t3n — digital pioneers
(t3n.de), Germany's well-known tech magazine — via its two
official RSS feeds (no key, no login) and article pages. The
latest news (both feeds combined, de-duplicated, newest first),
keyword search across the feeds (title + teaser + tags), stories
by topic tag, the topics in today's feeds, and full article text
(the JSON-LD NewsArticle articleBody — 2,900–4,200 characters
sampled — with the server-rendered <article> paragraphs as
fallback). No per-section feeds exist on t3n.de, so there is no
section tool; the section of one article (e.g. "Software &
Entwicklung") is reported by t3n_get_article from the page's
articleSection. t3n news articles are generally free to read; a
paywalled page is reported as paywalled=true with the teaser
only, never fabricated text.
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Germany MCP factory.\
"""


_SOURCE = "t3n.de"
_DISCLAIMER = "Unofficial read-only data from t3n's public RSS feeds and article pages; verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("t3n-mcp", instructions=INSTRUCTIONS)


def _feed(limit: int) -> dict:
    """Fetch both t3n RSS feeds, de-duplicate by canonical link,
    newest first, capped."""
    items: list[dict] = []
    for url in _dom.FEEDS:
        parsed = _dom.parse_rss(_http.fetch_feed(url))
        items.extend(parsed["items"])
    merged = _dom.dedupe_sort(items)
    return {
        "feed_title": "t3n.de - News",
        "total_results": len(merged),
        "count": min(limit, len(merged)),
        "items": merged[:limit],
    }


@mcp.tool()
def t3n_latest(limit: int = 10) -> str:
    """Top t3n news (both official RSS feeds combined, ~22 unique
items), newest first. limit: 1..50 (default 10). Every item carries
a title, a canonical per-article link for t3n_get_article, a teaser
(description), tags (<category> values), an image URL and publish
time."""
    try:
        lim = _dom.validate_limit(limit)
        out = _feed(lim)
    except (_http.T3nError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def t3n_search_news(query: str, limit: int = 10) -> str:
    """Search t3n news by keyword (title + teaser + tags) across both
official RSS feeds. query: free text, e.g. "ChatGPT" or "Black
Friday". limit: 1..50 (default 10). Newest first, de-duplicated by
link."""
    try:
        if not (query or "").strip():
            return _ok({"error": "query must not be empty"})
        lim = _dom.validate_limit(limit)
        items: list[dict] = []
        for url in _dom.FEEDS:
            parsed = _dom.parse_rss(_http.fetch_feed(url))
            items.extend(parsed["items"])
        found = _dom.search_items(_dom.dedupe_sort(items), query.strip())
        out = {
            "query": query.strip(),
            "total_results": len(found),
            "count": min(lim, len(found)),
            "items": found[:lim],
        }
    except (_http.T3nError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def t3n_by_topic(topic: str, limit: int = 10) -> str:
    """Newest t3n stories on one topic tag (the feeds' <category>
values, e.g. "kuenstliche-intelligenz", "black-friday" or
"whatsapp"). topic: free text, matched case-insensitively as a
substring of a tag. limit: 1..50 (default 10). Items carry title,
link (a per-article URL for t3n_get_article), teaser, tags, image
URL and publish time."""
    try:
        if not (topic or "").strip():
            return _ok({"error": "topic must not be empty"})
        lim = _dom.validate_limit(limit)
        items: list[dict] = []
        for url in _dom.FEEDS:
            parsed = _dom.parse_rss(_http.fetch_feed(url))
            items.extend(parsed["items"])
        found = _dom.items_by_topic(_dom.dedupe_sort(items), topic.strip())
        out = {
            "topic": topic.strip(),
            "total_results": len(found),
            "count": min(lim, len(found)),
            "items": found[:lim],
        }
    except (_http.T3nError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def t3n_topics() -> str:
    """The topic tags in today's t3n feeds, with how many stories
each carries — most stories first. The main feed's tags are
lowercase slugs (e.g. "kuenstliche-intelligenz"); the news feed's
are display names (e.g. "Black Friday"). Use t3n_by_topic to read
one topic's stories."""
    try:
        items: list[dict] = []
        for url in _dom.FEEDS:
            parsed = _dom.parse_rss(_http.fetch_feed(url))
            items.extend(parsed["items"])
        topics = _dom.topics_with_counts(_dom.dedupe_sort(items))
        out = {
            "total_results": len(topics),
            "count": len(topics),
            "topics": topics,
        }
    except (_http.T3nError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def t3n_get_article(url: str) -> str:
    """Full text of one t3n article page (the JSON-LD NewsArticle
articleBody, with the server-rendered <article> paragraphs as
fallback). url: a t3n.de article URL, e.g. from t3n_latest
(/news/<slug>-<id>/). Returns title, author, publish time, the
section from the page's articleSection (e.g. "Software &
Entwicklung"), the body text and its word count. A paywalled page
returns paywalled=true with only the teaser as body — the full
text needs a subscription. Feed URLs, the home page and off-site
links are refused. Nothing is ever fabricated."""
    try:
        if not (url or "").strip():
            return _ok({"error": "url must not be empty"})
        url = url.strip()
        article = _dom.parse_article(_http.fetch_article(url))
        paywalled = article["paywalled"]
        note = ""
        if paywalled:
            note = (
                "This article is paywalled: only the teaser is "
                "available; the full text needs a subscription."
            )
        elif article["teaser_only"]:
            note = (
                "Only the teaser is available for this item; the teaser "
                "is the whole freely available text."
            )
        out = {
            "url": url,
            "title": article["title"],
            "author": article["author"],
            "published": article["published"],
            "section": article["section"],
            "kind": article["kind"],
            "paywalled": paywalled,
            "teaser_only": article["teaser_only"],
            "word_count": article["word_count"],
            "body": article["body"],
            "description": article["description"],
            "note": note,
        }
    except (_http.T3nError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def t3n_health() -> str:
    """Check whether the t3n RSS feed is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
