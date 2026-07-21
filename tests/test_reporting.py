import json
from pathlib import Path

import generate_report


FIXTURES = Path(__file__).parent / "fixtures"


def load_report_data():
    return json.loads((FIXTURES / "report_data.json").read_text(encoding="utf-8"))


def test_scoring_config_loads_weights_from_resource_file():
    config = generate_report.load_scoring_config()
    weights = generate_report.get_scoring_weights(config)

    assert weights["pagespeed"] == 13
    assert sum(weights.values()) == 100


def test_calculate_overall_score_uses_config_weights():
    data = load_report_data()
    scores = generate_report.calculate_overall_score(data)

    assert scores["weights"]["broken_links"] == 10
    assert scores["categories"]["security"] == 75
    assert scores["categories"]["pagespeed"] == 57
    assert 0 <= scores["overall"] <= 100


def test_markdown_report_contains_score_card_and_findings():
    data = load_report_data()
    scores = generate_report.calculate_overall_score(data)

    markdown = generate_report.render_markdown_report(data, scores)

    assert "# Full Audit Report" in markdown
    assert "| Performance and Core Web Vitals | 13 | 57 |" in markdown
    assert "Content-Security-Policy is missing" in markdown
    assert "Score confidence: `High`" in markdown


def test_action_plan_prioritizes_findings_and_pagespeed_opportunities():
    data = load_report_data()
    scores = generate_report.calculate_overall_score(data)

    action_plan = generate_report.render_action_plan(data, scores)

    assert "# Action Plan" in action_plan
    assert "Content-Security-Policy is missing" in action_plan
    assert "Eliminate render-blocking resources" in action_plan


def test_write_text_output_creates_parent_directories(tmp_path):
    output = tmp_path / "nested" / "FULL-AUDIT-REPORT.md"

    written = generate_report.write_text_output(str(output), "# Report\n")

    assert Path(written).is_file()
    assert output.read_text(encoding="utf-8") == "# Report\n"
