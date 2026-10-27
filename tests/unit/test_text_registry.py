"""Unit tests for src/utils/text_registry.py."""

from pathlib import Path

import pytest

from src.utils.text_registry import load_text_registry

BULLETS = ("hint",)


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "texts.md"
    path.write_text(text)
    return path


GOOD = """# Title

Notes on the format, before the first section: ignored.

## term: silhouette

first line
second line

## hint: curves

- first bullet
  continued here
- second bullet
"""


def test_a_paragraph_joins_its_lines_and_a_hint_is_a_tuple_of_bullets_with_continuations_joined(tmp_path):
    texts = load_text_registry(_write(tmp_path, GOOD), ["term:silhouette", "hint:curves"], BULLETS)

    assert texts == {"term:silhouette": "first line second line", "hint:curves": ("first bullet continued here", "second bullet")}


@pytest.mark.parametrize(
    "text, message",
    [
        (GOOD.replace("- first bullet\n  continued here", "- first bullet\n\n  continued here"), "neither"),
        (GOOD + "\n## term: silhouette\n\nagain\n", "defined twice"),
        (GOOD.replace("## term: silhouette", "## Term Silhouette"), "is not '## <kind>: <name>'"),
        (GOOD.replace("first line\nsecond line", "first\n\nsecond"), "blank line inside"),
        (GOOD.replace("first line\nsecond line\n", ""), "is empty"),
        (GOOD.replace("- first bullet", "first bullet"), "neither"),
    ],
)
def test_a_malformed_file_raises(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        load_text_registry(_write(tmp_path, text), ["term:silhouette", "hint:curves"], BULLETS)


def test_a_text_the_code_uses_but_the_file_lacks_and_a_text_the_file_has_but_the_code_does_not_use_both_raise(tmp_path):
    path = _write(tmp_path, GOOD)

    with pytest.raises(ValueError, match=r"missing text\(s\) \['term:dunn'\]"):
        load_text_registry(path, ["term:silhouette", "hint:curves", "term:dunn"], BULLETS)
    with pytest.raises(ValueError, match=r"unknown text\(s\) \['hint:curves'\]"):
        load_text_registry(path, ["term:silhouette"], BULLETS)


def test_a_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="text registry not found"):
        load_text_registry(tmp_path / "absent.md", [], BULLETS)
