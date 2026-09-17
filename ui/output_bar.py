"""Printer, border style, insets, and distribute-align rows."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtPrintSupport import QPrinterInfo
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.enums import DashStyle
from ui.widgets import field_label, fit_combo_width, tune_combo, tune_slider

_BORDER_INSET_RANGE = (-99, 99)


class OutputBar(QWidget):
    changed = pyqtSignal()
    alpha_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self.printer_combo = QComboBox()
        self.line_combo = QComboBox()
        tune_combo(self.printer_combo, 200)
        tune_combo(self.line_combo, 108)

        self.border_top = QCheckBox("上边")
        self.border_bottom = QCheckBox("下边")
        self.border_left = QCheckBox("左边")
        self.border_right = QCheckBox("右边")
        for box in (self.border_top, self.border_bottom, self.border_left, self.border_right):
            box.setCursor(Qt.CursorShape.PointingHandCursor)
            box.setChecked(True)

        self.border_fold = QCheckBox("对折中线")
        self.border_fold.setCursor(Qt.CursorShape.PointingHandCursor)
        self.border_fold.setChecked(True)
        self.distribute = QCheckBox("文字分散对齐")
        self.distribute.setCursor(Qt.CursorShape.PointingHandCursor)

        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 255)
        self.alpha_slider.setMinimumWidth(90)
        self.alpha_slider.setMaximumWidth(120)
        tune_slider(self.alpha_slider)

        self.inset_top = self._make_inset_spin()
        self.inset_bottom = self._make_inset_spin()
        self.inset_left = self._make_inset_spin()
        self.inset_right = self._make_inset_spin()

        # Row 1 — printer / line / fold / density / distribute
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(6)
        row1.addWidget(field_label("输出打印机"))
        row1.addWidget(self.printer_combo, 3)
        row1.addWidget(field_label("外框线型"))
        row1.addWidget(self.line_combo, 1)
        row1.addWidget(self.border_fold)
        row1.addWidget(field_label("线条浓度"))
        row1.addWidget(self.alpha_slider, 1)
        row1.addWidget(self.distribute)
        root.addLayout(row1)

        # Row 2 — per-side border enable + inset (mm)
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(8)
        row2.addWidget(field_label("边框偏移"))
        for box, spin in (
            (self.border_top, self.inset_top),
            (self.border_bottom, self.inset_bottom),
            (self.border_left, self.inset_left),
            (self.border_right, self.inset_right),
        ):
            row2.addWidget(box)
            row2.addWidget(spin)
        row2.addStretch(1)
        root.addLayout(row2)

        printers = [p.printerName() for p in QPrinterInfo.availablePrinters()]
        self.printer_combo.addItems(printers or [""])
        self.line_combo.addItems([s.value for s in DashStyle])
        fit_combo_width(self.printer_combo, floor=200, ceiling=320)
        fit_combo_width(self.line_combo, floor=108, ceiling=140)

        self.line_combo.currentTextChanged.connect(self.changed)
        self.alpha_slider.valueChanged.connect(self.alpha_changed)
        self.alpha_slider.valueChanged.connect(self.changed)
        for box in (
            self.border_top,
            self.border_bottom,
            self.border_left,
            self.border_right,
            self.border_fold,
            self.distribute,
        ):
            box.toggled.connect(self.changed)
        for spin in (self.inset_top, self.inset_bottom, self.inset_left, self.inset_right):
            spin.valueChanged.connect(self.changed)

    @staticmethod
    def _make_inset_spin() -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(*_BORDER_INSET_RANGE)
        spin.setSuffix("mm")
        spin.setToolTip("边框偏移：正数向内缩，负数向外扩")
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setFixedWidth(76)
        return spin

    def set_fold_line_enabled(self, enabled: bool) -> None:
        """Single-sided cards have no fold mid-line."""
        self.border_fold.setEnabled(enabled)
        if not enabled:
            self.border_fold.setChecked(False)

    def border_insets_mm(self) -> tuple[int, int, int, int]:
        """top, bottom, left, right in mm."""
        return (
            self.inset_top.value(),
            self.inset_bottom.value(),
            self.inset_left.value(),
            self.inset_right.value(),
        )

    def set_border_insets_mm(self, top: int, bottom: int, left: int, right: int) -> None:
        for spin, value in (
            (self.inset_top, top),
            (self.inset_bottom, bottom),
            (self.inset_left, left),
            (self.inset_right, right),
        ):
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
