"""Printable paper size names (no Qt)."""

from __future__ import annotations

PAGE_SIZE_NAMES: tuple[str, ...] = ("A4", "A5", "A3", "Letter")
PAGE_SIZE_NAME_SET = frozenset(PAGE_SIZE_NAMES)

# Portrait width × height in millimetres.
PAGE_SIZE_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
    "A3": (297.0, 420.0),
    "Letter": (215.9, 279.4),
}
