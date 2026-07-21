import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_noindex_thin_page_is_skipped():
    duplicate_content = load_script("duplicate_content")
    report = duplicate_content.detect_duplicates({
        "https://example.com/utility": {
            "text": "Short utility page",
            "word_count": 3,
            "html": '<html><head><meta name="robots" content="NOINDEX, follow"></head><body>Short utility page</body></html>',
        },
    })

    assert report["thin_content"] == []
    assert report["summary"]["thin_pages"] == 0


def test_noindex_near_duplicate_pair_is_downgraded():
    duplicate_content = load_script("duplicate_content")
    base = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
        "nu xi omicron pi rho sigma tau upsilon phi chi psi omega"
    )
    variant = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
        "nu xi omicron pi rho sigma tau upsilon phi chi changed omega"
    )

    report = duplicate_content.detect_duplicates(
        {
            "https://example.com/a": {
                "text": base,
                "word_count": len(base.split()),
                "html": f"<html><body>{base}</body></html>",
            },
            "https://example.com/b": {
                "text": variant,
                "word_count": len(variant.split()),
                "html": f'<html><head><meta name="robots" content="noindex"></head><body>{variant}</body></html>',
            },
        },
        similarity_threshold=0.5,
    )

    assert len(report["near_duplicates"]) == 1
    pair = report["near_duplicates"][0]
    assert pair["severity"] == "Info"
    assert pair["noindex_in_pair"] is True
    assert "No action required" in pair["fix"]


def test_noindex_exact_duplicate_pair_is_not_critical():
    duplicate_content = load_script("duplicate_content")
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa"

    report = duplicate_content.detect_duplicates({
        "https://example.com/indexable": {
            "text": text,
            "word_count": len(text.split()),
            "html": f"<html><body>{text}</body></html>",
        },
        "https://example.com/noindex": {
            "text": text,
            "word_count": len(text.split()),
            "html": f'<html><head><meta name="robots" content="noindex"></head><body>{text}</body></html>',
        },
    })

    assert report["exact_duplicates"]
    assert all(group["severity"] != "Critical" for group in report["exact_duplicates"])
    assert all("No action required" in group["fix"] for group in report["exact_duplicates"])
