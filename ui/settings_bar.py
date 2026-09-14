"""Body font / spec / color / background + content margins."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.colors import WHITE_ARGB, argb_to_qcolor, qcolor_to_argb
from core.enums import FontStyle
from ui.font_list import chinese_fonts
from ui.widgets import field_label, pick_color, tune_combo

BODY_SIZES = [
    "自动适应",
    "每牌尽量大",
    "8",
    "9",
    "10",
    "11",
    "12",
    "14",
    "16",
    "18",
    "20",
    "22",
    "24",
    "26",
    "28",
    "36",
    "48",
    "72",
    "96",
    "120",
    "144",
    "168",
    "192",
]


class SettingsBar(QWidget):
    """Top settings: body type and content inset."""

    changed = pyqtSignal()
    color_clicked = pyqtSignal()
    spec_changed = pyqtSignal()
    bg_picked = pyqtSignal(str)
    bg_color_picked = pyqtSignal(int)
    bg_cleared = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        g = QGridLayout()
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(6)
        g.setVerticalSpacing(6)

        self.font_combo = QComboBox()
        self.style_combo = QComboBox()
        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.spec_combo = QComboBox()
        self.spec_combo.setEditable(True)
        self.spec_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        for combo, width in (
            (self.font_combo, 140),
            (self.style_combo, 88),
            (self.size_combo, 156),
            (self.spec_combo, 160),
        ):
            tune_combo(combo, width)

        self.color_btn = QPushButton("正文字色")
        self.color_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.bg_btn = QToolButton()
        self.bg_btn.setText("牌面背景 ▾")
        self.bg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bg_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        bg_menu = QMenu(self.bg_btn)
        act_color = QAction("选择纯色…", self)
        act_pick = QAction("选择图片…", self)
        act_clear = QAction("恢复白底", self)
        act_color.triggered.connect(self._pick_bg_color)
        act_pick.triggered.connect(self._pick_bg)
        act_clear.triggered.connect(self.bg_cleared.emit)
        bg_menu.addAction(act_color)
        bg_menu.addAction(act_pick)
        bg_menu.addAction(act_clear)
        self.bg_btn.setMenu(bg_menu)

        self._bg_argb = WHITE_ARGB
        self.bg_hint = QLabel("白底")
        self.bg_hint.setObjectName("hintLabel")
        self.bg_hint.setMaximumWidth(88)

        g.addWidget(field_label("正文字体"), 0, 0)
        g.addWidget(self.font_combo, 0, 1)
        g.addWidget(field_label("正文样式"), 0, 2)
        g.addWidget(self.style_combo, 0, 3)
        g.addWidget(field_label("正文字号"), 0, 4)
        g.addWidget(self.size_combo, 0, 5)
        g.addWidget(field_label("桌牌规格"), 0, 6)
        g.addWidget(self.spec_combo, 0, 7)
        g.addWidget(self.color_btn, 0, 8)
        g.addWidget(self.bg_btn, 0, 9)
        g.addWidget(self.bg_hint, 0, 10)
        g.setColumnStretch(1, 2)
        g.setColumnStretch(7, 2)
        root.addLayout(g)

        lr = QHBoxLayout()
        lr.setSpacing(6)
        lr.addWidget(field_label("内容边距"))
        self.margin_spin = QDoubleSpinBox()
        self.margin_spin.setRange(0.0, 0.5)
        self.margin_spin.setSingleStep(0.01)
        self.margin_spin.setDecimals(2)
        self.margin_spin.setFixedWidth(96)
        lr.addWidget(self.margin_spin)
        lr.addWidget(field_label("水平偏移(mm)"))
        self.offset_x = QSpinBox()
        self.offset_x.setRange(-999, 999)
        self.offset_x.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.offset_x.setFixedWidth(112)
        lr.addWidget(self.offset_x)
        lr.addWidget(field_label("垂直偏移(mm)"))
        self.offset_y = QSpinBox()
        self.offset_y.setRange(-999, 999)
        self.offset_y.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.offset_y.setFixedWidth(112)
        lr.addWidget(self.offset_y)
        lr.addStretch(1)
        root.addLayout(lr)

        self.color_btn.clicked.connect(self.color_clicked)
        self.font_combo.currentTextChanged.connect(self.changed)
        self.style_combo.currentTextChanged.connect(self.changed)
        self.size_combo.currentTextChanged.connect(self.changed)
        self.spec_combo.currentTextChanged.connect(self.spec_changed)
        self.spec_combo.currentTextChanged.connect(self.changed)
        self.margin_spin.valueChanged.connect(self.changed)
        self.offset_x.valueChanged.connect(self.changed)
        self.offset_y.valueChanged.connect(self.changed)

        fonts = chinese_fonts() or ["楷体", "黑体", "宋体"]
        self.font_combo.addItems(fonts)
        self.style_combo.addItems([s.value for s in FontStyle])
        self.size_combo.addItems(BODY_SIZES)

    def set_bg_hint(self, has_image: bool, color_argb: int = WHITE_ARGB) -> None:
        self._bg_argb = color_argb
        if has_image:
            self.bg_hint.setText("已设背景图")
        elif (color_argb & 0x00FFFFFF) != 0x00FFFFFF:
            self.bg_hint.setText("已设纯色")
        else:
            self.bg_hint.setText("白底")

    def set_offset_limits(self, width_mm: int, height_mm: int) -> None:
        _ = (width_mm, height_mm)
        self.offset_x.setRange(-999, 999)
        self.offset_y.setRange(-999, 999)

    def _pick_bg_color(self) -> None:
        chosen = pick_color(self, argb_to_qcolor(self._bg_argb), "牌面纯色")
        if chosen.isValid():
            self.bg_color_picked.emit(qcolor_to_argb(chosen))

    def _pick_bg(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", str(Path.cwd()), "图片文件 (*.bmp *.jpg *.jpeg *.png)"
        )
        if path:
            self.bg_picked.emit(path)
