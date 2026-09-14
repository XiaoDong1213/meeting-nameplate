"""Setup / Title models and size-spec parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from core.enums import FontStyle
from core.layout import Rect, calculate_layout, prefer_landscape

DEFAULT_SIZE_LIST = [
    "90*55mm",
    "100*70mm",
    "120*80mm",
    "140*90mm",
    "150*100mm",
    "220*110mm",
    "210*70mm",
    "240*100mm",
    "297*100mm",
    "100*80mm",
    "120*90mm",
    "105*148mm",
    "148*210mm",
    "210*297mm",
]

# mm -> 1/100 inch (same formula as original Millimeter2Inch)
MM_TO_HUNDREDTH_INCH = 10.0 / 2.54

_SPEC_RE = re.compile(r"^(\d+)[*|x](\d+)mm(-[PL])?$", re.IGNORECASE)


def mm_to_hundredth_inch(value: float) -> int:
    return int(value * MM_TO_HUNDREDTH_INCH)


def mm_to_pixels(value: float, dpi: float) -> int:
    return int(value / 25.4 * dpi)


def default_title_xy(width_mm: int, height_mm: int, is_header: bool) -> tuple[int, int]:
    """左上抬头 / 右下落款，边距随牌面缩放并夹在 6–10mm / 5–8mm。"""
    inset_x = max(6, min(10, max(width_mm, 1) // 20))
    inset_y = max(5, min(8, max(height_mm, 1) // 16))
    if is_header:
        return inset_x, inset_y
    text_w = max(36, width_mm * 2 // 5)
    x = max(inset_x, width_mm - inset_x - text_w)
    y = max(inset_y, height_mm - inset_y - 6)
    return x, y


def mm_size_to_hundredth(width_mm: int, height_mm: int) -> tuple[int, int]:
    return mm_to_hundredth_inch(width_mm), mm_to_hundredth_inch(height_mm)


@dataclass
class Title:
    enabled: bool = False
    content: str = ""
    font_name: str = "黑体"
    font_size: float = 20.0
    font_style: FontStyle = FontStyle.REGULAR
    argb: int = 0xFF000000  # opaque black
    x_mm: int = 0
    y_mm: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "content": self.content,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "font_style": self.font_style.value,
            "argb": self.argb,
            "x_mm": self.x_mm,
            "y_mm": self.y_mm,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> Title:
        if not data:
            return cls()
        style = data.get("font_style", FontStyle.REGULAR.value)
        try:
            font_style = FontStyle(style)
        except ValueError:
            font_style = FontStyle.REGULAR
        return cls(
            enabled=bool(data.get("enabled", False)),
            content=str(data.get("content", "")),
            font_name=str(data.get("font_name", "黑体")),
            font_size=float(data.get("font_size", 20)),
            font_style=font_style,
            argb=int(data.get("argb", 0xFF000000)),
            x_mm=int(data.get("x_mm", 0)),
            y_mm=int(data.get("y_mm", 0)),
        )


@dataclass
class Setup:
    text: str = "200*100mm"
    width_mm: int = 200
    height_mm: int = 100
    margin_ratio: float = 0.15
    offset_x_mm: int = 0
    offset_y_mm: int = 0
    title1: Title = field(default_factory=Title)
    title2: Title = field(default_factory=Title)
    landscape: Optional[bool] = None

    @property
    def mirror(self) -> bool:
        """Always fold-mirror desk cards (two halves on one card height)."""
        return True

    @classmethod
    def parse(cls, text: str) -> Optional[Setup]:
        match = _SPEC_RE.match(text.strip())
        if not match:
            return None
        width = int(match.group(1))
        height = int(match.group(2))
        if not (20 <= width <= 300 and 20 <= height <= 300):
            return None
        # Accept legacy -L/-P in the string for parse, but ignore: page orient is always auto.
        return cls(text=text.strip(), width_mm=width, height_mm=height, landscape=None)

    def card_height_mm(self) -> int:
        return self.height_mm * (2 if self.mirror else 1)

    def prefers_landscape(self, page_w_mm: float, page_h_mm: float) -> bool:
        _, landscape = calculate_layout(
            max(1, int(page_w_mm * 10)),
            max(1, int(page_h_mm * 10)),
            max(1, int(self.width_mm * 10)),
            max(1, int(self.card_height_mm() * 10)),
            None,
        )
        if landscape:
            return True
        return prefer_landscape(page_w_mm, page_h_mm, self.width_mm, self.card_height_mm())

    def get_rectangles(
        self,
        page_width: int,
        page_height: int,
        *,
        dpi: float | None = None,
        lock_page: bool = False,
    ) -> tuple[list[Rect], bool]:
        """Pack as many cards as fit. lock_page keeps the given sheet orientation."""
        card_h = self.card_height_mm()
        if dpi is not None:
            small_w = mm_to_pixels(self.width_mm, dpi)
            small_h = mm_to_pixels(card_h, dpi)
        else:
            small_w, small_h = mm_size_to_hundredth(self.width_mm, card_h)
        landscape = False if lock_page else self.landscape
        return calculate_layout(
            page_width, page_height, max(1, small_w), max(1, small_h), landscape
        )

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "margin_ratio": self.margin_ratio,
            "offset_x_mm": self.offset_x_mm,
            "offset_y_mm": self.offset_y_mm,
            "title1": self.title1.to_dict(),
            "title2": self.title2.to_dict(),
            "landscape": self.landscape,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Setup:
        parsed = cls.parse(str(data.get("text", "200*100mm")))
        base = parsed or cls()
        base.margin_ratio = float(data.get("margin_ratio", 0.15))
        base.offset_x_mm = int(data.get("offset_x_mm", 0))
        base.offset_y_mm = int(data.get("offset_y_mm", 0))
        base.title1 = Title.from_dict(data.get("title1"))
        base.title2 = Title.from_dict(data.get("title2"))
        if "landscape" in data and data["landscape"] is not None:
            # Legacy field ignored — orientation is chosen in print preview / auto pack.
            pass
        base.landscape = None
        return base
