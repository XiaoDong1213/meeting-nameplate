"""Rectangle packing and edge extraction for A4 pages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


@dataclass(frozen=True)
class _Arrange:
    rows: int
    cols: int


def centered_rect(page_w: int, page_h: int, card_w: int, card_h: int) -> Rect:
    """Place one card at full size, centered. Origin may be negative (clipped later)."""
    cw = max(1, card_w)
    ch = max(1, card_h)
    return Rect((page_w - cw) // 2, (page_h - ch) // 2, cw, ch)


def overflow_extent(page_w: float, page_h: float, card_w: float, card_h: float) -> float:
    return max(0.0, card_w - page_w) + max(0.0, card_h - page_h)


def prefer_landscape(page_w: float, page_h: float, card_w: float, card_h: float) -> bool:
    """True when rotating the page strictly reduces how far the card sticks out."""
    return overflow_extent(page_h, page_w, card_w, card_h) < overflow_extent(
        page_w, page_h, card_w, card_h
    )


def _arrangement(large_w: int, large_h: int, small_w: int, small_h: int) -> _Arrange:
    return _Arrange(rows=int(large_h / small_h), cols=int(large_w / small_w))


def _generate_positions(
    large_w: int, large_h: int, small_w: int, small_h: int, cols: int, rows: int
) -> list[Rect]:
    total_w = cols * small_w
    total_h = rows * small_h
    offset_x = (large_w - total_w) // 2
    offset_y = (large_h - total_h) // 2
    rects: list[Rect] = []
    for row in range(rows):
        for col in range(cols):
            rects.append(
                Rect(
                    x=offset_x + col * small_w,
                    y=offset_y + row * small_h,
                    width=small_w,
                    height=small_h,
                )
            )
    return rects


def calculate_layout(
    large_w: int,
    large_h: int,
    small_w: int,
    small_h: int,
    landscape: Optional[bool] = None,
) -> tuple[list[Rect], bool]:
    """Pack small rectangles into large page; choose orientation if needed.

    Returns (rectangles, landscape_flag).
    """
    if small_w <= 0 or small_h <= 0:
        raise ValueError("矩形尺寸必须大于0")

    horizontal = _arrangement(large_w, large_h, small_w, small_h)
    vertical = _arrangement(large_h, large_w, small_w, small_h)

    if landscape is None:
        landscape = (horizontal.cols * horizontal.rows) < (vertical.cols * vertical.rows)

    h_cols = max(1, horizontal.cols)
    h_rows = max(1, horizontal.rows)
    v_cols = max(1, vertical.cols)
    v_rows = max(1, vertical.rows)

    if landscape:
        return _generate_positions(large_h, large_w, small_w, small_h, v_cols, v_rows), True
    return _generate_positions(large_w, large_h, small_w, small_h, h_cols, h_rows), False


@dataclass(frozen=True)
class Edge:
    start: tuple[int, int]
    end: tuple[int, int]

    @staticmethod
    def normalize(start: tuple[int, int], end: tuple[int, int]) -> Edge:
        sx, sy = start
        ex, ey = end
        if sx == ex:  # vertical: top -> bottom
            if sy <= ey:
                return Edge(start, end)
            return Edge(end, start)
        # horizontal: left -> right
        if sx <= ex:
            return Edge(start, end)
        return Edge(end, start)


def edges_of_rect(
    rect: Rect,
    *,
    top: bool = True,
    right: bool = True,
    bottom: bool = True,
    left: bool = True,
) -> list[Edge]:
    top_left = (rect.left, rect.top)
    top_right = (rect.right, rect.top)
    bottom_right = (rect.right, rect.bottom)
    bottom_left = (rect.left, rect.bottom)
    edges: list[Edge] = []
    if top:
        edges.append(Edge.normalize(top_left, top_right))
    if right:
        edges.append(Edge.normalize(top_right, bottom_right))
    if bottom:
        edges.append(Edge.normalize(bottom_right, bottom_left))
    if left:
        edges.append(Edge.normalize(bottom_left, top_left))
    return edges


def inset_rect(
    rect: Rect,
    *,
    top: int = 0,
    right: int = 0,
    bottom: int = 0,
    left: int = 0,
) -> Rect:
    """Shrink (positive) or expand (negative) a rect on each side, in pixels."""
    return Rect(
        rect.x + left,
        rect.y + top,
        max(1, rect.width - left - right),
        max(1, rect.height - top - bottom),
    )


def get_edges(
    rects: Iterable[Rect],
    *,
    top: bool = True,
    right: bool = True,
    bottom: bool = True,
    left: bool = True,
) -> list[Edge]:
    seen: set[Edge] = set()
    result: list[Edge] = []
    for rect in rects:
        for edge in edges_of_rect(rect, top=top, right=right, bottom=bottom, left=left):
            if edge not in seen:
                seen.add(edge)
                result.append(edge)
    return result
