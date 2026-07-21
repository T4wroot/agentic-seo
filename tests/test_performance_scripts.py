import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_fixture(tmp_path):
    (tmp_path / "hero.jpg").write_bytes(b"x" * 128)
    html = tmp_path / "page.html"
    html.write_text(
        """
        <!doctype html>
        <html>
          <head>
            <link rel="stylesheet" href="/app.css">
            <link rel="preload" as="font" href="/font.woff2">
            <style>
              @font-face { font-family: Demo; src: url("font.woff2") format("woff2"); }
            </style>
            <script src="https://www.googletagmanager.com/gtm.js"></script>
          </head>
          <body>
            <img src="hero.jpg" width="1200" height="700" loading="lazy">
          </body>
        </html>
        """,
        encoding="utf-8",
    )
    return html


def test_static_performance_audits_work_on_local_html(tmp_path):
    html = write_fixture(tmp_path)
    third_party_script_audit = load_script("third_party_script_audit")
    font_audit = load_script("font_audit")
    image_weight_audit = load_script("image_weight_audit")
    critical_request_chain = load_script("critical_request_chain")
    lcp_subparts = load_script("lcp_subparts")

    scripts = third_party_script_audit.audit(str(html))
    assert scripts["third_party_count"] == 1
    assert scripts["blocking_third_party_count"] == 1

    fonts = font_audit.audit(str(html))
    assert fonts["font_file_count"] == 2
    assert any(issue["message"] == "@font-face missing font-display" for issue in fonts["issues"])

    images = image_weight_audit.audit(str(html))
    assert images["image_count"] == 1
    assert images["known_image_bytes"] == 128
    assert any(issue["message"] == "Likely LCP image is lazy-loaded" for issue in images["issues"])

    chains = critical_request_chain.audit(str(html))
    assert chains["critical_request_count"] == 2
    assert any(issue["message"] == "Render-blocking stylesheet" for issue in chains["issues"])

    lcp = lcp_subparts.analyze_source(str(html))
    assert lcp["mode"] == "static-html"
    assert lcp["lcp_element_url"].endswith("hero.jpg")


def test_optional_lighthouse_degrades_for_local_html():
    lighthouse_runner = load_script("lighthouse_runner")

    result = lighthouse_runner.run_lighthouse("page.html")

    assert result["error"]
    assert "requires an http(s) URL" in result["error"]


def test_cache_checker_reports_local_html_header_limitation(tmp_path):
    html = write_fixture(tmp_path)
    cache_compression_checker = load_script("cache_compression_checker")

    result = cache_compression_checker.audit(str(html))

    assert result["resources_checked"] == 0
    assert result["asset_count"] == 1
    assert "Header checks require HTTP(S)" in result["issues"][0]["message"]


def test_bare_local_html_filename_is_not_treated_as_url(tmp_path, monkeypatch):
    html = write_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    image_weight_audit = load_script("image_weight_audit")

    result = image_weight_audit.audit(html.name)

    assert result["image_count"] == 1
    assert result["fetch_error"] is None


def test_image_inventory_treats_next_fill_image_as_dimension_safe(tmp_path):
    html = tmp_path / "next-fill.html"
    html.write_text(
        """
        <!doctype html>
        <img alt="Hero" src="/_next/image?url=hero.jpg&w=1200&q=75" data-nimg="fill">
        <img alt="Inline" src="/inline.jpg">
        """,
        encoding="utf-8",
    )
    image_inventory = load_script("image_inventory")

    result = image_inventory.inventory(str(html))
    dimension_issues = [
        issue for issue in result["issues"]
        if issue["message"] == "Image missing explicit dimensions"
    ]

    assert result["images"][0]["is_responsive_fill"] is True
    assert len(dimension_issues) == 1
    assert dimension_issues[0]["url"] == "/inline.jpg"
