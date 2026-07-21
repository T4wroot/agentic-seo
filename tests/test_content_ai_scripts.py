import importlib.util
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


HTML = """<!doctype html>
<html lang="en">
<head>
  <title>Technical SEO audit guide</title>
  <meta name="description" content="Technical SEO audit guide with checklist and examples.">
  <meta property="article:published_time" content="2024-01-10">
  <meta property="article:modified_time" content="2026-05-01">
  <link rel="canonical" href="https://example.com/technical-seo-audit">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Article","author":{"@type":"Person","name":"Ada Analyst","sameAs":["https://www.wikidata.org/wiki/Q42"]},"datePublished":"2024-01-10","dateModified":"2026-05-01"}
  </script>
</head>
<body>
  <main>
    <p class="byline">By Ada Analyst, certified technical SEO specialist with 10 years of experience.</p>
    <a href="/about">About</a>
    <a href="/contact">Contact</a>
    <a href="/editorial-policy">Editorial policy</a>
    <h1>Technical SEO audit guide</h1>
    <h2>What is a technical SEO audit?</h2>
    <p>A technical SEO audit is a structured review of crawlability, indexability, metadata, internal links, and performance issues that can stop search engines from understanding a website.</p>
    <h2>Technical SEO audit checklist</h2>
    <ol><li>Crawl the site</li><li>Check canonicals</li><li>Review sitemaps</li></ol>
    <table><tr><th>Signal</th><th>Fix</th></tr><tr><td>Noindex</td><td>Remove when needed</td></tr></table>
    <p>According to research in 2024, 64% of large sites had indexability issues.</p>
    <p>We tested the checklist on 25 customer sites in 2026.</p>
    <a href="https://www.gov.uk/service-manual">Government service manual</a>
  </main>
</body>
</html>"""


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_html(tmp_path):
    path = tmp_path / "page.html"
    path.write_text(HTML, encoding="utf-8")
    return str(path)


def test_content_eeat_freshness_answer_and_citation_scripts(tmp_path):
    page = write_html(tmp_path)

    intent = load_script("content_intent_matcher").match_intent(page, "technical seo audit", "informational")
    assert intent["score"] >= 70
    assert intent["exact_matches"]["title"] is True

    eeat = load_script("eeat_signal_checker").check_eeat(page)
    assert eeat["score"] >= 70
    assert eeat["signals"]["authors"]

    freshness = load_script("freshness_checker").check_freshness(page, today=load_script("freshness_checker")._parse_date("2026-05-15"))
    assert freshness["latest_date"] == "2026-05-01"
    assert not freshness["schema_date_mismatch"]

    answers = load_script("answer_block_scanner").scan_answer_blocks(page)
    assert answers["direct_answers"]
    assert answers["lists"]
    assert answers["tables"]

    citations = load_script("citation_readiness").check_citation_readiness(page)
    assert citations["factual_claims"] >= 1
    assert citations["citation_signals"]["trusted_external_links"] == 1


def test_topical_cluster_mapper_and_decay_detector(tmp_path):
    cluster_csv = tmp_path / "clusters.csv"
    cluster_csv.write_text(
        "url,title,cluster,links\n"
        "https://example.com/seo,Technical SEO Hub,technical seo,https://example.com/seo/crawl\n"
        "https://example.com/seo/crawl,Crawl Audit,technical seo,https://example.com/seo\n",
        encoding="utf-8",
    )
    mapper = load_script("topical_cluster_mapper")
    clusters = mapper.map_clusters(mapper._rows_from_csv(str(cluster_csv)))
    assert clusters["cluster_count"] == 1
    assert clusters["clusters"]["technical seo"]["internal_edges"]

    decay_csv = tmp_path / "gsc.csv"
    decay_csv.write_text(
        "date,url,query,clicks,impressions,position\n"
        "2026-04-01,https://example.com/seo,technical seo audit,100,1000,3\n"
        "2026-04-02,https://example.com/seo,technical seo checklist,10,500,9\n"
        "2026-05-01,https://example.com/seo,technical seo audit,40,950,5\n"
        "2026-05-02,https://example.com/seo,technical seo checklist,15,600,8\n",
        encoding="utf-8",
    )
    decay = load_script("content_decay_detector").detect_decay(
        str(decay_csv),
        type(
            "Args",
            (),
            {
                "url_column": "url",
                "query_column": "query",
                "date_column": "date",
                "clicks_column": "clicks",
                "impressions_column": "impressions",
                "position_column": "position",
            },
        )(),
        split_date=load_script("content_decay_detector")._parse_date("2026-05-01"),
        decline_threshold=0.2,
        min_impressions=100,
    )
    assert decay["declining_pages"]
    assert decay["striking_distance_keywords"]
