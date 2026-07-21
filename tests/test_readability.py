import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_readability():
    spec = importlib.util.spec_from_file_location("readability", ROOT / "scripts" / "readability.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_html_paragraph_tags_count_as_separate_paragraphs():
    readability = load_readability()
    html = """
    <html>
      <body>
        <main>
          <h1>Readable guide</h1>
          <p>This first paragraph explains the topic clearly.</p>
          <p>This second paragraph adds another practical detail.</p>
          <p>This third paragraph gives readers a concise next step.</p>
        </main>
      </body>
    </html>
    """

    text = readability.extract_text(html)
    result = readability.analyze_readability(text)

    assert result["paragraph_count"] == 3
    assert result["sentence_count"] == 3
    assert result["avg_paragraph_length"] == 1.0


def test_plain_text_paragraph_count_still_uses_blank_lines():
    readability = load_readability()
    text = (
        "This first paragraph explains the topic clearly.\n\n"
        "This second paragraph adds another practical detail."
    )

    result = readability.analyze_readability(text)

    assert result["paragraph_count"] == 2
    assert result["avg_paragraph_length"] == 1.0
