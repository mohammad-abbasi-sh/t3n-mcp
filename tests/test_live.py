"""Live tests — hit the real t3n.de RSS feeds and article pages.
Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set T3N_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from t3n_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("T3N_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="T3N_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_latest_live(self):
        out = json.loads(srv.t3n_latest(limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(i["title"] and i["description"] for i in out["items"]))
        self.assertTrue(all("utm_" not in i["link"] for i in out["items"]))
        print(f"\nLIVE latest: {out['count']} items, first: {out['items'][0]['title']}")

    def test_search_live(self):
        out = json.loads(srv.t3n_search_news("ChatGPT", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        print(f"\nLIVE search 'ChatGPT': {out['total_results']} hits")

    def test_by_topic_live(self):
        topics = json.loads(srv.t3n_topics())
        self.assertNotIn("error", topics)
        topic = topics["topics"][0]["topic"]
        out = json.loads(srv.t3n_by_topic(topic, limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(
            any(topic.casefold() in t.casefold() for t in i["tags"])
            for i in out["items"]))
        print(f"\nLIVE by_topic {topic!r}: {out['count']} items")

    def test_topics_live(self):
        out = json.loads(srv.t3n_topics())
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(t["count"] >= 1 for t in out["topics"]))
        print(f"\nLIVE topics: {out['count']} distinct topics")

    def test_get_article_live(self):
        head = json.loads(srv.t3n_latest(limit=1))
        self.assertNotIn("error", head)
        url = head["items"][0]["link"]
        out = json.loads(srv.t3n_get_article(url))
        self.assertNotIn("error", out)
        self.assertEqual(out["url"], url)
        self.assertGreater(out["word_count"], 100)
        self.assertFalse(out["paywalled"])
        self.assertTrue(out["section"])
        print(
            f"\nLIVE article: {out['title']!r} — {out['word_count']} words, "
            f"section {out['section']!r}"
        )

    def test_health_live(self):
        out = json.loads(srv.t3n_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
        print(f"\nLIVE health: {out}")
