"""On-screen multi-sheet preview (one / two pages)."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPen
from PyQt6.QtWidgets import QScrollArea, QSizePolicy, QWidget

MODE_ONE = "one"
MODE_TWO = "two"

_GAP = 28
_MARGIN = 24
_PAPER = QColor("#FFFFFF")
_BOARD = QColor("#8A99A8")
_EDGE = QColor("#5A6A7A")


class SheetsCanvas(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sheetsCanvas")
        self._pages: list[QImage] = []
        self._mode = MODE_ONE
        self._index = 0
        self._zoom = 1.0
        self._fit = True
        self._vp = QSize(800, 600)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

    def set_viewport_size(self, size: QSize) -> None:
        self._vp = size
        self._relayout()

    def set_pages(self, pages: list[QImage]) -> None:
        self._pages = pages
        if self._index >= len(pages):
            self._index = max(0, len(pages) - 1)
        self._relayout()

    def set_mode(self, mode: str) -> None:
        self._mode = mode if mode in {MODE_ONE, MODE_TWO} else MODE_ONE
        if self._mode == MODE_TWO:
            self._index -= self._index % 2
        self._relayout()

    def set_index(self, index: int) -> None:
        n = len(self._pages)
        if n <= 0:
            self._index = 0
        else:
            self._index = max(0, min(index, n - 1))
        if self._mode == MODE_TWO:
            self._index -= self._index % 2
        self.update()

    def zoom_by(self, delta: float) -> None:
        self._fit = False
        self._zoom = max(0.2, min(3.0, self._zoom + delta))
        self._relayout()

    def fit(self) -> None:
        self._fit = True
        self._relayout()

    def page_count(self) -> int:
        return len(self._pages)

    def current_index(self) -> int:
        return self._index

    def mode(self) -> str:
        return self._mode

    def visible_indices(self) -> list[int]:
        n = len(self._pages)
        if n == 0:
            return []
        if self._mode == MODE_TWO:
            start = self._index - (self._index % 2)
            return [i for i in (start, start + 1) if i < n]
        return [self._index]

    def step(self) -> int:
        return 2 if self._mode == MODE_TWO else 1

    def _grid(self, count: int) -> tuple[int, int]:
        if count <= 1:
            return 1, 1
        if self._mode == MODE_TWO:
            return min(2, count), 1
        return 1, 1

    def _paper_size(self) -> tuple[int, int]:
        if not self._pages:
            return 1, 1
        return self._pages[0].width(), self._pages[0].height()

    def _scale(self) -> float:
        indices = self.visible_indices()
        if not indices:
            return 1.0
        pw, ph = self._paper_size()
        cols, rows = self._grid(len(indices))
        total_w = cols * pw + (cols - 1) * _GAP
        total_h = rows * ph + (rows - 1) * _GAP
        if self._fit:
            avail_w = max(1, self._vp.width() - _MARGIN * 2)
            avail_h = max(1, self._vp.height() - _MARGIN * 2)
            return max(0.08, min(avail_w / total_w, avail_h / total_h, 1.25))
        return self._zoom

    def _content_size(self) -> QSize:
        indices = self.visible_indices()
        if not indices:
            return self._vp
        pw, ph = self._paper_size()
        cols, rows = self._grid(len(indices))
        scale = self._scale()
        w = int(cols * pw * scale + (cols - 1) * _GAP) + _MARGIN * 2
        h = int(rows * ph * scale + (rows - 1) * _GAP) + _MARGIN * 2
        return QSize(max(w, self._vp.width()), max(h, self._vp.height()))

    def _relayout(self) -> None:
        size = self._content_size()
        self.setMinimumSize(size)
        self.resize(size)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), _BOARD)
        indices = self.visible_indices()
        if not indices:
            painter.setPen(QColor("#F3F7FB"))
            painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), "暂无预览")
            return
        pw, ph = self._paper_size()
        cols, _rows = self._grid(len(indices))
        scale = self._scale()
        cell_w = pw * scale
        cell_h = ph * scale
        total_w = cols * cell_w + (cols - 1) * _GAP
        total_h = cell_h
        ox = (self.width() - total_w) / 2
        oy = (self.height() - total_h) / 2
        for n, idx in enumerate(indices):
            col = n % cols
            row = n // cols
            x = ox + col * (cell_w + _GAP)
            y = oy + row * (cell_h + _GAP)
            dest = QRectF(x, y, cell_w, cell_h)
            painter.fillRect(dest, _PAPER)
            painter.setPen(QPen(_EDGE, 1))
            painter.drawRect(dest.adjusted(0.5, 0.5, -0.5, -0.5))
            page = self._pages[idx]
            painter.drawImage(dest, page)


class SheetsView(QScrollArea):
    index_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sheetsView")
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.canvas = SheetsCanvas()
        self.setWidget(self.canvas)
        self.setStyleSheet("QScrollArea#sheetsView { border: none; background: #8A99A8; }")

    def wheelEvent(self, event) -> None:  # noqa: N802
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y() or event.pixelDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
            return
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return
        step = self.step()
        nxt = self.current_index() + (-step if delta > 0 else step)
        if 0 <= nxt < self.page_count():
            self.set_index(nxt)
            self.index_changed.emit()
        event.accept()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.canvas.set_viewport_size(self.viewport().size())

    def set_pages(self, pages: list[QImage]) -> None:
        self.canvas.set_pages(pages)

    def set_mode(self, mode: str) -> None:
        self.canvas.set_mode(mode)

    def set_index(self, index: int) -> None:
        self.canvas.set_index(index)

    def zoom_in(self) -> None:
        self.canvas.zoom_by(0.1)

    def zoom_out(self) -> None:
        self.canvas.zoom_by(-0.1)

    def fit(self) -> None:
        self.canvas.fit()

    def page_count(self) -> int:
        return self.canvas.page_count()

    def current_index(self) -> int:
        return self.canvas.current_index()

    def mode(self) -> str:
        return self.canvas.mode()

    def visible_indices(self) -> list[int]:
        return self.canvas.visible_indices()

    def step(self) -> int:
        return self.canvas.step()
