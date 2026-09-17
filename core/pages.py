"""Printable paper size names (no Qt)."""

from __future__ import annotations

PAGE_SIZE_NAMES: tuple[str, ...] = ("A4", "A5", "A3", "A6", "B5", "Letter")
PAGE_SIZE_NAME_SET = frozenset(PAGE_SIZE_NAMES)

# Portrait width × height in millimetres.
PAGE_SIZE_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
    "A3": (297.0, 420.0),
    "A6": (105.0, 148.0),
    "B5": (176.0, 250.0),
    "Letter": (215.9, 279.4),
}

# Uppercase lookup for desk-card spec aliases (A4 / a4 / …).
PAPER_SPEC_ALIASES: dict[str, tuple[str, int, int]] = {
    name.upper(): (name, int(round(w)), int(round(h)))
    for name, (w, h) in PAGE_SIZE_MM.items()
}

# UI label → config key for print sheet orientation.
PAGE_ORIENT_LABELS: tuple[tuple[str, str], ...] = (
    ("自动判断", "auto"),
    ("纵向", "portrait"),
    ("横向", "landscape"),
)
PAGE_ORIENT_KEYS: tuple[str, ...] = tuple(k for _, k in PAGE_ORIENT_LABELS)
PAGE_ORIENT_KEY_SET = frozenset(PAGE_ORIENT_KEYS)
