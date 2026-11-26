# t3n-mcp 💻

mcp-name: io.github.mohammad-abbasi-sh/t3n-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[t3n — دیجیتال پایونیرز](https://t3n.de)** — مجله فناوری شناخته‌شده آلمان (yeebase media) — از طریق دو فید RSS رسمی (rss.xml با ۲۰ مورد، به‌علاوه /news/feed/ با ۱۰ مورد، پس از حذف موارد تکراری حدود ۲۲ خبر یکتا) و صفحات مقاله که متن کامل آن‌ها از `articleBody` در JSON-LD NewsArticle داخل بلوک `@graph` خوانده می‌شود (پاراگراف‌های `<article>` رندرشده در سرور، جایگزین است). تازه‌ترین اخبار، جست‌وجوی کلیدواژه، مقاله‌ها بر اساس برچسب موضوعی، موضوع‌های فیدهای امروز و متن کامل مقاله. بدون کلید، بدون ورود.

> ساخته‌شده توسط محمد عباسی در چارچوب «کارخانه MCP آلمان». وابسته به t3n نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی کلاینت MCP اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m t3n_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------------|
| `t3n_latest` | تازه‌ترین اخبار t3n (هر دو فید RSS رسمی با هم، حدود ۲۲ مورد یکتا)، جدیدترین اول — `limit` از ۱ تا ۵۰. هر مورد عنوان، لینک یکتای مقاله، تیزر، برچسب‌ها، آدرس تصویر و زمان انتشار دارد |
| `t3n_search_news` | جست‌وجوی اخبار t3n با کلیدواژه (عنوان + تیزر + برچسب‌ها) در هر دو فید RSS رسمی — `query` (مثلاً «ChatGPT» یا «Black Friday»)، `limit` از ۱ تا ۵۰ |
| `t3n_by_topic` | جدیدترین مقاله‌های t3n درباره یک برچسب موضوعی (مقادیر `<category>` در فیدها، مثلاً «kuenstliche-intelligenz»، «black-friday» یا «whatsapp») — `topic` به‌صورت زیررشته و بدون حساسیت به بزرگی و کوچکی حروف تطبیق داده می‌شود، `limit` از ۱ تا ۵۰ |
| `t3n_topics` | برچسب‌های موضوعی فیدهای امروز t3n با تعداد مقاله‌های هر یک — بیشترین اول |
| `t3n_get_article` | متن کامل یک صفحه مقاله t3n (JSON-LD NewsArticle `articleBody`، پاراگراف‌های `<article>` به‌عنوان جایگزین) — `url`: آدرس مقاله t3n.de (‎/news/<slug>-<id>/‎). عنوان، نویسنده، زمان انتشار، بخش مقاله از `articleSection` صفحه (مثلاً «Software & Entwicklung»)، متن و تعداد کلمات را برمی‌گرداند. صفحه پولی `paywalled: true` با فقط تیزر برمی‌گرداند — متن کامل نیازمند اشتراک است. آدرس‌های فید، صفحه اصلی و لینک‌های خارجی رد می‌شوند |
| `t3n_health` | بررسی دسترسی (ok / blocked / error) — یک درخواست مؤدبانه |

نمونه خروجی (`t3n_latest` با `limit` برابر ۱):

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

نکته‌ها:
- سرور **دو فید RSS رسمی** را می‌خواند — `https://t3n.de/rss.xml` (۲۰ مورد، تأیید زنده در ۲۰۲۶-۱۱-۲۶) و `https://t3n.de/news/feed/` (۱۰ مورد، فید وردپرس). ۸ مورد از ۱۰ مورد فید اخبار با فید اصلی هم‌پوشانی دارند؛ دو فید با هم ادغام و بر اساس لینک یکتا حدود ۲۲ خبر یکتا می‌شوند. مورد ادغام‌شده برچسب‌های هر دو نسخه را با هم دارد و نویسنده/تصویر غیرخالی را ترجیح می‌دهد.
- **فید جداگانه برای هر بخش وجود ندارد:** `/news/rss.xml`، `/magazin/rss.xml`، `/rss/news.xml` و `/feed/` همگی ۴۰۴ برمی‌گردانند — ابزار بخش وجود ندارد. بخش هر مقاله را `t3n_get_article` از `articleSection` صفحه گزارش می‌کند (مثلاً «Software & Entwicklung»).
- مقادیر `<category>` در فید اصلی اسلاگ‌های برچسب با حروف کوچک‌اند (android، kuenstliche-intelligenz، black-friday و...)؛ در فید اخبار نام‌های نمایشی‌اند («Hardware & Gadgets»، «Black Friday» و...). هر دو به‌عنوان برچسب مورد حفظ می‌شوند؛ `t3n_by_topic` بدون حساسیت به بزرگی و کوچکی حروف و به‌صورت زیررشته تطبیق می‌دهد، پس «hardware» هر دو را می‌گیرد.
- فید اصلی **نویسنده ندارد**؛ فید اخبار `dc:creator` («t3n Redaktion») دارد. نویسنده واقعی هر مقاله را `t3n_get_article` از نویسنده JSON-LD گزارش می‌کند (مثلاً «Noëlle Bölling»). فید اصلی برای هر مورد تصویر (enclosure) دارد؛ فید اخبار تصویر ندارد.
- لینک‌های فید پارامترهای ردیابی `utm_source=rss` دارند — لینک‌ها پیش از برگرداندن یکتاسازی می‌شوند (query حذف می‌شود).
- هر تیزر فید اصلی با نشان «ادامه مطلب» **«weiterlesen auf t3n.de»** تمام می‌شود — از توضیح حذف می‌شود. تیزرهای فید وردپرس با **«The post … appeared first on t3n.»** تمام می‌شوند — آن دنباله هم حذف می‌شود (نشان «[…]» وسط متن می‌ماند: کوتاه‌سازی صادقانه است).
- **متن مقاله، صادقانه:** صفحات t3n واقعاً `articleBody` در JSON-LD داخل بلوک `@graph` دارند (نمونه: ۲٬۹۳۶ کاراکتر / ۳۹۳ کلمه و ۴٬۱۵۲ کاراکتر / ۶۲۰ کلمه در مقاله‌های رایگان). متن نرمال‌سازی فاصله می‌شود؛ پاراگراف‌های `<article>` جایگزین‌اند وقتی `articleBody` نباشد (تبلیغ خبرنامه «Verpasse keine News mehr!»، زیرنویس عکس‌ها «Foto: ...» و تکه‌های نام نویسنده فیلتر می‌شوند).
- **پی‌وال، صادقانه:** در نمونه‌های ۲۰۲۶-۱۱-۲۶ هیچ مقاله پولی پیدا نشد (همه `isAccessibleForFree: true` — از جمله مقاله‌ای با برچسب t3n-PRO) — مقاله‌های خبری t3n عموماً رایگان‌اند. شاخه پی‌وال همچنان به‌صورت دفاعی پیاده شده: صفحه‌ای با `isAccessibleForFree: false` با `paywalled: true` و فقط تیزر برمی‌گردد — هرگز متن ساختگی.
- لینک‌های مقاله t3n **پسوند `.html` ندارند** (با ‎/news/<slug>-<id>/‎ تمام می‌شوند) — پس فیلتر پسوند اعمال نمی‌شود.
- داده: فیدهای RSS عمومی و صفحات مقاله t3n — بدون کلید، بدون ورود، فقط‌خواندنی.

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — آفلاین، دو فید واقعی ضبط‌شده به‌علاوه یک صفحه مقاله واقعی (مقاله رایگان با `articleBody` واقعی در JSON-LD داخل `@graph`) را تجزیه می‌کند؛ شاخه پی‌وال و جایگزین SSR از صفحات کوچک مصنوعی استفاده می‌کنند
- `tests/test_live.py` — درخواست‌های زنده محتاطانه به t3n.de

تست‌ها: ۲۹ از ۲۹ سبز (۲۳ آفلاین + ۶ زنده، ۲۰۲۶-۱۱-۲۶).

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — رایگان برای استفاده شخصی و غیرتجاری؛ استفاده تجاری نیازمند مجوز جداگانه است (به LICENSE مراجعه کنید).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
