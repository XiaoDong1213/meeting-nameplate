"""题款行：抬头 / 落款。"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from core.colors import argb_to_qcolor, qcolor_to_argb
from core.enums import FontStyle
from core.specs import Title, default_title_xy
from ui.widgets import field_label, pick_color, tune_combo

TITLE_SIZES = [
    str(s) for s in (8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72)
]
_LEGACY_COL_TOKENS = {"第一列", "最后一列"}


class TitleRow(QWidget):
    """题款：抬头（左上）/ 落款（右下）。"""

    changed = pyqtSignal()

    def __init__(
        self,
        title: str,
        hint: str,
        data: Title,
        fonts: list[str],
        styles: list[str],
        is_header: bool,
        width_mm: int,
        height_mm: int,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.enabled = QCheckBox(title)
        self.enabled.setChecked(data.enabled)
        self.enabled.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enabled.setMinimumWidth(72)

        self.content = QLineEdit()
        self.content.setPlaceholderText(hint)
        self.content.setMinimumWidth(140)
        raw = (data.content or "").strip()
        if raw and raw not in _LEGACY_COL_TOKENS:
            self.content.setText(raw)

        self.font = QComboBox()
        tune_combo(self.font, 110)
        self.font.addItems(fonts)
        self.font.setCurrentText(data.font_name if data.font_name in fonts else fonts[0])

        self.size = QComboBox()
        self.size.setEditable(True)
        self.size.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        tune_combo(self.size, 72)
        self.size.addItems(TITLE_SIZES)
        self.size.setCurrentText(str(int(data.font_size)))

        self.style = QComboBox()
        tune_combo(self.style, 72)
        self.style.addItems(styles)
        self.style.setCurrentText(data.font_style.value)

        self._color = argb_to_qcolor(data.argb)
        self.color_btn = QPushButton("文字颜色")
        self.color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_btn.setMinimumWidth(72)
        self.color_btn.clicked.connect(self._pick_color)

        self.x = QSpinBox()
        self.y = QSpinBox()
        self.x.setRange(0, 999)
        self.y.setRange(0, 999)
        self.x.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.y.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.x.setFixedWidth(112)
        self.y.setFixedWidth(112)
        self._auto_pos = True
        self.set_limits(width_mm, height_mm, is_header, data)

        self._fields = (
            self.content,
            self.font,
            self.size,
            self.style,
            self.color_btn,
            self.x,
            self.y,
        )
        for w in self._fields:
            w.setEnabled(data.enabled)
        self.enabled.toggled.connect(self._set_enabled)

        row.addWidget(self.enabled)
        row.addWidget(self.content, 1)
        row.addSpacing(8)
        row.addWidget(field_label("字体"))
        row.addWidget(self.font)
        row.addWidget(field_label("字号"))
        row.addWidget(self.size)
        row.addWidget(field_label("样式"))
        row.addWidget(self.style)
        row.addWidget(self.color_btn)
        row.addSpacing(8)
        row.addWidget(field_label("X"))
        row.addWidget(self.x)
        row.addWidget(field_label("Y"))
        row.addWidget(self.y)

        self.enabled.toggled.connect(self.changed)
        self.content.textChanged.connect(self.changed)
        self.font.currentTextChanged.connect(self.changed)
        self.size.currentTextChanged.connect(self.changed)
        self.style.currentTextChanged.connect(self.changed)
        self.x.valueChanged.connect(self._on_pos_edited)
        self.y.valueChanged.connect(self._on_pos_edited)
        self.x.valueChanged.connect(self.changed)
        self.y.valueChanged.connect(self.changed)

    def _set_enabled(self, on: bool) -> None:
        for w in self._fields:
            w.setEnabled(on)

    def _pick_color(self) -> None:
        chosen = pick_color(self, self._color, "文字颜色")
        if chosen.isValid():
            self._color = chosen
            self.changed.emit()

    def _on_pos_edited(self, *_args) -> None:
        self._auto_pos = False

    def _apply_xy(self, x_mm: int, y_mm: int) -> None:
        self.x.blockSignals(True)
        self.y.blockSignals(True)
        self.x.setValue(x_mm)
        self.y.setValue(y_mm)
        self.x.blockSignals(False)
        self.y.blockSignals(False)

    def set_limits(
        self, width_mm: int, height_mm: int, is_header: bool, data: Title | None = None
    ) -> None:
        self.x.setRange(0, 999)
        self.y.setRange(0, 999)
        default_x, default_y = default_title_xy(width_mm, height_mm, is_header)
        if data is not None:
            raw = (data.content or "").strip()
            unused = (not raw) or raw in _LEGACY_COL_TOKENS
            if unused or (data.x_mm == 0 and data.y_mm == 0):
                self._apply_xy(default_x, default_y)
                self._auto_pos = True
            else:
                self._apply_xy(data.x_mm, data.y_mm)
                self._auto_pos = (data.x_mm, data.y_mm) == (default_x, default_y)
            return
        if self._auto_pos:
            self._apply_xy(default_x, default_y)

    def to_title(self) -> Title:
        try:
            font_style = FontStyle(self.style.currentText())
        except ValueError:
            font_style = FontStyle.REGULAR
        try:
            font_size = float(self.size.currentText().strip())
        except ValueError:
            font_size = 20.0
        return Title(
            enabled=self.enabled.isChecked(),
            content=self.content.text().strip(),
            font_name=self.font.currentText(),
            font_size=font_size if font_size > 0 else 20.0,
            font_style=font_style,
            argb=qcolor_to_argb(self._color),
            x_mm=self.x.value(),
            y_mm=self.y.value(),
        )
