# t3n-mcp 💻

mcp-name: io.github.mohammad-abbasi-sh/t3n-mcp

Unofficial **read-only** MCP server for **[t3n — digital pioneers](https://t3n.de)** — Germany's well-known tech magazine (yeebase media) — via its two official RSS feeds (rss.xml, 20 items, plus /news/feed/, 10 items, de-duplicated to ~22 unique stories) and article pages, whose full text is read from the JSON-LD NewsArticle `articleBody` inside the `@graph` block (the server-rendered `<article>` paragraphs are the fallback). Latest news, keyword search, stories by topic tag, the topics in today's feeds, and full article text. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory" (Sepehr-style pipeline). Not affiliated with t3n.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "t3n": {
      "command": "uvx",
      "args": ["t3n-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m t3n_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `t3n_latest` | Latest t3n news (both official RSS feeds combined, ~22 unique items), newest first — `limit` 1..50. Every item carries a title, a canonical per-article link, a teaser, tags, an image URL and publish time |
| `t3n_search_news` | Search t3n news by keyword (title + teaser + tags) across both official RSS feeds — `query` (e.g. "ChatGPT" or "Black Friday"), `limit` 1..50 |
| `t3n_by_topic` | Newest t3n stories on one topic tag (the feeds' `<category>` values, e.g. "kuenstliche-intelligenz", "black-friday" or "whatsapp") — `topic` matched case-insensitively as a substring, `limit` 1..50 |
| `t3n_topics` | The topic tags in today's t3n feeds, with how many stories each carries — most stories first |
| `t3n_get_article` | Full text of one t3n article page (JSON-LD NewsArticle `articleBody`, `<article>` paragraphs as fallback) — `url`: a t3n.de article URL (/news/<slug>-<id>/). Returns title, author, publish time, the section from the page's `articleSection` (e.g. "Software & Entwicklung"), body text and word count. A paywalled page returns `paywalled: true` with only the teaser as body — the full text needs a subscription. Feed URLs, the home page and off-site links are refused |
| `t3n_health` | Reachability probe (ok / blocked / error) — one polite request |

Example output (`t3n_latest`, `limit` 1):

```json
{"feed_title": "t3n.de - News", "total_results": 22, "count": 1,
 "items": [
  {"title": "Neue Funktion in Whatsapp: So versendest du Geburtstagsgrüße bis zu 14 Tage im Voraus",
   "link": "https://t3n.de/news/neue-funktion-in-whatsapp-so-versendest-du-geburtstagsgruesse-bis-zu-14-tage-im-voraus-1775472/",
   "description": "Der Messenger baut seinen Funktionsumfang stetig aus. Nutzer:innen können den Versandzeitpunkt von Nachrichten jetzt vorab einplanen. Diese werden in Whatsapp versendet, auch wenn sie selbst offline sind.",
   "published": "2026-11-26T09:30:26+00:00", "author": "t3n Redaktion",
   "tags": ["android", "apps", "ios", "messenger", "server", "whatsapp"],
   "image_url": "https://cdn.t3n.de/news/wp-content/uploads/2025/04/whatsapp.jpg?class=hero"},
  ...]}
```

Notes:
- The server reads **two official RSS feeds** — `https://t3n.de/rss.xml` (20 items, verified live 2026-11-26) and `https://t3n.de/news/feed/` (10 items, WordPress feed). 8 of the 10 news-feed items overlap with the main feed; the two feeds are merged and de-duplicated by canonical link into ~22 unique stories. The merged item unions both versions' tags and prefers the non-empty author/image.
- **No per-section feeds exist:** `/news/rss.xml`, `/magazin/rss.xml`, `/rss/news.xml` and `/feed/` all 404 — there is NO section tool. The section of one article is reported by `t3n_get_article` from the page's `articleSection` (e.g. "Software & Entwicklung").
- The main feed's `<category>` values are lowercase tag slugs (android, kuenstliche-intelligenz, black-friday, ...); the news feed's are display names ("Hardware & Gadgets", "Black Friday", ...). Both are kept as the item's tags; `t3n_by_topic` matches case-insensitively as a substring, so "hardware" matches both.
- The main feed carries **no author**; the news feed carries `dc:creator` ("t3n Redaktion"). The real author of one article is reported by `t3n_get_article` from the JSON-LD author (e.g. "Noëlle Bölling"). The main feed carries an image enclosure on every item; the news feed carries none.
- Feed links carry `utm_source=rss` tracking params — links are canonicalised (query stripped) before they are returned.
- Every main-feed teaser ends with the read-more marker **"weiterlesen auf t3n.de"** — it is stripped from the description. WordPress-feed teasers end with **"The post … appeared first on t3n."** — that tail is stripped too (the "[…]" truncation marker mid-text is kept: it is honest truncation).
- **Article text, honestly:** t3n pages DO carry a real JSON-LD `articleBody` inside the `@graph` block (sampled: 2,936 characters / 393 words and 4,152 characters / 620 words on free articles). The body is whitespace-normalised; the `<article>` `<p>` tags are the fallback when `articleBody` is absent (newsletter promo "Verpasse keine News mehr!", photo captions "Foto: ..." and byline fragments filtered).
- **Paywall, honestly:** no paywalled article was found in the sampled pages on 2026-11-26 (all `isAccessibleForFree: true` — including a story tagged as a t3n-PRO article) — t3n news articles are generally free to read. The paywall branch is still implemented defensively: a page with `isAccessibleForFree: false` returns `paywalled: true` with only the teaser as body — never fabricated text.
- t3n article links carry **no `.html` suffix** (they end in `/news/<slug>-<id>/`) — so no suffix filter is applied.
- Data: t3n public RSS feeds and article pages — no key, no login, read-only.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, parses the two real captured feeds plus one real article page (a free article with a real JSON-LD `articleBody` inside `@graph`); the paywalled branch and the SSR fallback use small synthetic pages
- `tests/test_live.py` — cautious live requests against t3n.de

Tests: 29/29 green (23 offline + 6 live, 2026-11-26).

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — free for personal and non-commercial use; commercial use needs a separate license (see LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
