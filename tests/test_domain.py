"""Offline tests — parse the real captured t3n.de RSS feeds and one
real article page (a free NewsArticle with a real JSON-LD
articleBody inside @graph), no network. The paywalled branch is
tested with a small synthetic page (no paywalled t3n article was
found in the sampled pages on 2026-11-26 — t3n news articles are
generally free)."""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from t3n_mcp import domain as dom
from t3n_mcp import http as http_mod

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def _merged() -> list:
    main = dom.parse_rss(_read("headlines.xml"))
    news = dom.parse_rss(_read("news-feed.xml"))
    return dom.dedupe_sort(main["items"] + news["items"])


# Paywalled page, synthetic — built like a real t3n page (the
# NewsArticle lives inside an @graph array) but with
# isAccessibleForFree=false and a full body that must NOT leak.
_PAYWALLED_HTML = """<!DOCTYPE html><html><head><title>Test: Bezahlartikel | t3n</title>
<meta property="og:description" content="Nur der Teaser ist frei lesbar.">
<script type="application/ld+json">{"@context": "https://schema.org",
"@graph": [
{"@type": "NewsArticle", "headline": "Test: Bezahlartikel",
"description": "Nur der Teaser ist frei lesbar.",
"isAccessibleForFree": false,
"articleBody": "Der volle Text steht nur Abonnenten zur Verfügung.",
"author": {"@type": "Person", "name": "Max Muster"},
"datePublished": "2026-11-26T08:00:00+00:00",
"articleSection": "Software & Entwicklung"},
{"@type": "BreadcrumbList", "itemListElement": [
{"@type": "ListItem", "position": 1, "name": "Startseite"},
{"@type": "ListItem", "position": 2, "name": "News"},
{"@type": "ListItem", "position": 3, "name": "Test: Bezahlartikel"}]}]}</script>
</head><body><article><p>Nur der Teaser ist frei lesbar.</p>
<p>Der volle Text steht nur Abonnenten zur Verfügung.</p></article>
</body></html>"""

# Free page with NO articleBody — the SSR <article> paragraphs are
# the fallback; the newsletter promo must be filtered out.
_SSR_ONLY_HTML = """<!DOCTYPE html><html><head><title>Test: Nur SSR | t3n</title>
<meta property="og:description" content="Kurzer Teaser.">
<script type="application/ld+json">{"@context": "https://schema.org",
"@graph": [
{"@type": "NewsArticle", "headline": "Test: Nur SSR",
"isAccessibleForFree": true,
"author": {"@type": "Person", "name": "Erika Muster"},
"datePublished": "2026-11-26T09:00:00+00:00",
"articleSection": "Künstliche Intelligenz"}]}</script>
</head><body><article>
<p>Verpasse keine News mehr! Test: Nur SSR Kurzer Teaser.</p>
<p>Erster Absatz des Artikels mit echtem Inhalt.</p>
<p>Zweiter Absatz des Artikels mit echtem Inhalt.</p>
</article></body></html>"""


class TestMainFeed:
    def test_main_shape(self):
        parsed = dom.parse_rss(_read("headlines.xml"))
        assert parsed["feed_title"] == "t3n.de - News"
        assert parsed["count"] == 20
        assert len(parsed["items"]) == 20

    def test_main_first_item(self):
        parsed = dom.parse_rss(_read("headlines.xml"))
        first = parsed["items"][0]
        assert first["title"] == (
            "Neue Funktion in Whatsapp: So versendest du "
            "Geburtstagsgrüße bis zu 14 Tage im Voraus"
        )
        # Feed links carry utm params — the returned link is canonical.
        assert first["link"] == (
            "https://t3n.de/news/neue-funktion-in-whatsapp-so-"
            "versendest-du-geburtstagsgruesse-bis-zu-14-tage-im-"
            "voraus-1775472/"
        )
        assert "utm_source" not in first["link"]
        assert first["description"].startswith(
            "Der Messenger baut seinen Funktionsumfang stetig aus."
        )
        # The trailing "weiterlesen auf t3n.de" marker is stripped.
        assert not first["description"].endswith("weiterlesen auf t3n.de")
        assert first["published"] == "2026-11-26T09:30:26+00:00"
        # The main feed carries no author.
        assert first["author"] == ""
        assert first["tags"] == [
            "android", "apps", "ios", "messenger", "server", "whatsapp",
        ]
        assert first["image_url"] == (
            "https://cdn.t3n.de/news/wp-content/uploads/2025/04/"
            "whatsapp.jpg?class=hero"
        )

    def test_main_items_all_have_title_description_image(self):
        parsed = dom.parse_rss(_read("headlines.xml"))
        assert all(i["title"] and i["description"] for i in parsed["items"])
        assert all(i["image_url"] for i in parsed["items"])
        assert all(
            i["link"].startswith("https://t3n.de/news/")
            for i in parsed["items"]
        )


