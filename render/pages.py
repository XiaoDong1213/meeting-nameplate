"""Qt page-size map for printers and preview."""

from __future__ import annotations

from PyQt6.QtGui import QPageSize

from core.pages import PAGE_SIZE_NAMES

PAGE_SIZES: dict[str, QPageSize.PageSizeId] = {
    "A4": QPageSize.PageSizeId.A4,
    "A5": QPageSize.PageSizeId.A5,
    "A3": QPageSize.PageSizeId.A3,
    "Letter": QPageSize.PageSizeId.Letter,
}

assert tuple(PAGE_SIZES) == PAGE_SIZE_NAMES
