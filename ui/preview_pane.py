"""Single-card live preview with prev/next navigation."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.preview.live_preview import LivePreviewWidget


class PreviewPane(QWidget):
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        right = QVBoxLayout(self)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(4)
        prev_lab = QLabel("单牌预览")
        prev_lab.setObjectName("sectionTitle")
        right.addWidget(prev_lab)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(6)
        self.live_preview = LivePreviewWidget()
        preview_row.addWidget(self.live_preview, 1)

        nav = QVBoxLayout()
        nav.setSpacing(0)
        nav.setContentsMargins(0, 0, 0, 0)
        self.preview_prev_btn = QPushButton("上一张牌")
        self.preview_next_btn = QPushButton("下一张牌")
        self.preview_page_label = QLabel("1 / 1")
        self.preview_page_label.setObjectName("previewNavLabel")
        self.preview_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for w in (self.preview_prev_btn, self.preview_next_btn, self.preview_page_label):
            w.setFixedSize(72, 28)
        for b in (self.preview_prev_btn, self.preview_next_btn):
            b.setObjectName("previewNavButton")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        cluster = QVBoxLayout()
        cluster.setSpacing(8)
        cluster.setContentsMargins(0, 0, 0, 0)
        cluster.addWidget(self.preview_prev_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        cluster.addWidget(self.preview_page_label, 0, Qt.AlignmentFlag.AlignHCenter)
        cluster.addWidget(self.preview_next_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        nav.addStretch(1)
        nav.addLayout(cluster)
        nav.addStretch(1)
        preview_row.addLayout(nav)
        right.addLayout(preview_row, 1)

        self.preview_prev_btn.clicked.connect(self.prev_clicked)
        self.preview_next_btn.clicked.connect(self.next_clicked)

    def set_page(self, current: int, total: int, has_lines: bool) -> None:
        self.preview_page_label.setText(f"{current} / {total}" if has_lines else "0 / 0")
        self.preview_prev_btn.setEnabled(has_lines and current > 1)
        self.preview_next_btn.setEnabled(has_lines and current < total)
