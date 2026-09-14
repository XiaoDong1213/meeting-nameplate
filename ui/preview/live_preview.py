"""On-screen live preview of one desk card."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from core.colors import argb_to_qcolor
from core.config import PrintConfig
from core.layout import Edge, Rect, edges_of_rect
from render.paint import draw_borders, draw_content
from core.specs import Setup, mm_to_pixels


class LivePreviewWidget(QWidget):
    """Scaled preview of one card (mirror shows both halves)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("livePreview")
        self.setMinimumWidth(280)
        self.setMinimumHeight(200)
        self._config: PrintConfig | None = None
        self._setup: Setup | None = None
        self._text: str = ""
        self._bg: QImage | None = None
        self._bg_path: str | None = None

    def set_snapshot(
        self,
        config: PrintConfig,
        setup: Setup,
        text: str,
    ) -> None:
        self._config = config
        self._setup = setup
        self._text = text or ""
        path = config.image_file
        if path and Path(path).exists():
            if path != self._bg_path or self._bg is None:
                img = QImage(path)
                self._bg = img if not img.isNull() else None
                self._bg_path = path if self._bg is not None else None
        else:
            self._bg = None
            self._bg_path = None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), QColor("#E8F1F8"))

            if self._config is None or self._setup is None:
                painter.setPen(QColor("#5A6A7A"))
                painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), "暂无预览")
                return

            dpi = 96.0
            setup = self._setup
            cfg = self._config
            card_w = max(1, mm_to_pixels(setup.width_mm, dpi))
            card_h = max(1, mm_to_pixels(setup.height_mm * (2 if setup.mirror else 1), dpi))

            margin = 2
            avail_w = max(1, self.width() - margin * 2)
            avail_h = max(1, self.height() - margin * 2)
            scale = min(avail_w / card_w, avail_h / card_h)
            draw_w = card_w * scale
            draw_h = card_h * scale
            ox = (self.width() - draw_w) / 2
            oy = (self.height() - draw_h) / 2

            painter.save()
            painter.translate(ox, oy)
            painter.scale(scale, scale)

            painter.fillRect(QRectF(0, 0, card_w, card_h), argb_to_qcolor(cfg.bg_argb))
            painter.setPen(QPen(QColor("#D4DEE8"), 1))
            painter.drawRect(QRectF(0.5, 0.5, card_w - 1, card_h - 1))

            text = self._text
            edges: list[Edge] = []
            if setup.mirror:
                half = Rect(0, card_h // 2, card_w, card_h // 2)
                draw_content(painter, half, text, cfg, setup, self._bg, dpi)
                mid_y = card_h // 2
                if cfg.border_fold:
                    edges.append(Edge.normalize((0, mid_y), (card_w, mid_y)))
                painter.save()
                painter.translate(card_w, card_h)
                painter.rotate(180)
                draw_content(painter, half, text, cfg, setup, self._bg, dpi)
                painter.restore()
                outer = Rect(0, 0, card_w, card_h)
            else:
                outer = Rect(0, 0, card_w, card_h)
                draw_content(painter, outer, text, cfg, setup, self._bg, dpi)

            edges.extend(
                edges_of_rect(
                    outer,
                    top=cfg.border_top,
                    right=cfg.border_right,
                    bottom=cfg.border_bottom,
                    left=cfg.border_left,
                )
            )
            draw_borders(painter, edges, cfg.line_style, cfg.border_alpha)
            painter.restore()
        except Exception:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).exception("live preview paint failed")
            if painter.isActive():
                painter.fillRect(self.rect(), QColor("#E8F1F8"))
                painter.setPen(QColor("#DC2626"))
                painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), "预览绘制失败")
        finally:
            if painter.isActive():
                painter.end()
