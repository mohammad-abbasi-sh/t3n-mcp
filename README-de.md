# t3n-mcp 💻

mcp-name: io.github.mohammad-abbasi-sh/t3n-mcp

Inoffizieller **schreibgeschützter** MCP-Server für **[t3n — digital pioneers](https://t3n.de)** — Deutschlands bekanntes Tech-Magazin (yeebase media) — über zwei offizielle RSS-Feeds (rss.xml, 20 Einträge, plus /news/feed/, 10 Einträge, dedupliziert auf ~22 einzigartige Artikel) und Artikelseiten, deren Volltext aus dem JSON-LD-NewsArticle-`articleBody` im `@graph`-Block gelesen wird (die serverseitig gerenderten `<article>`-Absätze sind der Fallback). Neueste Meldungen, Stichwortsuche, Artikel nach Themen-Tag, die Themen der heutigen Feeds und Volltexte. Kein Schlüssel, kein Login.

> Gebaut von Mohammad Abbasi im Rahmen der „Germany MCP factory". Nicht mit t3n verbunden.

## Für KI-Agenten

In die MCP-Client-Konfiguration eintragen (stdio):

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

Oder lokal starten: `python -m t3n_mcp.server` (benötigt `mcp<2`, `httpx`).

## Werkzeuge

| Werkzeug | Beschreibung |
|------|-------------|
| `t3n_latest` | Neueste t3n-Meldungen (beide offiziellen RSS-Feeds kombiniert, ~22 einzigartige Einträge), neueste zuerst — `limit` 1..50. Jeder Eintrag hat Titel, kanonischen Artikel-Link, Teaser, Tags, Bild-URL und Veröffentlichungszeit |
| `t3n_search_news` | Stichwortsuche in den t3n-Meldungen (Titel + Teaser + Tags) über beide offiziellen RSS-Feeds — `query` (z. B. "ChatGPT" oder "Black Friday"), `limit` 1..50 |
| `t3n_by_topic` | Neueste t3n-Artikel zu einem Themen-Tag (die `<category>`-Werte der Feeds, z. B. "kuenstliche-intelligenz", "black-friday" oder "whatsapp") — `topic` wird als Teilstring ohne Beachtung von Groß-/Kleinschreibung verglichen, `limit` 1..50 |
| `t3n_topics` | Die Themen-Tags der heutigen t3n-Feeds mit der Anzahl der Artikel je Tag — häufigste zuerst |
| `t3n_get_article` | Volltext einer t3n-Artikelseite (JSON-LD-NewsArticle-`articleBody`, `<article>`-Absätze als Fallback) — `url`: eine t3n.de-Artikel-URL (/news/<slug>-<id>/). Gibt Titel, Autor:in, Veröffentlichungszeit, den Ressortnamen aus der `articleSection` der Seite (z. B. "Software & Entwicklung"), Text und Wortzahl zurück. Eine Bezahlseite gibt `paywalled: true` mit nur dem Teaser als Text zurück — der Volltext braucht ein Abo. Feed-URLs, die Startseite und externe Links werden abgelehnt |
| `t3n_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

Beispielausgabe (`t3n_latest`, `limit` 1):

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

Hinweise:
- Der Server liest **zwei offizielle RSS-Feeds** — `https://t3n.de/rss.xml` (20 Einträge, live verifiziert 2026-11-26) und `https://t3n.de/news/feed/` (10 Einträge, WordPress-Feed). 8 der 10 Einträge des News-Feeds überschneiden sich mit dem Hauptfeed; beide Feeds werden zusammengeführt und per kanonischem Link auf ~22 einzigartige Artikel dedupliziert. Der zusammengeführte Eintrag vereint die Tags beider Versionen und bevorzugt Autor:in bzw. Bild, sofern vorhanden.
- **Keine Feeds pro Ressort:** `/news/rss.xml`, `/magazin/rss.xml`, `/rss/news.xml` und `/feed/` geben alle 404 zurück — es gibt KEIN Ressort-Werkzeug. Das Ressort eines Artikels meldet `t3n_get_article` aus der `articleSection` der Seite (z. B. "Software & Entwicklung").
- Die `<category>`-Werte des Hauptfeeds sind kleingeschriebene Tag-Slugs (android, kuenstliche-intelligenz, black-friday, ...); die des News-Feeds sind Anzeigenamen ("Hardware & Gadgets", "Black Friday", ...). Beide bleiben als Tags des Eintrags erhalten; `t3n_by_topic` vergleicht ohne Beachtung von Groß-/Kleinschreibung als Teilstring, sodass "hardware" beides trifft.
- Der Hauptfeed enthält **keine Autor:innen**; der News-Feed enthält `dc:creator` ("t3n Redaktion"). Die echte Autor:in eines Artikels meldet `t3n_get_article` aus dem JSON-LD-Autor (z. B. "Noëlle Bölling"). Der Hauptfeed enthält bei jedem Eintrag ein Bild (Enclosure); der News-Feed enthält keines.
- Feed-Links tragen `utm_source=rss`-Tracking-Parameter — Links werden vor der Rückgabe kanonisiert (Query entfernt).
- Jeder Teaser des Hauptfeeds endet mit dem Weiterlesen-Hinweis **"weiterlesen auf t3n.de"** — er wird aus der Beschreibung entfernt. WordPress-Feed-Teaser enden mit **"The post … appeared first on t3n."** — auch dieser Anhang wird entfernt (die "[…]"-Kürzungsmarke im Text bleibt: sie ist ehrliche Kürzung).
- **Artikeltext, ehrlich:** t3n-Seiten enthalten DOCH einen echten JSON-LD-`articleBody` im `@graph`-Block (Stichprobe: 2.936 Zeichen / 393 Wörter und 4.152 Zeichen / 620 Wörter bei kostenlosen Artikeln). Der Text wird whitespace-normalisiert; die `<article>`-`<p>`-Tags sind der Fallback, wenn `articleBody` fehlt (Newsletter-Werbung "Verpasse keine News mehr!", Bildunterschriften "Foto: ..." und Byline-Fragmente werden gefiltert).
- **Paywall, ehrlich:** In den Stichproben vom 2026-11-26 wurde kein Bezahlartikel gefunden (alle `isAccessibleForFree: true` — darunter ein als t3n-PRO-Artikel markierter Artikel) — t3n-News-Artikel sind in der Regel frei lesbar. Der Paywall-Zweig ist trotzdem defensiv umgesetzt: Eine Seite mit `isAccessibleForFree: false` gibt `paywalled: true` mit nur dem Teaser als Text zurück — niemals erfundenen Text.
- t3n-Artikel-Links haben **kein `.html`-Suffix** (sie enden auf `/news/<slug>-<id>/`) — daher wird kein Suffix-Filter angewendet.
- Daten: öffentliche RSS-Feeds und Artikelseiten von t3n — kein Schlüssel, kein Login, nur lesend.

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, parst die beiden echten, aufgezeichneten Feeds plus eine echte Artikelseite (ein kostenloser Artikel mit echtem JSON-LD-`articleBody` in `@graph`); der Paywall-Zweig und der SSR-Fallback nutzen kleine synthetische Seiten
- `tests/test_live.py` — vorsichtige Live-Anfragen an t3n.de

Tests: 29/29 grün (23 offline + 6 live, 2026-11-26).

## Lizenz

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — kostenlos für persönliche und nicht-kommerzielle Nutzung; kommerzielle Nutzung braucht eine separate Lizenz (siehe LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
