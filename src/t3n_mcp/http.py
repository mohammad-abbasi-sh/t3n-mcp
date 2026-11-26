"""HTTP layer for t3n_mcp — plain httpx GETs against t3n.de.

Endpoints, all public, no key, no login:
- the official RSS feeds: https://t3n.de/rss.xml (20 items) and
  https://t3n.de/news/feed/ (10 items, WordPress feed) — both
  fetched and de-duplicated by canonical link (see domain).
  /news/rss.xml, /magazin/rss.xml, /rss/news.xml and /feed/ all
  404, so these two are the only feeds.
- article pages: https://t3n.de/news/<slug>-<id>/ — the full text
  is read from the JSON-LD NewsArticle articleBody inside the
  @graph block (see domain.parse_article), with the
  server-rendered <article> paragraphs as fallback.

Only t3n.de is ever fetched. Feed items that link off-site are
never fetched: fetch_article only accepts t3n.de article URLs.
"""
from __future__ import annotations

import os
import ssl
import time
from urllib.parse import urlparse

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 25.0
ALLOWED_HOSTS = ("t3n.de",)
HEALTH_URL = "https://t3n.de/rss.xml"


class T3nError(RuntimeError):
    pass


def _verify():
    """TLS trust store: the OS bundle when present, else httpx/certifi.

    The OS bundle matters behind MITM egress proxies (their CA is in the
    system store, not in certifi) and is the right default on Linux
    anyway; on systems without it we fall back to certifi.
    """
    for path in (
        "/etc/ssl/certs/ca-certificates.crt",
        ssl.get_default_verify_paths().openssl_cafile,
    ):
        if path and os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return True


def _client(accept: str) -> httpx.Client:
    # NOTE: we read the proxy URL from the environment but never log it.
    # trust_env=False because httpx fails to parse bracketed IPv6 entries
    # (e.g. [::1]) that some environments put in no_proxy.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    return httpx.Client(
        headers={"User-Agent": UA, "Accept": accept},
        timeout=TIMEOUT,
        proxy=proxy or None,
        trust_env=False,
        verify=_verify(),
        follow_redirects=True,
    )


def _check_host(url: str) -> None:
    host = (urlparse(url).netloc or "").lower()
    if host not in ALLOWED_HOSTS:
        raise T3nError(
            f"only {', '.join(ALLOWED_HOSTS)} pages are fetched "
            f"(got {host or url!r})"
        )


def _get(url: str, accept: str) -> str:
    """GET with one retry on 429/5xx and on transient network errors."""
    _check_host(url)
    last_exc: Exception | None = None
    r: httpx.Response | None = None
    for attempt in range(2):
        try:
            with _client(accept) as c:
                r = c.get(url)
        except httpx.HTTPError as e:
            last_exc = e
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise T3nError(f"network error fetching {url}: {e}") from e
        if r.status_code in (429, 500, 502, 503):
            if attempt == 0:
                time.sleep(1.0)
                continue
        break
    assert r is not None  # loop always assigns r or raises
    if r.status_code == 403:
        raise T3nError(
            f"t3n.de returned HTTP 403 for {url} (bot wall) — try again later"
        )
    if r.status_code == 429:
        raise T3nError(
            "t3n.de rate-limited the request (HTTP 429) — try again later"
        )
    if r.status_code != 200:
        raise T3nError(f"t3n.de returned HTTP {r.status_code} for {url}")
    return r.text


def fetch_feed(url: str) -> str:
    """GET one official t3n RSS feed; returns the raw XML text."""
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    ok = host in ALLOWED_HOSTS and parsed.path in ("/rss.xml", "/news/feed/")
    if not ok:
        raise T3nError(f"only the t3n RSS feed URLs are fetched (got {url!r})")
    return _get(url, "application/rss+xml, application/xml, text/xml, */*")


def fetch_article(url: str) -> str:
    """GET one t3n.de article page; returns the raw HTML text.

    Article URLs are /news/<slug>-<id>/ (no .html suffix). Feed
    URLs (/rss.xml, /news/feed/), the home page and any other host
    are refused.
    """
    parsed = urlparse(url)
    if parsed.fragment:
        raise T3nError(
            "URLs with a fragment are not articles (got {url!r})".format(url=url)
        )
    path = parsed.path
    if path in ("/rss.xml", "/rss", "/rss/", "/news/feed", "/news/feed/") or path.endswith((".xml", ".rss")):
        raise T3nError(
            "only t3n.de article URLs are fetched — feed URLs are "
            f"not articles (got {url!r})"
        )
    if path in ("", "/"):
        raise T3nError(
            "only t3n.de article URLs are fetched — the home page "
            f"is not an article (got {url!r})"
        )
    return _get(url, "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")


def health_check() -> dict:
    """One polite probe of the source feed.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `t3n_health` tool
    and the daily smoke CI.
    """
    url = HEALTH_URL
    try:
        fetch_feed(url)
    except T3nError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
