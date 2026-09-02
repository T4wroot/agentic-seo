<div align="center">

# 🤖 مهارت سئوی ایجنتیک (Agentic SEO Skill)

**[🇮🇷 فارسی (Persian)](README.fa.md) | [🇺🇸 English](README.md)**

[![Release](https://img.shields.io/github/v/release/T4wroot/agentic-seo?style=for-the-badge&color=blue)](https://github.com/T4wroot/agentic-seo/releases)
[![GitHub Pages](https://img.shields.io/github/actions/workflow/status/T4wroot/agentic-seo/deploy-pages.yml?branch=master&label=Live%20Site&style=for-the-badge&color=success)](https://T4wroot.github.io/agentic-seo)
[![Python](https://img.shields.io/badge/Python-91%25-yellow?style=for-the-badge&logo=python)](https://github.com/T4wroot/agentic-seo)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

> **جامع‌ترین پکیج ۳-در-۱ سئو و بهینه‌سازی موتورهای جستجوی هوش مصنوعی (GEO & AEO) ویژه دستیاران و ایجنت‌های کدنویسی** 🚀
</div>

این مخزن حاصل ادغام سه پروژه کاربردی و قدرتمند است که به عنوان یک استاندارد نوین برای مجهز کردن ایجنت‌های هوش مصنوعی (AI Agents) به دانش عمیق سئو طراحی شده است:

1. 📝 **مهارت‌های مارک‌داون (Markdown Skills):** بیش از ۱۶۰ مهارت بومی مارکتینگ، سئو و بازاریابی محتوا برای IDEها.
2. 🐍 **اکوسیستم پیشرفته پایتون:** شامل ۸۹ اسکریپت تحلیلی (۸۸ اسکریپت پایتون + ۱ اسکریپت شل)، ۱۰ ایجنت متخصص (Specialist Agents) و نصب‌کننده‌های اختصاصی برای تمام محیط‌های توسعه.
3. ✨ **داشبورد تعاملی (Interactive UI):** داشبورد شیشه‌ای مدرن (Glassmorphism) برای مشاهده زنده آمار و قابلیت‌ها ([مشاهده سایت زنده](https://T4wroot.github.io/agentic-seo)).

---

## 🌟 قابلیت‌های برجسته

- 🎯 **استدلال مبتنی بر داده (Evidence-Based):** اسکریپت‌های پایتون مستقیماً دیتای واقعی سئو (وضعیت ایندکس، اسکیما، Core Web Vitals، ربات‌ها، ریدایرکت‌ها) را استخراج کرده و به صورت JSON و گزارش Markdown در اختیار مدل قرار می‌دهند.
- 👥 **تیم ۱۰ ایجنت تخصصی:** ایجنت‌های مجزا برای تحلیل فنی (Technical SEO)، ارزیابی محتوا و E-E-A-T، ساختار اسکیما (Schema.org)، سئوی ریپازیتوری‌های گیت‌هاب (GitHub SEO) و بهینه‌سازی برای جستجوی هوش مصنوعی (GEO/AEO).
- 🚫 **پیشگیری از ضد الگوها (Anti-Patterns):** جلوگیری خودکار از اشتباهات متداول مانند حلقه‌های کنونیکال، جهش‌های لایه‌بندی (CLS) و تداخل کلمات کلیدی (Keyword Cannibalization).
- 🔍 **بهینه‌سازی برای موتورهای جستجوی نسل جدید (GEO & AEO):** بهینه‌سازی محتوا برای دیده‌شدن در Google AI Overviews، ChatGPT Search و Perplexity.

---

## 💻 سازگاری بومی با انواع محیط‌های توسعه (IDEs)

این پکیج به صورت خودکار با فرمت استاندارد و بومی هر ادیتور نصب و پیکربندی می‌شود:

| ابزار / IDE | مسیر نصب | فرمت بومی |
|---|---|---|
| **Antigravity IDE** | `<project>/.agent/skills/seo` | Skill Directory |
| **Cursor** | `.cursor/rules/seo.mdc` + `.cursor/skills/seo/` | MDC Rule + Skills |
| **Claude Code** | `~/.claude/skills/seo` | Skill Directory |
| **Windsurf** | `.windsurf/rules/seo.md` + `.windsurf/skills/seo/` | Windsurf Rule |
| **Codex CLI** | `~/.codex/skills/seo` | Skill Directory |
| **Claude Cowork** | `<project>/.claude/skills/seo` | Project-scoped Skill |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Repo Instructions |
| **Continue.dev** | `.continue/prompts/seo.prompt` | Slash Command |
| **Cline** | `.clinerules` | Project Rules |

---

## 🚀 روش نصب سریع (در کمتر از ۱ دقیقه)

### لینوکس و مک (Linux & macOS)
```bash
# نصب پیش‌فرض
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --online

# یا نصب اختصاصی برای پروژه جاری در یک IDE خاص (مثلا Antigravity یا Cursor):
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --target antigravity
```

### ویندوز (Windows PowerShell)
```powershell
irm https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.ps1 -OutFile install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online
```

---

## 🎯 پرامپت‌های آماده و کاربردی (Copy & Paste Prompts)

پس از نصب اسکیل، کافیست پرامپت مورد نظرتان را کپی کرده و در چت هوش مصنوعی (Antigravity، Cursor، Claude و...) پیست کنید:

### 🌟 ۱. پرامپت جامع صفر تا صد (Master Audit Prompt)
> *مناسب برای بررسی ۳۶۰ درجه هر نوع وب‌سایت (فروشگاهی، شرکتی، وبلاگ، پورتال و...):*
```text
یک آدیت کامل و ۳۶۰ درجه روی وب‌سایت https://example.com انجام بده.
تمام بخش‌های زیر را بررسی و تحلیل کن:
۱. سئوی فنی: بررسی robots.txt، سایت‌مپ، ریدایرکت‌ها، هدرهای امنیتی و ایندکس‌پذیری
۲. سرعت و Core Web Vitals: فاکتورهای LCP، CLS و سرعت بارگذاری
۳. کیفیت محتوا و E-E-A-T: خوانایی، عمق اطلاعات و ساختار تگ‌های هدینگ (H1-H6)
۴. ساختار اسکیما (Schema.org): اعتبارسنجی و تولید کدهای ساختاریافته JSON-LD
۵. تصاویر و لینک‌ها: اتریبیوت‌های Alt، تصاویر غیربهینه، لینک‌های شکسته و لینک‌سازی داخلی
۶. هوش مصنوعی (GEO/AEO): بررسی فایل llms.txt و مجوزهای ربات‌های هوش مصنوعی (GPTBot و...)

در پایان داشبورد گرافیکی audit-report.html، گزارش کامل FULL-AUDIT-REPORT.md و اکشن‌پلن گام‌به‌گام ACTION-PLAN.md را بساز.
```

### 🛒 ۲. سایت‌های فروشگاهی (E-Commerce SEO)
```text
صفحه محصول یا دسته‌بندی https://myshop.com/product/shoes را برای سئوی فروشگاهی تحلیل کن:
- اسکیمای Product و AggregateOffer و Reviews را استخراج و اعتبارسنجی کن.
- تگ‌های Alt تصاویر محصول و لود تنبل (Lazy Loading) را بررسی کن.
- توضیحات محصول و جذابیت متاتگ‌ها (CTR) را ارزیابی کن و کدهای اسکیمای بهینه را بهم بده.
```

### 📰 ۳. وبلاگ‌ها و مقالات (Blog & Content SEO)
```text
مقاله https://example.com/blog/seo-guide را با زیر‌مهارت‌های seo-article و seo-content آنالیز کن:
- امتیاز خوانایی (Readability) و تطابق با معیارهای E-E-A-T گوگل را بسنج.
- ساختار هدینگ‌ها، کلمات کلیدی LSI و خطر آدم‌خواری کلمات کلیدی (Keyword Cannibalization) را مشخص کن.
- اسکیمای Article و FAQPage آماده به صورت JSON-LD برای قرار دادن در سایت تولید کن.
```

### 🏢 ۴. سایت‌های شرکتی، خدماتی و سئوی محلی (Corporate & Local SEO)
```text
سایت شرکتی/خدماتی https://mycompany.com را تحلیل کن:
- اسکیمای Organization و LocalBusiness همراه با ساعات کاری، آدرس و شماره تماس را تولید کن.
- سیگنال‌های اعتماد (Trust Signals) شامل درباره ما، تماس با ما و سیاست حریم خصوصی را ارزیابی کن.
- ساختار و انکرتکست‌های لینک‌سازی داخلی را برای صفحات خدمات اصلی بهینه‌سازی کن.
```

### 🤖 ۵. بهینه‌سازی برای هوش مصنوعی (GEO & AEO)
```text
وب‌سایت https://example.com را برای موتورهای جستجوی هوش مصنوعی (ChatGPT Search, Perplexity, Google AI Overviews) بهینه‌سازی کن:
- وضعیت دسترسی ربات‌های AI (مثل GPTBot، ClaudeBot و PerplexityBot) را در robots.txt چک کن.
- یک فایل استاندارد llms.txt برای معرفی دقیق محتوا و ساختار سایت به هوش مصنوعی بساز.
- پاسخ‌های کلیدی محتوا را برای برنده شدن در Featured Snippets بهینه‌سازی کن.
```

### ⚡ ۶. بهینه‌سازی تصاویر و رسانه‌ها (Image SEO)
```text
صفحه https://example.com را با زیر‌مهارت seo-images بررسی کن:
- تمام تصاویر بدون تگ alt یا با تگ‌های نامناسب را لیست کن.
- تصاویری که فرمت مدرن (WebP/AVIF) ندارند یا ابعاد صریح ندارند و باعث پرش صفحه (CLS) می‌شوند را پیدا کن و کدهای بهینه‌شده HTML را ارائه بده.
```

### 🐙 ۷. سئو و افزایش رتبه مخزن گیت‌هاب (GitHub SEO)
```text
ریپازیتوری https://github.com/owner/repo را از نظر سئوی گیت‌هاب تحلیل کن:
- کلمات کلیدی تاپیک‌ها، عنوان مخزن و تگ‌های About را با رقبای برتر مقایسه کن.
- گزارش GITHUB-SEO-REPORT.md و اکشن پلن ارتقای رتبه در سرچ گیت‌هاب و گوگل را تولید کن.
```

---

## 📦 فهرست دارایی‌ها و ابزارها (Inventory)

- **۱۶ مهارت فرعی تخصصی (Sub-Skills):**
  - `seo audit`: آدیت جامع ۳۶۰ درجه وب‌سایت همراه با امتیازدهی و پلن اقدام.
  - `seo technical`: بررسی خزش (Crawlability)، ایندکس‌پذیری، ربات‌های هوش مصنوعی و امنیت.
  - `seo content`: ارزیابی کیفیت محتوا طبق آخرین استانداردهای گوگل و E-E-A-T.
  - `seo schema`: اعتبارسنجی و تولید کدهای ساختاریافته JSON-LD (Schema.org).
  - `seo geo`: بهینه‌سازی برای موتورهای جستجوی هوش مصنوعی (Generative Engine Optimization).
  - `seo images`: بهینه‌سازی جامع تصاویر و کاهش CLS.
  - `seo links`: تحلیل لینک‌های داخلی، انکرتکست‌ها و لینک‌های شکسته.
  - `seo sitemap`: ارزیابی و تولید نقشه‌های سایت XML.
  - `seo aeo`: بهینه‌سازی برای پاسخ‌های سریع و جستجوی صوتی.
  - `seo hreflang`: سئوی بین‌المللی و چندزبانه.
  - `seo programmatic`: سئوی برنامه‌نویسی‌شده صفحات مقیاس‌پذیر.
  - `seo github`: تحلیل سئو، کلمات کلیدی، رقبا و ساختار مخازن گیت‌هاب.
  - و ۴ زیر‌مهارت تکمیلی دیگر.
- **۱۰ ایجنت متخصص (Specialist Agents)**
- **۸۹ اسکریپت تحلیلی** در پوشه `scripts/` برای جمع‌آوری شواهد و ایجاد گزارش‌های بدون خطا.

---

## 🤝 مشارکت در پروژه (Contributing)

ما از تمامی مشارکت‌ها (افزودن مهارت‌های جدید، بهبود اسکریپت‌ها، ترجمه و رفع باگ‌ها) استقبال می‌کنیم! لطفاً راهنمای [CONTRIBUTING.md](CONTRIBUTING.md) را مطالعه کنید.

## 📄 لایسنس

این پروژه تحت لایسنس [MIT](LICENSE) منتشر شده است و استفاده شخصی و تجاری از آن کاملاً آزاد و رایگان است.
