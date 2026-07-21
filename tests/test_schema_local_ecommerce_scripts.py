import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_schema_required_props_walks_graph_nodes():
    schema_required_props = load_script("schema_required_props")
    doc = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "name": "Example Co", "url": "https://example.com"},
            {"@type": "Product", "name": "Widget"},
        ],
    }

    result = schema_required_props.validate_schema_required_props([doc])

    assert result["schema_nodes"] == 2
    assert any("offers" in item["message"] for item in result["issues"])


def test_product_schema_checker_flags_missing_offer_price_currency():
    product_schema_checker = load_script("product_schema_checker")
    doc = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Widget",
        "offers": {"@type": "Offer", "price": "19.99"},
    }

    result = product_schema_checker.check_product_schema([doc])

    assert result["products"] == 1
    assert any("priceCurrency" in item["message"] for item in result["issues"])


def test_template_generator_returns_bundled_localbusiness_template():
    schema_template_generator = load_script("schema_template_generator")

    result = schema_template_generator.get_template("LocalBusiness")

    assert result["json_ld"]["@type"] == "LocalBusiness"
    assert "description" in result


def test_hreflang_sitemap_parser_extracts_xhtml_links():
    hreflang_sitemap_validator = load_script("hreflang_sitemap_validator")
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
      xmlns:xhtml="http://www.w3.org/1999/xhtml">
      <url>
        <loc>https://example.com/en/</loc>
        <xhtml:link rel="alternate" hreflang="en" href="https://example.com/en/"/>
        <xhtml:link rel="alternate" hreflang="fr" href="https://example.com/fr/"/>
      </url>
    </urlset>
    """

    result = hreflang_sitemap_validator.parse_hreflang_sitemap(xml, "https://example.com/sitemap.xml")

    assert result["type"] == "urlset"
    assert result["urls"][0]["alternates"][1]["lang"] == "fr"