class TestNewsFeed:
    def test_news_shape(self):
        parsed = dom.parse_rss(_read("news-feed.xml"))
        assert parsed["feed_title"] == "t3n"
        assert parsed["count"] == 10
        assert len(parsed["items"]) == 10

    def test_news_first_item(self):
        parsed = dom.parse_rss(_read("news-feed.xml"))
        first = parsed["items"][0]
        assert first["title"] == (
            "Black Friday: Balkonkraftwerk mit Anker SOLIX 4 Pro "
            "Speicher für 1.599 Euro"
        )
        assert first["link"] == (
            "https://t3n.de/news/balkonkraftwerk-speicher-quattro-xl-"
            "anker-solix-1775174/"
        )
        # WordPress tail "The post ... appeared first on t3n." stripped.
        assert "appeared first on t3n" not in first["description"]
        assert first["published"] == "2026-11-26T08:05:08+00:00"
        assert first["author"] == "t3n Redaktion"
        # Display-name categories in this feed.
        assert first["tags"] == [
            "Hardware & Gadgets", "Balkonkraftwerk", "Black Friday",
        ]
        # The WordPress feed carries no image enclosure.
        assert first["image_url"] is None


class TestMerge:
    def test_merged_unique_count(self):
        # 20 main + 10 news, 8 overlap -> 22 unique articles.
        assert len(_merged()) == 22

    def test_merged_item_unions_tags_and_author(self):
        merged = _merged()
        bf = next(
            i for i in merged if "balkonkraftwerk" in i["link"]
        )
        # Slug tags from the main feed + display tags from the news
        # feed, author from the news feed, image from the main feed.
        assert "black-friday" in bf["tags"]
        assert "Black Friday" in bf["tags"]
        assert bf["author"] == "t3n Redaktion"
        assert bf["image_url"] is not None

    def test_merged_sorted_newest_first(self):
        merged = _merged()
        pubs = [i["published"] for i in merged]
        assert pubs == sorted(pubs, reverse=True)


class TestArticle:
    def test_free_article(self):
        art = dom.parse_article(_read("article-free.html"))
        assert art["kind"] == "article"
        assert art["title"] == (
            "Neue Funktion in Whatsapp: So versendest du "
            "Geburtstagsgrüße bis zu 14 Tage im Voraus"
        )
        assert art["author"] == "Noëlle Bölling"
        assert art["published"] == "2026-11-26T09:30:26+00:00"
        # Section comes from the JSON-LD articleSection field.
        assert art["section"] == "Software & Entwicklung"
        assert art["word_count"] == 393
        assert art["paywalled"] is False
        assert art["teaser_only"] is False

    def test_free_article_body_is_json_ld(self):
        # t3n pages DO carry a real JSON-LD articleBody inside
        # @graph — it is the body (the SSR <article> paragraphs are
        # only the fallback).
        art = dom.parse_article(_read("article-free.html"))
        assert art["body"].startswith(
            "Der Messenger baut seinen Funktionsumfang stetig aus."
        )
        assert "Whatsapp hat in den vergangenen Wochen" in art["body"]
        assert art["description"].startswith(
            "Der Messenger baut seinen Funktionsumfang fortlaufend aus."
        )

    def test_free_article_body_has_no_promo(self):
        art = dom.parse_article(_read("article-free.html"))
        assert "Verpasse keine News mehr!" not in art["body"]

    def test_paywalled_article_returns_teaser_only(self):
        art = dom.parse_article(_PAYWALLED_HTML)
        assert art["kind"] == "article"
        assert art["title"] == "Test: Bezahlartikel"
        assert art["author"] == "Max Muster"
        assert art["published"] == "2026-11-26T08:00:00+00:00"
        assert art["section"] == "Software & Entwicklung"
        assert art["paywalled"] is True
        assert art["teaser_only"] is True
        # Only the teaser is exposed — never the full text.
        assert art["body"] == "Nur der Teaser ist frei lesbar."
        assert "Abonnenten" not in art["body"]

    def test_ssr_fallback_filters_promo(self):
        art = dom.parse_article(_SSR_ONLY_HTML)
        assert art["paywalled"] is False
        assert art["author"] == "Erika Muster"
        assert art["section"] == "Künstliche Intelligenz"
        assert "Verpasse keine News mehr!" not in art["body"]
        assert art["body"] == (
            "Erster Absatz des Artikels mit echtem Inhalt.\n\n"
            "Zweiter Absatz des Artikels mit echtem Inhalt."
        )


