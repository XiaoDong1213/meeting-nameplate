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
from core.specs import (
    CARD_ORIENT_LABELS,
    CARD_ORIENT_LANDSCAPE,
    CARD_ORIENT_PORTRAIT,
    MIRROR_MODE_FOLD,
    MIRROR_MODE_LABELS,
    MIRROR_MODE_SINGLE,
)
from ui.font_list import chinese_fonts
from ui.widgets import field_label, fit_combo_width, pick_color, tune_combo

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
    """Top settings: body type, card setup, and content inset."""

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

        self.font_combo = QComboBox()
        self.style_combo = QComboBox()
        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.spec_combo = QComboBox()
        self.spec_combo.setEditable(True)
        self.spec_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mirror_combo = QComboBox()
        self.orient_combo = QComboBox()
        for combo, width in (
            (self.font_combo, 140),
            (self.style_combo, 88),
            (self.size_combo, 156),
            (self.spec_combo, 168),
            (self.mirror_combo, 132),
            (self.orient_combo, 88),
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

        # Row 1 — body type / color / background
        row1 = QGridLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setHorizontalSpacing(6)
        row1.setVerticalSpacing(6)
        row1.addWidget(field_label("正文字体"), 0, 0)
        row1.addWidget(self.font_combo, 0, 1)
        row1.addWidget(field_label("正文样式"), 0, 2)
        row1.addWidget(self.style_combo, 0, 3)
        row1.addWidget(field_label("正文字号"), 0, 4)
        row1.addWidget(self.size_combo, 0, 5)
        row1.addWidget(self.color_btn, 0, 6)
        row1.addWidget(self.bg_btn, 0, 7)
        row1.addWidget(self.bg_hint, 0, 8)
        row1.setColumnStretch(1, 2)
        row1.setColumnStretch(5, 1)
        root.addLayout(row1)

        # Row 2 — card spec / fold / orient / content inset
        self.margin_spin = QDoubleSpinBox()
        self.margin_spin.setRange(0.0, 0.5)
        self.margin_spin.setSingleStep(0.01)
        self.margin_spin.setDecimals(2)
        self.margin_spin.setFixedWidth(80)
        self.offset_x = QSpinBox()
        self.offset_x.setRange(-999, 999)
        self.offset_x.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.offset_x.setFixedWidth(88)
        self.offset_y = QSpinBox()
        self.offset_y.setRange(-999, 999)
        self.offset_y.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.offset_y.setFixedWidth(88)

        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(field_label("桌牌规格"))
        row2.addWidget(self.spec_combo, 2)
        row2.addWidget(field_label("牌面"))
        row2.addWidget(self.mirror_combo)
        row2.addWidget(field_label("桌牌方向"))
        row2.addWidget(self.orient_combo)
        row2.addWidget(field_label("内容边距"))
        row2.addWidget(self.margin_spin)
        row2.addWidget(field_label("水平偏移"))
        row2.addWidget(self.offset_x)
        row2.addWidget(field_label("垂直偏移"))
        row2.addWidget(self.offset_y)
        row2.addStretch(1)
        root.addLayout(row2)

        self.color_btn.clicked.connect(self.color_clicked)
        self.font_combo.currentTextChanged.connect(self.changed)
        self.style_combo.currentTextChanged.connect(self.changed)
        self.size_combo.currentTextChanged.connect(self.changed)
        self.spec_combo.currentTextChanged.connect(self.spec_changed)
        self.spec_combo.currentTextChanged.connect(self.changed)
        self.mirror_combo.currentTextChanged.connect(self.changed)
        self.orient_combo.currentTextChanged.connect(self.changed)
        self.margin_spin.valueChanged.connect(self.changed)
        self.offset_x.valueChanged.connect(self.changed)
        self.offset_y.valueChanged.connect(self.changed)

        fonts = chinese_fonts() or ["楷体", "黑体", "宋体"]
        self.font_combo.addItems(fonts)
        self.style_combo.addItems([s.value for s in FontStyle])
        self.size_combo.addItems(BODY_SIZES)
        self.mirror_combo.addItems(list(MIRROR_MODE_LABELS))
        self.orient_combo.addItems(list(CARD_ORIENT_LABELS))
        # Font list can be huge — only keep a readable closed width.
        fit_combo_width(self.font_combo, floor=140, ceiling=200)
        fit_combo_width(self.style_combo, floor=88, ceiling=120)
        fit_combo_width(self.size_combo, floor=156, ceiling=200)
        fit_combo_width(self.mirror_combo, floor=132, ceiling=160)
        fit_combo_width(self.orient_combo, floor=88, ceiling=120)
        from core.specs import DEFAULT_SIZE_LIST

        fit_combo_width(
            self.spec_combo,
            floor=168,
            ceiling=220,
            extra_texts=list(DEFAULT_SIZE_LIST) + ["210*110mm", "297*100mm"],
        )
        self.spec_combo.editTextChanged.connect(self._fit_spec_width)

    def _fit_spec_width(self, *_args) -> None:
        fit_combo_width(self.spec_combo, floor=168, ceiling=220)

    def mirror_enabled(self) -> bool:
        return self.mirror_combo.currentText() != MIRROR_MODE_SINGLE

    def set_mirror_enabled(self, mirror: bool) -> None:
        label = MIRROR_MODE_FOLD if mirror else MIRROR_MODE_SINGLE
        self.mirror_combo.setCurrentText(label)

    def card_landscape(self) -> bool:
        return self.orient_combo.currentText() != CARD_ORIENT_PORTRAIT

    def set_card_landscape(self, landscape: bool) -> None:
        label = CARD_ORIENT_LANDSCAPE if landscape else CARD_ORIENT_PORTRAIT
        self.orient_combo.setCurrentText(label)

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
