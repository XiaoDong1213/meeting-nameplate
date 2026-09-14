"""Cached Chinese font family list for combo boxes."""

from __future__ import annotations

from PyQt6.QtGui import QFontDatabase

_cached: list[str] | None = None


def chinese_fonts(*, refresh: bool = False) -> list[str]:
    """Return non-ASCII font families (cached after first call)."""
    global _cached
    if _cached is not None and not refresh:
        return list(_cached)
    families = QFontDatabase.families()
    _cached = [f for f in families if f and not f[0].isascii()]
    return list(_cached)


def clear_font_cache() -> None:
    global _cached
    _cached = None
