<div align="center">

# 🤖 مهارت سئوی ایجنتیک (Agentic SEO Skill)

**[🇮🇷 فارسی (Persian)](README.fa.md) | [🇺🇸 English](README.md)**

[![Release](https://img.shields.io/github/v/release/T4wroot/agentic-seo?style=for-the-badge&color=blue)](https://github.com/T4wroot/agentic-seo/releases)
[![GitHub Pages](https://img.shields.io/github/actions/workflow/status/T4wroot/agentic-seo/deploy-pages.yml?branch=master&label=Live%20Site&style=for-the-badge&color=success)](https://T4wroot.github.io/agentic-seo)
[![Python](https://img.shields.io/badge/Python-91%25-yellow?style=for-the-badge&logo=python)](https://github.com/T4wroot/agentic-seo)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **قدرتمندترین و کامل‌ترین پکیج ۳-در-۱ سئو برای ایجنت‌های هوش مصنوعی** 🚀
</div>

این مخزن (Repository) حاصل ادغام سه پروژه عظیم است و به عنوان یک استاندارد جهانی برای آموزش سئو به ایجنت‌های هوش مصنوعی طراحی شده است:

۱. 📝 **مهارت‌های مارک‌داون (Markdown Skills):** بیش از ۱۶۰ فایل مهارت (اسکیل) مارکتینگ و سئو برای محیط‌های توسعه هوش مصنوعی (مانند Cursor و Claude).
۲. 🐍 **اکوسیستم پیشرفته پایتون:** شامل ۸۹ اسکریپت تخصصی پایتون، ۱۰ ایجنت متخصص (Specialist Agents) و نصب‌کننده‌های چندپلتفرمی.
۳. ✨ **رابط کاربری تعاملی (Interactive UI):** یک لندینگ پیج و داشبورد فوق‌حرفه‌ای با طراحی Glassmorphism (برای مشاهده کلیک کنید: [سایت زنده](https://T4wroot.github.io/agentic-seo)).

---

## 🌟 قابلیت‌های کلیدی

- **موتور استدلال جامع:** اسکریپت‌های سبک پایتون که به عنوان منبع حقیقت (Source of Truth) برای استخراج مدارک و استدلال‌های سئو عمل می‌کنند.
- **تیم ۱۰ نفره ایجنت‌ها:** شامل ایجنت بررسی محتوا، ایجنت تحلیل فنی، ایجنت اسکیما (Schema)، ایجنت بررسی سئوی گیت‌هاب و...
- **ضد الگوها (Anti-Patterns):** لیستی از اشتباهات مرگبار سئو که ایجنت‌ها تحت هر شرایطی باید از آن‌ها دوری کنند (مثل حلقه‌های کنونیکال، مشکل CLS و آدم‌خواری کلمات کلیدی).
- **قوانین تخصصی:** بهترین شیوه‌ها برای سئوی محلی (Local SEO)، فروشگاهی (E-commerce) و برنامه‌نویسی (Programmatic SEO).

---

## 💻 سازگاری با محیط‌های توسعه (IDE)

این ابزار با تمام ایجنت‌ها و دستیارهای برنامه‌نویسی هوشمند سازگار است:
- **Cursor** (قوانین خودکار `.cursorrules` و MDC)
- **Windsurf** (پشتیبانی کامل از `.windsurf/rules`)
- **Claude Code** (یکپارچگی مستقیم با مهارت‌های کلود)
- **Antigravity IDE**
- **Cline**
- **GitHub Copilot**

---

## 📦 محتویات بسته (Inventory)

- **۱۶** مهارت فرعی تخصصی (Sub-skills)
- **۱۰** ایجنت متخصص (Specialist Agents)
- **۸۹** اسکریپت پایتون در پوشه `scripts/` برای اتوماسیون کامل بررسی‌های سئو.

---

## 🚀 روش نصب

شما می‌توانید با یک دستور ساده در ترمینال خود (سیستم‌های لینوکس و مک)، این پکیج عظیم را برای ایجنت خود نصب کنید:
```bash
# نصب پیش‌فرض برای تمام محیط‌های توسعه
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --online
```

کاربران **ویندوز** نیز می‌توانند به راحتی از PowerShell استفاده کنند:
```powershell
irm https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.ps1 -OutFile install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online
```

> **نکته:** نصب‌کننده هوشمند ما به صورت خودکار تشخیص می‌دهد که شما از چه ادیتوری استفاده می‌کنید و فایل‌ها را در جای درست قرار می‌دهد.

---

## 💡 نمونه پرامپت‌ها (دستورات)

کافیست در ادیتور هوش مصنوعی خود (مثلاً کِرسِر)، یکی از دستورات زیر را تایپ کنید:
- "یک آدیت (SEO Audit) کامل روی سایت `example.com` اجرا کن."
- "مشکلات فنی سئوی این آدرس را پیدا کن و گزارش بده."
- "اسکیمای (Schema Markup) این صفحه وبلاگ را بررسی کن."
- "برای من یک پلن استراتژیک ۶ ماهه سئو بنویس."
- "سئوی این ریپازیتوری گیت‌هاب را بررسی کن."

هوش مصنوعی شما به لطف فایل‌های مخفی این پکیج (SKILL.md و اسکریپت‌ها) بلافاصله وارد عمل شده و مانند یک کارشناس سئوی سنیور (Senior SEO Expert) کارهای شما را انجام می‌دهد!
