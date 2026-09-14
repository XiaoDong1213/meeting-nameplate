"""Printer, border style, and distribute-align row."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtPrintSupport import QPrinterInfo
from PyQt6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QSlider, QWidget

from core.enums import DashStyle
from ui.widgets import field_label, tune_combo, tune_slider


class OutputBar(QWidget):
    changed = pyqtSignal()
    alpha_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        fr = QHBoxLayout(self)
        fr.setContentsMargins(0, 0, 0, 0)
        fr.setSpacing(6)

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

        fr.addWidget(field_label("输出打印机"))
        fr.addWidget(self.printer_combo, 3)
        fr.addWidget(field_label("外框线型"))
        fr.addWidget(self.line_combo, 1)
        fr.addWidget(self.border_top)
        fr.addWidget(self.border_bottom)
        fr.addWidget(self.border_left)
        fr.addWidget(self.border_right)
        fr.addWidget(self.border_fold)
        fr.addWidget(field_label("线条浓度"))
        fr.addWidget(self.alpha_slider, 1)
        fr.addWidget(self.distribute)

        printers = [p.printerName() for p in QPrinterInfo.availablePrinters()]
        self.printer_combo.addItems(printers or [""])
        self.line_combo.addItems([s.value for s in DashStyle])

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
