import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_anchor_text_extraction_flags_internal_links():
    anchor_text_audit = load_script("anchor_text_audit")
    html = """
    <html><body>
      <a href="/features">Learn more</a>
      <a href="https://example.com/pricing" rel="nofollow"></a>
      <a href="https://external.test/">External</a>
    </body></html>
    """

    links = anchor_text_audit.extract_internal_anchors(html, "https://example.com/", "https://example.com/")

    assert len(links) == 2
    assert links[0]["anchor"] == "Learn more"
    assert links[1]["nofollow"] is True


def test_log_file_parser_classifies_googlebot():
    log_file_analyzer = load_script("log_file_analyzer")
    row = log_file_analyzer.parse_log_line(
        '127.0.0.1 - - [15/May/2026:10:20:30 +0000] "GET /missing HTTP/1.1" '
        '404 123 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"'
    )

    assert row["status"] == 404
    assert row["bot"] == "Googlebot"
    assert row["date"] == "2026-05-15"


def test_repo_file_inventory_scores_present_files(tmp_path):
    repo_file_inventory = load_script("repo_file_inventory")
    (tmp_path / "README.md").write_text("# Demo\n\nInstall with pip.\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("# Security\n", encoding="utf-8")

    result = repo_file_inventory.inventory_repository(str(tmp_path))

    assert result["summary"]["present"] >= 3
    assert result["readme"]["install_mentions"] == 1
    assert all(issue["type"] != "readme_install_cta" for issue in result["issues"])


def test_topic_suggester_uses_local_intent_without_github(tmp_path):
    repo_topic_suggester = load_script("repo_topic_suggester")
    (tmp_path / "README.md").write_text(
        "# Technical SEO CLI\n\nSchema JSON-LD audit automation for AI search.",
        encoding="utf-8",
    )

    result = repo_topic_suggester.suggest_topics(
        repo="invalid",
        path=str(tmp_path),
        token="",
        provider="api",
        intent_terms=["github seo"],
        limit=5,
    )

    topics = {row["topic"] for row in result["suggested_topics"]}
    assert "technical-seo" in topics
    assert result["limitations"]
