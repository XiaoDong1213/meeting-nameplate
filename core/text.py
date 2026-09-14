"""Text helpers: tab columns, newlines, name spacing."""

from __future__ import annotations

IDEOGRAPHIC_SPACE = "\u3000"


def split_tab(text: str) -> list[str]:
    return [part.strip() for part in text.split("\t")]


def new_line(text: str) -> str:
    return "\n".join(split_tab(text))


def build_content_list(lines: list[str]) -> list[str]:
    """Non-empty roster lines → printable desk-card texts."""
    return [line for line in lines if line and not line.isspace()]


def insert_ideographic_spaces(text: str) -> tuple[str, int]:
    """Insert full-width space into every exact two-character name.

    Returns (new_text, changed_count). Tab-separated lines only transform the first column.
    Lines that already contain a full-width space are left unchanged.
    """

    def transform_name(s: str) -> tuple[str, bool]:
        core = s.strip()
        if not core or IDEOGRAPHIC_SPACE in core:
            return s, False
        if len(core) != 2:
            return s, False
        left = s[: len(s) - len(s.lstrip())]
        right = s[len(s.rstrip()) :]
        return f"{left}{core[0]}{IDEOGRAPHIC_SPACE}{core[1]}{right}", True

    lines = text.splitlines()
    changed = 0
    out: list[str] = []
    for line in lines:
        if "\t" in line:
            first, *rest = line.split("\t")
            new_first, ok = transform_name(first)
            if ok:
                changed += 1
            out.append("\t".join([new_first, *rest]))
        else:
            new_line, ok = transform_name(line)
            if ok:
                changed += 1
            out.append(new_line)

    new_text = "\n".join(out)
    if text.endswith("\n"):
        new_text += "\n"
    return new_text, changed
