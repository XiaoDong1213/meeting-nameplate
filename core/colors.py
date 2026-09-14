"""ARGB integer ↔ QColor."""

from __future__ import annotations

from PyQt6.QtGui import QColor

WHITE_ARGB = 0xFFFFFFFF


def argb_to_qcolor(argb: int) -> QColor:
    a = (argb >> 24) & 0xFF
    r = (argb >> 16) & 0xFF
    g = (argb >> 8) & 0xFF
    b = argb & 0xFF
    return QColor(r, g, b, a)


def qcolor_to_argb(color: QColor) -> int:
    return (color.alpha() << 24) | (color.red() << 16) | (color.green() << 8) | color.blue()
