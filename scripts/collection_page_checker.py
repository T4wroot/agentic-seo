#!/usr/bin/env python3
"""Check ecommerce collection/category pages for copy, filters, pagination, and crawlability."""

from __future__ import annotations

import argparse
from urllib.parse import parse_qs, urlparse

from schema_required_props import load_source_html
from seo_common import issue, parse_html, print_json_or_text


FILTER_PARAMS = {"filter", "sort", "color", "size", "brand", "price", "min_price", "max_price", "page", "p"}


def rel_values(value) -> set[str]:
    if not value:
        return set()
    if isinstance(value, list):
        return {str(item).lower() for item in value}
    return {str(value).lower()}


def check_collection_page(source: str, timeout: int = 15) -> dict:
    html, final_url, fetch = load_source_html(source, timeout=timeout)
    parsed = parse_html(html, final_url or source) if html else {}
    soup = parsed.get("soup")
    issues = []
    url = final_url or source
    word_count = parsed.get("word_count", 0)
    if word_count < 150:
        issues.append(issue("warning", "Collection page has thin visible copy", url, str(word_count)))
    if not parsed.get("headings", {}).get("h1"):
        issues.append(issue("error", "Collection page is missing H1", url))
    if not parsed.get("meta_description"):
        issues.append(issue("warning", "Collection page is missing meta description", url))
    canonical = parsed.get("canonical")
    params = parse_qs(urlparse(url).query)
    filter_params = sorted(set(params) & FILTER_PARAMS)
    if filter_params and canonical and "?" in canonical:
        issues.append(issue("warning", "Filtered URL canonical keeps query parameters", url, canonical))
    if filter_params and not canonical:
        issues.append(issue("warning", "Filtered URL has no canonical", url, ",".join(filter_params)))
    product_links = []
    for link in parsed.get("links", []):
        href = link.get("href", "")
        text = link.get("text", "")
        if any(token in href.lower() for token in ("/product", "/products/", "/p/")) or text.lower() in {"view", "details", "buy"}:
            product_links.append(href)
    if len(set(product_links)) < 4:
        issues.append(issue("info", "Few crawlable product links detected", url, str(len(set(product_links)))))
    rels = {rel for link in parsed.get("links", []) for rel in rel_values(link.get("rel"))}
    pagination_links = []
    if soup:
        pagination_links = [tag.get("href") for tag in soup.find_all("a", href=True) if tag.get_text(" ", strip=True).lower() in {"next", "prev", "previous"}]
    if "next" not in rels and "prev" not in rels and not pagination_links and any(key in params for key in ("page", "p")):
        issues.append(issue("info", "Paginated URL has no visible next/prev links", url))
    if soup:
        nofollow_filter_links = 0
        for tag in soup.find_all("a", href=True):
            href_params = parse_qs(urlparse(tag.get("href")).query)
            if set(href_params) & FILTER_PARAMS and "nofollow" in rel_values(tag.get("rel")):
                nofollow_filter_links += 1
        if nofollow_filter_links:
            issues.append(issue("info", "Filter links use nofollow; confirm crawl strategy", url, str(nofollow_filter_links)))
    return {
        "source": source,
        "final_url": url,
        "status": fetch.get("status"),
        "word_count": word_count,
        "filter_parameters": filter_params,
        "product_links_detected": len(set(product_links)),
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check ecommerce collection/category page SEO")
    parser.add_argument("source", help="URL or HTML file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    result = check_collection_page(args.source, timeout=args.timeout)
    lines = [
        f"Collection page check for {args.source}",
        f"Words: {result['word_count']}  Product links: {result['product_links_detected']}  Issues: {len(result['issues'])}",
    ] + [f"[{item['severity']}] {item['message']} {item.get('evidence') or ''}" for item in result["issues"][:30]]
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
