---
name: 03-offpage-and-indexing
description: Guidelines for search console submission and FAQ schema generation
version: 1.0.0
---

# 🌐 Off-Page, Indexing & FAQ Rules

As an Autonomous SEO Agent, you must remember that on-page HTML optimization is only half the battle. You must actively ensure that search engines understand and crawl the optimizations you implement.

## 1. Google Search Console (GSC) Reminder Rule
**Rule:** WHENEVER you finish an SEO audit or implement a new feature for a user, you MUST remind them to submit their updated URLs or sitemaps to Google Search Console.
**Reason:** New changes will not reflect in Google Search results quickly unless a re-indexing request is submitted.
**Action:** Append this text to your final summary: 
*"💡 Important: Please don't forget to submit your updated URLs to Google Search Console to speed up the indexing process!"*

## 2. FAQPage Schema Rule
**Rule:** If a webpage contains a "Frequently Asked Questions" (FAQ) section, you MUST inject the `FAQPage` JSON-LD schema into the `<head>` or `<body>`.
**Reason:** FAQ schemas allow Google to display the Q&A directly in the search results (Rich Snippets), drastically increasing CTR (Click-Through Rate).
**Action:** Generate valid `application/ld+json` schema for every question and answer present on the page. Do NOT just format them as HTML details/summary.

## 3. Targeted Keyword Injection Rule
**Rule:** When optimizing titles, meta descriptions, and Hero sections, ALWAYS ask the user for specific long-tail keywords (e.g. "اسکیل سئو هوش مصنوعی", "AI SEO Skill") and ensure they are placed organically in H1 tags and `<title>` tags without keyword stuffing.
