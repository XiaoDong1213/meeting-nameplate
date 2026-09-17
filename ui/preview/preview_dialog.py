"""Custom print preview dialog — paper size / orientation + toolbar."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeySequence, QPageLayout, QPageSize, QShortcut
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter, QPrinterInfo
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from core.config import PrintConfig
from core.pages import PAGE_ORIENT_KEYS, PAGE_ORIENT_LABELS
from core.paths import app_icon_path
from render.document import paint_to_printer, render_sheets, resolve_landscape
from render.pages import PAGE_SIZES
from ui.preview.sheets_view import MODE_ONE, MODE_TWO, SheetsView
from ui.widgets import fit_combo_width, tune_combo

_log = logging.getLogger(__name__)


class PreviewDialog(QDialog):
    """打印预览：纸张、方向、缩放、翻页、打印。"""

    def __init__(
        self,
        printer: QPrinter,
        config: PrintConfig,
        paint_callback: Callable[[QPrinter], None] | None = None,
        *,
        page_size: str = "A4",
        page_orientation: str = "auto",
        on_page_settings: Callable[[str, str], None] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("PreviewDialog")
        self.setWindowTitle("排版预览")
        icon_file = app_icon_path()
        if icon_file.is_file():
            self.setWindowIcon(QIcon(str(icon_file)))
        self.resize(1100, 760)
        self.setMinimumSize(900, 560)
        self._printer = printer
        self._config = config
        self._paint_callback = paint_callback or (lambda p: paint_to_printer(p, config))
        self._on_page_settings = on_page_settings
        self._printing = False
        self._paint_error: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        bar = QFrame()
        bar.setObjectName("previewToolbar")
        bar_lay = QVBoxLayout(bar)
        bar_lay.setContentsMargins(16, 10, 16, 10)
        bar_lay.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        self.page_label = QLabel("1 / 1")
        self.page_label.setObjectName("previewPageLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_in_btn = QPushButton("放大")
        self.fit_btn = QPushButton("适应窗口")
        view_lab = QLabel("页视图")
        view_lab.setObjectName("fieldLabel")
        self.view_one_btn = QPushButton("一页")
        self.view_two_btn = QPushButton("两页")
        self._view_group = QButtonGroup(self)
        self._view_group.setExclusive(True)
        for btn in (self.view_one_btn, self.view_two_btn):
            btn.setCheckable(True)
            btn.setObjectName("previewViewButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(30)
            self._view_group.addButton(btn)
        self.view_one_btn.setChecked(True)
        self.view_one_btn.setToolTip("每次显示一张纸")
        self.view_two_btn.setToolTip("两张一组：1–2，然后 3")

        size_lab = QLabel("打印纸张")
        size_lab.setObjectName("fieldLabel")
        self.size_combo = QComboBox()
        self.size_combo.addItems(list(PAGE_SIZES.keys()))
        if page_size in PAGE_SIZES:
            self.size_combo.setCurrentText(page_size)
        tune_combo(self.size_combo, 88)
        fit_combo_width(self.size_combo, floor=88, ceiling=120)

        orient_lab = QLabel("页面方向")
        orient_lab.setObjectName("fieldLabel")
        self.orient_combo = QComboBox()
        for label, _key in PAGE_ORIENT_LABELS:
            self.orient_combo.addItem(label)
        if page_orientation in PAGE_ORIENT_KEYS:
            self.orient_combo.setCurrentIndex(PAGE_ORIENT_KEYS.index(page_orientation))
        tune_combo(self.orient_combo, 110)
        fit_combo_width(self.orient_combo, floor=110, ceiling=140)

        self.print_btn = QPushButton("发送到打印机")
        self.print_btn.setObjectName("primaryButton")
        self.print_btn.setMinimumWidth(128)
        self.print_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.close_btn = QPushButton("关闭预览")
        self.close_btn.setMinimumWidth(96)
        self.close_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        for btn in (
            self.prev_btn,
            self.next_btn,
            self.zoom_out_btn,
            self.zoom_in_btn,
            self.fit_btn,
            self.print_btn,
            self.close_btn,
        ):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        row1.addWidget(self.prev_btn)
        row1.addWidget(self.next_btn)
        row1.addWidget(self.page_label)
        row1.addSpacing(8)
        row1.addWidget(self.zoom_out_btn)
        row1.addWidget(self.zoom_in_btn)
        row1.addWidget(self.fit_btn)
        row1.addSpacing(12)
        row1.addWidget(view_lab)
        row1.addWidget(self.view_one_btn)
        row1.addWidget(self.view_two_btn)
        row1.addStretch(1)

        row2.addWidget(size_lab)
        row2.addWidget(self.size_combo)
        row2.addWidget(orient_lab)
        row2.addWidget(self.orient_combo)
        row2.addStretch(1)
        row2.addWidget(self.print_btn)
        row2.addWidget(self.close_btn)

        bar_lay.addLayout(row1)
        bar_lay.addLayout(row2)
        root.addWidget(bar)

        self.sheets = SheetsView(self)
        root.addWidget(self.sheets, 1)

        self.prev_btn.clicked.connect(self._go_prev)
        self.next_btn.clicked.connect(self._go_next)
        self.sheets.index_changed.connect(self._update_page_label)
        self.zoom_out_btn.clicked.connect(self.sheets.zoom_out)
        self.zoom_in_btn.clicked.connect(self.sheets.zoom_in)
        self.fit_btn.clicked.connect(self.sheets.fit)
        self.view_one_btn.clicked.connect(lambda: self._set_view(MODE_ONE))
        self.view_two_btn.clicked.connect(lambda: self._set_view(MODE_TWO))
        self.size_combo.currentTextChanged.connect(self._apply_page_settings)
        self.orient_combo.currentIndexChanged.connect(self._apply_page_settings)
        self.print_btn.clicked.connect(self._print)
        self.close_btn.clicked.connect(self.accept)

        QShortcut(QKeySequence("Escape"), self, activated=self.accept)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self._print)

        self._apply_page_settings()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.sheets.canvas.set_viewport_size(self.sheets.viewport().size())
        self.sheets.fit()

    def _report_paint_error(self) -> None:
        if not self._paint_error:
            return
        msg = self._paint_error
        self._paint_error = None
        QMessageBox.warning(
            self,
            "预览失败",
            f"排版预览时出错，已阻止闪退：\n{msg}",
        )

    def _current_orientation_key(self) -> str:
        idx = self.orient_combo.currentIndex()
        if 0 <= idx < len(PAGE_ORIENT_KEYS):
            return PAGE_ORIENT_KEYS[idx]
        return "auto"

    def _sync_printer_page(self) -> None:
        size_name = self.size_combo.currentText()
        size_id = PAGE_SIZES.get(size_name, QPageSize.PageSizeId.A4)
        self._printer.setPageSize(QPageSize(size_id))
        self._printer.setFullPage(True)
        setup = self._config.current_setup
        landscape = bool(setup and resolve_landscape(self._config, setup))
        self._printer.setPageOrientation(
            QPageLayout.Orientation.Landscape if landscape else QPageLayout.Orientation.Portrait
        )

    def _refresh_sheets(self) -> None:
        try:
            images = render_sheets(self._config)
            self._paint_error = None
        except Exception as exc:  # noqa: BLE001
            _log.exception("preview raster failed")
            self._paint_error = str(exc)
            images = []
        self.sheets.set_pages(images)
        self.sheets.fit()
        self._update_page_label()
        self._report_paint_error()

    def _apply_page_settings(self, *_args) -> None:
        size_name = self.size_combo.currentText()
        orient = self._current_orientation_key()
        self._config.page_size = size_name
        self._config.page_orientation = orient
        if self._on_page_settings:
            self._on_page_settings(size_name, orient)
        self._sync_printer_page()
        self._refresh_sheets()

    def _set_view(self, mode: str) -> None:
        self.sheets.set_mode(mode)
        self.sheets.fit()
        self._update_page_label()

    def _go_prev(self) -> None:
        nxt = self.sheets.current_index() - self.sheets.step()
        if nxt >= 0:
            self.sheets.set_index(nxt)
            self._update_page_label()

    def _go_next(self) -> None:
        nxt = self.sheets.current_index() + self.sheets.step()
        if nxt < self.sheets.page_count():
            self.sheets.set_index(nxt)
            self._update_page_label()

    def _update_page_label(self) -> None:
        total = self.sheets.page_count()
        if total <= 0:
            self.page_label.setText("0 / 0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        visible = self.sheets.visible_indices()
        first = visible[0] + 1
        last = visible[-1] + 1
        if first == last:
            self.page_label.setText(f"{first} / {total}")
        else:
            self.page_label.setText(f"{first}–{last} / {total}")
        self.prev_btn.setEnabled(visible[0] > 0)
        self.next_btn.setEnabled(visible[-1] < total - 1)

    def _ensure_printer(self) -> bool:
        """Confirm a usable printer is selected; prompt if missing/offline."""
        available = {p.printerName() for p in QPrinterInfo.availablePrinters() if p.printerName()}
        name = (self._printer.printerName() or "").strip()
        if name and name in available:
            return True
        if not available:
            QMessageBox.warning(
                self,
                "没有可用打印机",
                "系统未检测到可用打印机。\n请先安装打印机或选择「打印到 PDF」。",
            )
            return False
        dlg = QPrintDialog(self._printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return False
        name = (self._printer.printerName() or "").strip()
        if not name or name not in available:
            QMessageBox.warning(
                self,
                "打印机无效",
                "所选打印机不可用或已离线，请重新选择。",
            )
            return False
        return True

    def _ensure_pdf_path(self, printer: QPrinter) -> bool:
        if printer.outputFormat() != QPrinter.OutputFormat.PdfFormat:
            return True
        existing = (printer.outputFileName() or "").strip()
        if existing:
            return True
        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存 PDF",
            str(Path.cwd() / "桌牌.pdf"),
            "PDF 文件 (*.pdf)",
        )
        if not path:
            return False
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        printer.setOutputFileName(path)
        return True

    def _make_print_printer(self) -> QPrinter:
        """High-res printer for final output; preview keeps ScreenResolution."""
        out = QPrinter(QPrinter.PrinterMode.HighResolution)
        name = (self._printer.printerName() or "").strip()
        if name:
            out.setPrinterName(name)
        out.setPageSize(self._printer.pageLayout().pageSize())
        out.setPageOrientation(self._printer.pageLayout().orientation())
        out.setFullPage(True)
        if self._printer.outputFormat() == QPrinter.OutputFormat.PdfFormat:
            out.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            out.setOutputFileName(self._printer.outputFileName())
        return out

    def _print(self) -> None:
        """Print to the printer already chosen on the main window — no second dialog unless needed."""
        if self._printing:
            return
        if not self._ensure_printer():
            return
        self._sync_printer_page()
        print_printer = self._make_print_printer()
        if not self._ensure_pdf_path(print_printer):
            return

        self._printing = True
        self.print_btn.setEnabled(False)
        try:
            self._paint_callback(print_printer)
        except Exception as exc:  # noqa: BLE001
            _log.exception("print failed")
            QMessageBox.warning(
                self,
                "打印失败",
                f"无法完成打印（打印机离线或驱动拒绝）：\n{exc}",
            )
        finally:
            self._printing = False
            self.print_btn.setEnabled(True)
