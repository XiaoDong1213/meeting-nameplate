"""Multipage nameplate document and printer paint loop."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QImage, QPageLayout, QPageSize, QPainter
from PyQt6.QtPrintSupport import QPrinter

from core.config import PrintConfig
from core.layout import Edge, Rect, get_edges
from core.pages import PAGE_SIZE_MM
from core.specs import Setup, mm_to_pixels
from render.fonts import MAX_FONT, fit_font_for_lines
from render.pages import PAGE_SIZES
from render.paint import draw_borders, draw_content, font_from_style

PREVIEW_DPI = 96.0


def resolve_landscape(config: PrintConfig, setup: Setup) -> bool:
    orient = config.page_orientation
    if orient == "landscape":
        return True
    if orient == "portrait":
        return False
    pw, ph = PAGE_SIZE_MM.get(config.page_size, (210.0, 297.0))
    return setup.prefers_landscape(pw, ph)


def sheet_pixel_size(config: PrintConfig, landscape: bool, dpi: float) -> tuple[int, int]:
    pw, ph = PAGE_SIZE_MM.get(config.page_size, (210.0, 297.0))
    if landscape:
        pw, ph = ph, pw
    return max(1, mm_to_pixels(pw, dpi)), max(1, mm_to_pixels(ph, dpi))


class NameplateDocument:
    """Paints packed nameplate layouts onto a QPrinter or QImage."""

    def __init__(self, config: PrintConfig):
        self.config = config
        self.setup = config.current_setup
        if self.setup is None:
            raise ValueError("规格尺寸不合要求")
        self.contents = list(config.content_list)
        self._index = 0
        self._rects: list[Rect] = []
        self._dpi = 600.0
        self._page_w = 1
        self._page_h = 1
        self._origin = (0.0, 0.0)
        self._bg: QImage | None = None
        if config.image_file and Path(config.image_file).exists():
            self._bg = QImage(config.image_file)

    def configure_printer(self, printer: QPrinter) -> None:
        size_id = PAGE_SIZES.get(self.config.page_size, QPageSize.PageSizeId.A4)
        printer.setPageSize(QPageSize(size_id))
        printer.setFullPage(True)
        if self.config.printer_name:
            printer.setPrinterName(self.config.printer_name)

    def _place_cards(self, page_w: int, page_h: int) -> None:
        self._page_w = max(1, page_w)
        self._page_h = max(1, page_h)
        self._rects, _ = self.setup.get_rectangles(
            self._page_w, self._page_h, dpi=self._dpi, lock_page=True
        )
        self._index = 0

    def begin(self, printer: QPrinter) -> None:
        self._dpi = float(printer.resolution()) or 96.0
        landscape = resolve_landscape(self.config, self.setup)
        printer.setPageOrientation(
            QPageLayout.Orientation.Landscape if landscape else QPageLayout.Orientation.Portrait
        )
        printer.setFullPage(True)
        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        self._origin = (float(page_rect.x()), float(page_rect.y()))
        self._place_cards(max(1, int(page_rect.width())), max(1, int(page_rect.height())))

    def begin_sheet(self, page_w: int, page_h: int, dpi: float) -> None:
        self._dpi = dpi
        self._origin = (0.0, 0.0)
        self._place_cards(page_w, page_h)

    def paint_page(self, painter: QPainter) -> bool:
        """Paint one page. Returns True if more pages remain."""
        cfg = self.config
        painter.save()
        painter.translate(*self._origin)
        painter.setClipRect(QRectF(0, 0, self._page_w, self._page_h))
        edges = get_edges(
            self._rects,
            top=cfg.border_top,
            right=cfg.border_right,
            bottom=cfg.border_bottom,
            left=cfg.border_left,
        )
        for rect in self._rects:
            text = self.contents[self._index] if self._index < len(self.contents) else ""
            if self.setup.mirror:
                painter.save()
                painter.translate(rect.x, rect.y)
                half = Rect(0, rect.height // 2, rect.width, rect.height // 2)
                draw_content(painter, half, text, self.config, self.setup, self._bg, self._dpi)
                mid_y = rect.height // 2
                if cfg.border_fold:
                    edges.append(
                        Edge.normalize(
                            (rect.x, rect.y + mid_y),
                            (rect.x + rect.width, rect.y + mid_y),
                        )
                    )
                painter.translate(rect.width, rect.height)
                painter.rotate(180)
                draw_content(painter, half, text, self.config, self.setup, self._bg, self._dpi)
                painter.restore()
            else:
                draw_content(painter, rect, text, self.config, self.setup, self._bg, self._dpi)
            self._index += 1

        draw_borders(painter, edges, self.config.line_style, self.config.border_alpha)
        painter.restore()
        return self._index < len(self.contents)


def resolve_font_size(config: PrintConfig, setup: Setup, lines: list[str], dpi: float = 96.0) -> float:
    """Resolve configured font size mode to point size."""
    size_text = config.font_size_text
    base = font_from_style(config.font_name, 12, config.font_style)
    card_w = mm_to_pixels(setup.width_mm, dpi)
    card_h = mm_to_pixels(setup.height_mm, dpi)
    if size_text in {"最大化", "每牌尽量大", str(MAX_FONT)}:
        return float(MAX_FONT)
    try:
        value = float(size_text.strip())
        if 0 < value < MAX_FONT:
            return float(value)
    except ValueError:
        pass
    fitted = fit_font_for_lines(lines, base, card_w, card_h, setup.margin_ratio, dpi=dpi)
    return float(fitted.pointSizeF())


def render_sheets(config: PrintConfig, dpi: float = PREVIEW_DPI) -> list[QImage]:
    """Rasterize one image per packed paper sheet for on-screen preview."""
    local = NameplateDocument(config)
    landscape = resolve_landscape(config, local.setup)
    page_w, page_h = sheet_pixel_size(config, landscape, dpi)
    local.begin_sheet(page_w, page_h, dpi)
    images: list[QImage] = []
    if not local.contents:
        return images
    more = True
    while more:
        image = QImage(page_w, page_h, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor("#FFFFFF"))
        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            more = local.paint_page(painter)
        finally:
            if painter.isActive():
                painter.end()
        images.append(image)
    return images


def paint_to_printer(printer: QPrinter, config: PrintConfig) -> None:
    """Render all pages onto ``printer``."""
    local = NameplateDocument(config)
    local.configure_printer(printer)
    local.begin(printer)
    qp = QPainter(printer)
    if not qp.isActive():
        return
    try:
        more = True
        first = True
        while more:
            if not first:
                printer.newPage()
            first = False
            more = local.paint_page(qp)
    finally:
        qp.end()
