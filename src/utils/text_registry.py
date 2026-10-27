"""A markdown file of named texts, read by the code that writes them into a report.

The texts live in a markdown file so that whoever reads or edits them does not touch code: each text is a section
`## <kind>: <name>`, the key it is looked up by is `<kind>:<name>`. Anything before the first section (the title,
the notes on the format) is ignored. A section of a kind in `bullet_kinds` is a list (one `- ` line per item, a
continuation line indented), any other is a single paragraph with no blank line inside.

The file and the code that reads it must agree exactly: a missing, repeated or unknown key raises, so a text is
never silently absent from a report or left in the file with nothing using it.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from pathlib import Path

_HEADING = re.compile(r"^## (?P<kind>[a-z_]+): (?P<name>[a-z0-9_]+)$")


def _paragraph(path: Path, key: str, lines: list[str]) -> str:
    if any(not line.strip() for line in lines):
        raise ValueError(f"{path}: the text {key!r} has a blank line inside: a paragraph is a single block of lines")
    return " ".join(line.strip() for line in lines)


def _bullets(path: Path, key: str, lines: list[str]) -> tuple[str, ...]:
    items: list[str] = []
    for line in lines:
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith((" ", "\t")) and items and line.strip():
            items[-1] += " " + line.strip()
        else:
            raise ValueError(f"{path}: the list {key!r} has a line that is neither '- ' nor an indented continuation: {line!r}")
    return tuple(items)


def _sections(path: Path, text: str) -> dict[str, list[str]]:
    """The body lines (blank edges removed) of every `## kind: name` section, by `kind:name`."""
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            match = _HEADING.match(line)
            if match is None:
                raise ValueError(f"{path}:{number}: heading {line!r} is not '## <kind>: <name>' (lowercase letters, digits, underscores)")
            key = f"{match['kind']}:{match['name']}"
            if key in sections:
                raise ValueError(f"{path}:{number}: the text {key!r} is defined twice")
            current = sections[key] = []
        elif current is not None:
            current.append(line.rstrip())
    for body in sections.values():
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
    return sections


def load_text_registry(path: Path, expected: Collection[str], bullet_kinds: Collection[str]) -> dict[str, str | tuple[str, ...]]:
    """The texts of `path` by `kind:name`: a string, or a tuple of strings for a kind in `bullet_kinds`.

    `expected` is every key the caller uses. Raises FileNotFoundError if the file does not exist and ValueError for a
    malformed heading, a repeated key, an empty text, a key of `expected` that the file lacks or a key of the file
    that is not in `expected`."""
    if not path.is_file():
        raise FileNotFoundError(f"text registry not found: {path}")
    sections = _sections(path, path.read_text())
    missing, unknown = sorted(set(expected) - set(sections)), sorted(set(sections) - set(expected))
    if missing or unknown:
        raise ValueError(f"{path}: missing text(s) {missing}, unknown text(s) {unknown} - it must define exactly the texts the code uses")
    texts: dict[str, str | tuple[str, ...]] = {}
    for key, body in sections.items():
        if not body:
            raise ValueError(f"{path}: the text {key!r} is empty")
        texts[key] = _bullets(path, key, body) if key.split(":", 1)[0] in set(bullet_kinds) else _paragraph(path, key, body)
    return texts
