"""Desk-card roster editor."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

EDITOR_DEFAULT_PT = 16.0


class RosterPanel(QWidget):
    text_changed = pyqtSignal()
    insert_spaces_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        left = QVBoxLayout(self)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(4)

        list_head = QHBoxLayout()
        list_head.setContentsMargins(0, 0, 0, 0)
        list_head.setSpacing(8)
        list_lab = QLabel("桌牌名单")
        list_lab.setObjectName("sectionTitle")
        self.insert_idespace_btn = QPushButton("两字名加空格")
        self.insert_idespace_btn.setObjectName("previewNavButton")
        self.insert_idespace_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.insert_idespace_btn.setFixedHeight(28)
        list_head.addWidget(list_lab)
        list_head.addStretch(1)
        list_head.addWidget(self.insert_idespace_btn)
        left.addLayout(list_head)

        self.editor = QTextEdit()
        self.editor.setObjectName("contentEditor")
        self.editor.setPlaceholderText("每行一张桌牌；可用 Tab 分列")
        left.addWidget(self.editor, 1)

        self.insert_idespace_btn.clicked.connect(self.insert_spaces_clicked)
        self.editor.textChanged.connect(self.text_changed)

    def preview_lines(self) -> list[str]:
        return [ln for ln in self.editor.toPlainText().splitlines() if ln.strip()]