class TestValidators:
    def test_limit(self):
        assert dom.validate_limit(1) == 1
        assert dom.validate_limit(50) == 50
        with pytest.raises(ValueError):
            dom.validate_limit(0)
        with pytest.raises(ValueError):
            dom.validate_limit(51)


class TestSearchTopicAndDedupe:
    def test_search_items(self):
        merged = _merged()
        found = dom.search_items(merged, "whatsapp")
        assert len(found) == 1
        assert dom.search_items(merged, "WHATSAPP") == found
        assert len(dom.search_items(merged, "ChatGPT")) == 4
        with pytest.raises(ValueError):
            dom.search_items(merged, "   ")

    def test_items_by_topic(self):
        merged = _merged()
        found = dom.items_by_topic(merged, "black-friday")
        assert len(found) == 3
        assert dom.items_by_topic(merged, "BLACK-FRIDAY") == found
        # Display-name tags match too (substring, case-insensitive).
        assert len(dom.items_by_topic(merged, "Black Friday")) == 2
        assert dom.items_by_topic(merged, "Niemand") == []
        with pytest.raises(ValueError):
            dom.items_by_topic(merged, "   ")

    def test_topics_with_counts(self):
        merged = _merged()
        topics = dom.topics_with_counts(merged)
        assert len(topics) == 87
        assert topics[0] == {"topic": "kuenstliche-intelligenz", "count": 9}
        assert {"topic": "Black Friday", "count": 2} in topics
        assert {"topic": "whatsapp", "count": 1} in topics
        counts = [t["count"] for t in topics]
        assert counts == sorted(counts, reverse=True)

    def test_dedupe_sort(self):
        merged = _merged()
        doubled = merged + merged[:5]
        out = dom.dedupe_sort(doubled)
        assert len(out) == 22
        pubs = [i["published"] for i in out]
        assert pubs == sorted(pubs, reverse=True)


class TestFeedGuards:
    def test_parse_rss_rejects_garbage(self):
        with pytest.raises(ValueError):
            dom.parse_rss("<html><body>not rss</body></html>")

    def test_fetch_article_refuses_feed_urls(self):
        with pytest.raises(http_mod.T3nError):
            http_mod.fetch_article("https://t3n.de/rss.xml")
        with pytest.raises(http_mod.T3nError):
            http_mod.fetch_article("https://t3n.de/news/feed/")
        with pytest.raises(http_mod.T3nError):
            http_mod.fetch_article("https://t3n.de/")

    def test_fetch_article_refuses_other_hosts(self):
        with pytest.raises(http_mod.T3nError):
            http_mod.fetch_article(
                "https://www.spiegel.de/politik/deutschland/afd-100.html"
            )
        with pytest.raises(http_mod.T3nError):
            http_mod.fetch_article(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            )

    def test_fetch_feed_refuses_non_feed_urls(self):
        with pytest.raises(http_mod.T3nError):
            http_mod.fetch_feed("https://t3n.de/news/")
        with pytest.raises(http_mod.T3nError):
            http_mod.fetch_feed(
                "https://t3n.de/news/neue-funktion-in-whatsapp-1775472/"
            )


class TestServerEnvelope:
    def test_tools_return_json_envelope(self):
        # Offline: the tools hit the network, so only the error path
        # is exercised here — but the envelope shape is the same.
        from t3n_mcp import server as srv

        out = json.loads(srv.t3n_latest(51))
        assert "error" in out
        assert out["source"] == "t3n.de"
        assert "fetched_at" in out
