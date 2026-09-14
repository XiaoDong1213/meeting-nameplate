"""QPainter drawing for a single nameplate face."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen

from core.colors import WHITE_ARGB, argb_to_qcolor
from core.config import PrintConfig
from core.enums import DashStyle, FontStyle
from core.layout import Edge, Rect
from core.specs import Setup, Title, mm_to_pixels
from core.text import new_line
from render.fonts import MAX_FONT, fit_font_in_rect


def font_from_style(name: str, size: float, style: FontStyle) -> QFont:
    font = QFont(name)
    font.setPointSizeF(max(size, 1.0))
    if style == FontStyle.BOLD:
        font.setBold(True)
    elif style == FontStyle.ITALIC:
        font.setItalic(True)
    elif style == FontStyle.UNDERLINE:
        font.setUnderline(True)
    return font


def _draw_cross(painter: QPainter, pen: QPen, point: tuple[int, int], radius: float = 5.0) -> None:
    painter.setPen(pen)
    x, y = point
    painter.drawLine(QPointF(x - radius, y), QPointF(x + radius, y))
    painter.drawLine(QPointF(x, y - radius), QPointF(x, y + radius))


def _draw_distributed(
    painter: QPainter,
    text: str,
    font: QFont,
    color: QColor,
    rect: QRectF,
    margin_ratio: float,
) -> None:
    margin_ratio = max(0.0, min(margin_ratio, 0.5))
    margin = rect.width() * margin_ratio
    content_width = rect.width() - margin
    painter.setFont(font)
    metrics = painter.fontMetrics()
    char_widths = [metrics.horizontalAdvance(ch) for ch in text]
    total = sum(char_widths)
    extra = content_width - total
    if extra <= 0 or len(text) <= 1 or "\n" in text:
        painter.setPen(color)
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), text)
        return
    spacing = extra / (len(text) - 1)
    start_x = rect.left() + (margin / 2)
    y = rect.top() + (rect.height() - metrics.ascent() - metrics.descent()) / 2 + metrics.ascent()
    x = start_x
    painter.setPen(color)
    for i, ch in enumerate(text):
        painter.drawText(QPointF(x, y), ch)
        x += char_widths[i] + spacing


def _apply_title(painter: QPainter, rect: QRectF, text: str, title: Title, dpi: float) -> str:
    content = title.content
    if not (title.enabled and content and content.strip()):
        return text
    lines = text.split("\n")
    if content == "第一列" and lines:
        content = lines[0]
        text = "\n".join(lines[1:])
    elif content == "最后一列" and lines:
        content = lines[-1]
        text = "\n".join(lines[:-1])
    color = argb_to_qcolor(title.argb)
    font = font_from_style(title.font_name, title.font_size, title.font_style)
    painter.setFont(font)
    painter.setPen(color)
    px = rect.left() + mm_to_pixels(title.x_mm, dpi)
    py = rect.top() + mm_to_pixels(title.y_mm, dpi)
    painter.drawText(QPointF(px, py + painter.fontMetrics().ascent()), content)
    return text


def draw_content(
    painter: QPainter,
    rect: Rect,
    text: str,
    config: PrintConfig,
    setup: Setup,
    bg_image: QImage | None,
    dpi: float,
) -> None:
    qrect = QRectF(rect.x, rect.y, rect.width, rect.height)
    fill = argb_to_qcolor(getattr(config, "bg_argb", WHITE_ARGB))
    painter.fillRect(qrect, fill)
    if bg_image is not None and not bg_image.isNull():
        painter.drawImage(qrect, bg_image)
    if not text or text.isspace():
        return
    text = new_line(text)
    text = _apply_title(painter, qrect, text, setup.title1, dpi)
    text = _apply_title(painter, qrect, text, setup.title2, dpi)
    ceiling = (
        MAX_FONT
        if config.font_size_text in {"最大化", "每牌尽量大", str(MAX_FONT)}
        else config.font_em_size
    )
    base = font_from_style(config.font_name, ceiling, config.font_style)
    fitted = fit_font_in_rect(
        text,
        base,
        rect.width,
        rect.height,
        setup.margin_ratio,
        paint_device=painter.device(),
        dpi=dpi,
    )
    offset_x = mm_to_pixels(setup.offset_x_mm, dpi)
    offset_y = mm_to_pixels(setup.offset_y_mm, dpi)
    draw_rect = QRectF(rect.x + offset_x, rect.y + offset_y, rect.width, rect.height)
    color = argb_to_qcolor(config.argb)
    painter.save()
    painter.setClipRect(qrect)
    if config.insert_blank:
        _draw_distributed(painter, text, fitted, color, draw_rect, setup.margin_ratio)
    else:
        painter.setFont(fitted)
        painter.setPen(color)
        painter.drawText(draw_rect, int(Qt.AlignmentFlag.AlignCenter), text)
    painter.restore()


def draw_borders(painter: QPainter, edges: list[Edge], style: DashStyle, alpha: int) -> None:
    pen = QPen(QColor(0, 0, 0, max(0, min(255, alpha))))
    pen.setWidth(1)
    if style == DashStyle.NONE:
        return
    if style == DashStyle.CORNER:
        for edge in edges:
            _draw_cross(painter, pen, edge.start)
            _draw_cross(painter, pen, edge.end)
        return
    if style == DashStyle.DASH:
        pen.setStyle(Qt.PenStyle.DashLine)
    elif style == DashStyle.DOT:
        pen.setStyle(Qt.PenStyle.DotLine)
    else:
        pen.setStyle(Qt.PenStyle.SolidLine)
    painter.setPen(pen)
    for edge in edges:
        painter.drawLine(QPointF(*edge.start), QPointF(*edge.end))
