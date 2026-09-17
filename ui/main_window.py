"""Main window — assemble panels and bind config."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.identity import APP_NAME
from core.colors import WHITE_ARGB, argb_to_qcolor, qcolor_to_argb
from core.config import load_config, save_config
from core.enums import DashStyle, FontStyle
from core.paths import app_icon_path
from core.specs import Setup
from core.text import insert_ideographic_spaces
from render.document import NameplateDocument, paint_to_printer, resolve_font_size
from render.paint import font_from_style
from ui.font_list import chinese_fonts
from ui.output_bar import OutputBar
from ui.preview.preview_dialog import PreviewDialog
from ui.preview_pane import PreviewPane
from ui.roster_panel import EDITOR_DEFAULT_PT, RosterPanel
from ui.settings_bar import SettingsBar
from ui.title_row import TitleRow
from ui.widgets import fit_combo_width, pick_color, section_label


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        icon_file = app_icon_path()
        if icon_file.is_file():
            self.setWindowIcon(QIcon(str(icon_file)))
        self.resize(1180, 740)
        self.setMinimumSize(1040, 660)
        loaded = load_config()
        self.config = loaded.config
        self._text_argb = self.config.argb
        self._title_header: TitleRow | None = None
        self._title_footer: TitleRow | None = None
        self._preview_index = 0
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(120)
        self._preview_timer.timeout.connect(self._refresh_live_preview)
        self._build_ui()
        self._bind_config()
        QShortcut(QKeySequence("F8"), self, activated=self._preview)
        self._refresh_live_preview()
        if loaded.warning:
            QMessageBox.warning(self, "配置已重置", loaded.warning)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("appHeader")
        top = QHBoxLayout(header)
        top.setContentsMargins(20, 12, 20, 12)
        top.setSpacing(12)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        title = QLabel(APP_NAME)
        title.setObjectName("appTitle")
        subtitle = QLabel("排版 · 预览 · 打印")
        subtitle.setObjectName("appSubtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        top.addLayout(brand)
        top.addStretch(1)
        self.preview_btn = QPushButton("排版预览并打印  F8")
        self.preview_btn.setObjectName("primaryButton")
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.setMinimumHeight(36)
        self.preview_btn.setAutoDefault(False)
        self.preview_btn.setDefault(False)
        top.addWidget(self.preview_btn)
        root.addWidget(header)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 12, 16, 8)
        body_lay.setSpacing(10)

        self.settings = SettingsBar()
        body_lay.addWidget(self.settings)
        body_lay.addWidget(section_label("题款（抬头 / 落款）"))
        self._title_host = QVBoxLayout()
        self._title_host.setSpacing(4)
        body_lay.addLayout(self._title_host)

        mid = QHBoxLayout()
        mid.setSpacing(0)
        work = QFrame()
        work.setObjectName("workSurface")
        work_lay = QHBoxLayout(work)
        work_lay.setContentsMargins(0, 4, 0, 4)
        work_lay.setSpacing(16)
        self.roster = RosterPanel()
        self.preview_pane = PreviewPane()
        work_lay.addWidget(self.roster, 1)
        work_lay.addWidget(self.preview_pane, 1)
        mid.addWidget(work)
        body_lay.addLayout(mid, 1)
        root.addWidget(body, 1)

        output_wrap = QFrame()
        output_wrap.setObjectName("outputBar")
        out_lay = QHBoxLayout(output_wrap)
        out_lay.setContentsMargins(16, 8, 16, 8)
        self.output = OutputBar()
        out_lay.addWidget(self.output)
        root.addWidget(output_wrap)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("就绪 · 编辑名单后按 F8 预览打印")
        status.addWidget(self.status_label, 1)

        self.preview_btn.clicked.connect(self._preview)
        self.settings.changed.connect(self._schedule_live_preview)
        self.settings.font_combo.currentTextChanged.connect(self._update_editor_font)
        self.settings.style_combo.currentTextChanged.connect(self._update_editor_font)
        self.settings.spec_changed.connect(self._on_spec_changed)
        self.settings.mirror_combo.currentTextChanged.connect(self._on_mirror_mode_changed)
        self.settings.orient_combo.currentTextChanged.connect(self._on_card_orient_changed)
        self.settings.color_clicked.connect(self._pick_color)
        self.settings.bg_picked.connect(self._on_bg_picked)
        self.settings.bg_color_picked.connect(self._on_bg_color)
        self.settings.bg_cleared.connect(self._clear_bg)
        self.output.changed.connect(self._schedule_live_preview)
        self.output.alpha_changed.connect(lambda v: self.status_label.setText(f"线条浓度：{v}"))
        self.roster.text_changed.connect(self._on_text_changed)
        self.roster.insert_spaces_clicked.connect(self._insert_ideographic_space)
        self.preview_pane.prev_clicked.connect(self._preview_prev)
        self.preview_pane.next_clicked.connect(self._preview_next)

    @property
    def editor(self):
        return self.roster.editor

    def _clear_titles(self) -> None:
        while self._title_host.count():
            item = self._title_host.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._title_header = None
        self._title_footer = None

    def _rebuild_titles(self, setup: Setup) -> None:
        self._clear_titles()
        fonts = chinese_fonts() or ["黑体", "楷体", "宋体"]
        styles = [s.value for s in FontStyle]
        self._title_header = TitleRow(
            "抬头", "例如：工作会议", setup.title1, fonts, styles, True, setup.face_width_mm(), setup.face_height_mm()
        )
        self._title_footer = TitleRow(
            "落款", "例如：主办单位", setup.title2, fonts, styles, False, setup.face_width_mm(), setup.face_height_mm()
        )
        self._title_host.addWidget(self._title_header)
        self._title_host.addWidget(self._title_footer)
        self._title_header.changed.connect(self._schedule_live_preview)
        self._title_footer.changed.connect(self._schedule_live_preview)

    def _bind_config(self) -> None:
        cfg = self.config
        s = self.settings
        o = self.output
        fonts = [s.font_combo.itemText(i) for i in range(s.font_combo.count())]
        if cfg.font_name in fonts:
            s.font_combo.setCurrentText(cfg.font_name)
        else:
            s.font_combo.setCurrentIndex(0)
        s.style_combo.setCurrentText(cfg.font_style.value)
        s.size_combo.setCurrentText(cfg.font_size_text)
        s.spec_combo.addItems(cfg.size_list)
        s.spec_combo.setCurrentText(cfg.size_text)
        fit_combo_width(s.spec_combo, floor=168, ceiling=220)

        printers = [o.printer_combo.itemText(i) for i in range(o.printer_combo.count())]
        if cfg.printer_name and cfg.printer_name in printers:
            o.printer_combo.setCurrentText(cfg.printer_name)
        o.line_combo.setCurrentText(cfg.line_style.value)
        o.border_top.setChecked(cfg.border_top)
        o.border_bottom.setChecked(cfg.border_bottom)
        o.border_left.setChecked(cfg.border_left)
        o.border_right.setChecked(cfg.border_right)
        o.border_fold.setChecked(cfg.border_fold)
        o.set_border_insets_mm(
            cfg.border_inset_top_mm,
            cfg.border_inset_bottom_mm,
            cfg.border_inset_left_mm,
            cfg.border_inset_right_mm,
        )
        o.distribute.setChecked(cfg.insert_blank)
        o.alpha_slider.setValue(cfg.border_alpha)
        s.set_bg_hint(bool(cfg.image_file), cfg.bg_argb)

        setup = cfg.current_setup or Setup.parse(cfg.size_text) or Setup()
        s.set_mirror_enabled(setup.mirror)
        s.set_card_landscape(setup.card_landscape)
        o.set_fold_line_enabled(setup.mirror)
        if setup.mirror:
            o.border_fold.setChecked(cfg.border_fold)
        s.set_offset_limits(setup.face_width_mm(), setup.face_height_mm())
        s.margin_spin.setValue(setup.margin_ratio)
        s.offset_x.setValue(setup.offset_x_mm)
        s.offset_y.setValue(setup.offset_y_mm)
        self._rebuild_titles(setup)

        self.editor.setPlainText("\n".join(cfg.lines))
        self._text_argb = cfg.argb
        self.editor.setTextColor(argb_to_qcolor(cfg.argb))
        self._update_editor_font()

    def _on_spec_changed(self, *_args) -> None:
        text = self.settings.spec_combo.currentText().strip()
        setup = Setup.parse(text)
        if setup is None:
            return
        stored = self.config.setups.get(setup.text)
        if stored is not None and stored.text == setup.text:
            setup.mirror = stored.mirror
            setup.card_landscape = stored.card_landscape
            setup.margin_ratio = stored.margin_ratio
            setup.offset_x_mm = stored.offset_x_mm
            setup.offset_y_mm = stored.offset_y_mm
            setup.title1 = stored.title1
            setup.title2 = stored.title2
        self.settings.set_mirror_enabled(setup.mirror)
        self.settings.set_card_landscape(setup.card_landscape)
        self.output.set_fold_line_enabled(setup.mirror)
        if setup.mirror and self.config.border_fold:
            self.output.border_fold.setChecked(True)
        fw, fh = setup.face_width_mm(), setup.face_height_mm()
        self.settings.set_offset_limits(fw, fh)
        if self._title_header and self._title_footer:
            self._title_header.set_limits(fw, fh, True, setup.title1)
            self._title_footer.set_limits(fw, fh, False, setup.title2)
        # Keep combo text canonical (e.g. a4 → A4).
        if self.settings.spec_combo.currentText().strip() != setup.text:
            self.settings.spec_combo.blockSignals(True)
            self.settings.spec_combo.setCurrentText(setup.text)
            self.settings.spec_combo.blockSignals(False)

    def _on_mirror_mode_changed(self, *_args) -> None:
        mirror = self.settings.mirror_enabled()
        self.output.set_fold_line_enabled(mirror)
        if mirror and self.config.border_fold:
            self.output.border_fold.setChecked(True)

    def _on_card_orient_changed(self, *_args) -> None:
        setup = Setup.parse(self.settings.spec_combo.currentText().strip())
        if setup is None:
            return
        setup.card_landscape = self.settings.card_landscape()
        fw, fh = setup.face_width_mm(), setup.face_height_mm()
        self.settings.set_offset_limits(fw, fh)
        if self._title_header and self._title_footer:
            self._title_header.set_limits(fw, fh, True)
            self._title_footer.set_limits(fw, fh, False)

    def _apply_layout_to_setup(self, setup: Setup) -> None:
        s = self.settings
        setup.margin_ratio = float(s.margin_spin.value())
        setup.offset_x_mm = int(s.offset_x.value())
        setup.offset_y_mm = int(s.offset_y.value())
        setup.mirror = s.mirror_enabled()
        setup.card_landscape = s.card_landscape()
        if self._title_header:
            setup.title1 = self._title_header.to_title()
        if self._title_footer:
            setup.title2 = self._title_footer.to_title()

    def _sync_from_ui(self) -> None:
        cfg = self.config
        s = self.settings
        o = self.output
        cfg.font_name = s.font_combo.currentText()
        try:
            cfg.font_style = FontStyle(s.style_combo.currentText())
        except ValueError:
            cfg.font_style = FontStyle.REGULAR
        cfg.font_size_text = s.size_combo.currentText()
        cfg.size_text = s.spec_combo.currentText().strip()
        cfg.lines = self.editor.toPlainText().splitlines()
        cfg.printer_name = o.printer_combo.currentText()
        try:
            cfg.line_style = DashStyle(o.line_combo.currentText())
        except ValueError:
            cfg.line_style = DashStyle.SOLID
        cfg.insert_blank = o.distribute.isChecked()
        cfg.border_alpha = o.alpha_slider.value()
        cfg.border_top = o.border_top.isChecked()
        cfg.border_bottom = o.border_bottom.isChecked()
        cfg.border_left = o.border_left.isChecked()
        cfg.border_right = o.border_right.isChecked()
        cfg.border_fold = o.border_fold.isChecked()
        top_i, bottom_i, left_i, right_i = o.border_insets_mm()
        cfg.border_inset_top_mm = top_i
        cfg.border_inset_bottom_mm = bottom_i
        cfg.border_inset_left_mm = left_i
        cfg.border_inset_right_mm = right_i
        cfg.argb = self._text_argb

    def _update_editor_font(self, *_args) -> None:
        try:
            style = FontStyle(self.settings.style_combo.currentText())
        except ValueError:
            style = FontStyle.REGULAR
        size = self.editor.font().pointSizeF() or EDITOR_DEFAULT_PT
        if size < 12:
            size = EDITOR_DEFAULT_PT
        self.editor.setFont(font_from_style(self.settings.font_combo.currentText(), size, style))

    def _insert_ideographic_space(self) -> None:
        text = self.editor.toPlainText()
        new_text, changed = insert_ideographic_spaces(text)
        if new_text != text:
            self.editor.setPlainText(new_text)
            self._schedule_live_preview()
        self.status_label.setText(
            f"已为 {changed} 个两字名插入全角空格" if changed else "没有需要插入的两字名"
        )

    def _preview_prev(self) -> None:
        if self._preview_index > 0:
            self._preview_index -= 1
            self._refresh_live_preview()

    def _preview_next(self) -> None:
        lines = self.roster.preview_lines()
        if self._preview_index < max(0, len(lines) - 1):
            self._preview_index += 1
            self._refresh_live_preview()

    def _schedule_live_preview(self, *_args) -> None:
        self._preview_timer.start()

    def _refresh_live_preview(self) -> None:
        try:
            self._sync_from_ui()
            setup = self.config.current_setup
            if setup is None:
                setup = Setup()
            else:
                self._apply_layout_to_setup(setup)
            lines = self.roster.preview_lines()
            total = max(1, len(lines))
            if self._preview_index >= total:
                self._preview_index = total - 1
            if self._preview_index < 0:
                self._preview_index = 0
            text = lines[self._preview_index] if lines else "预览"
            self.config.font_em_size = resolve_font_size(
                self.config, setup, lines or [text], dpi=96.0
            )
            self.preview_pane.live_preview.set_snapshot(self.config, setup, text)
            current = self._preview_index + 1 if lines else 0
            self.preview_pane.set_page(current, len(lines), bool(lines))
        except Exception as exc:  # noqa: BLE001
            self.status_label.setText(f"预览刷新失败：{exc}")

    def _on_text_changed(self) -> None:
        self.status_label.setText(f"共 {len(self.editor.toPlainText().splitlines())} 行")
        self._schedule_live_preview()

    def _pick_color(self) -> None:
        current = argb_to_qcolor(self._text_argb)
        color = pick_color(self, current, "正文字色")
        if color.isValid():
            self._text_argb = qcolor_to_argb(color)
            self.config.argb = self._text_argb
            cursor = self.editor.textCursor()
            self.editor.selectAll()
            self.editor.setTextColor(color)
            self.editor.setTextCursor(cursor)
            self._refresh_live_preview()

    def _on_bg_picked(self, path: str) -> None:
        self.config.image_file = path
        self.settings.set_bg_hint(True, self.config.bg_argb)
        self._schedule_live_preview()
        self.status_label.setText(f"已设置背景图：{Path(path).name}")

    def _on_bg_color(self, argb: int) -> None:
        self.config.bg_argb = argb
        self.config.image_file = None
        self.settings.set_bg_hint(False, argb)
        self._schedule_live_preview()
        self.status_label.setText("已设置牌面纯色")

    def _clear_bg(self) -> None:
        self.config.image_file = None
        self.config.bg_argb = WHITE_ARGB
        self.settings.set_bg_hint(False, WHITE_ARGB)
        self._schedule_live_preview()
        self.status_label.setText("已恢复白底")

    def _ensure_setup(self):
        self._sync_from_ui()
        setup = self.config.current_setup
        if setup is None:
            QMessageBox.warning(
                self,
                "桌牌规格无效",
                "请填写有效的桌牌规格。\n"
                "可用 A4 / A5 / A3 / A6 / B5 / Letter，或毫米格式如 220*110mm（约 20～500mm）",
            )
            return None
        self._apply_layout_to_setup(setup)
        return setup

    def _on_page_settings(self, size: str, orient: str) -> None:
        self.config.page_size = size
        self.config.page_orientation = orient

    def _preview(self) -> None:
        setup = self._ensure_setup()
        if setup is None:
            return
        contents = self.config.content_list
        if not contents:
            QMessageBox.information(self, "提示", "桌牌名单为空，请先填写内容")
            return

        font_size = resolve_font_size(self.config, setup, contents, dpi=96.0)
        self.config.font_em_size = font_size
        lengths = [len(x) for x in contents]
        if self.config.font_size_text in {"最大化", "每牌尽量大"}:
            self.status_label.setText(
                f"共 {len(contents)} 张牌，字数 {min(lengths)}-{max(lengths)}，字号：每牌尽量大"
            )
        else:
            self.status_label.setText(
                f"共 {len(contents)} 张牌，字数 {min(lengths)}-{max(lengths)}，字号：{int(font_size)}"
            )
        self.config.remember_setup(setup)
        save_config(self.config)

        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        if self.config.printer_name:
            printer.setPrinterName(self.config.printer_name)
        NameplateDocument(self.config).configure_printer(printer)

        dlg = PreviewDialog(
            printer,
            self.config,
            lambda p: paint_to_printer(p, self.config),
            page_size=self.config.page_size,
            page_orientation=self.config.page_orientation,
            on_page_settings=self._on_page_settings,
            parent=self,
        )
        dlg.exec()
        save_config(self.config)

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            font = self.editor.font()
            size = font.pointSizeF() + event.angleDelta().y() / 120
            if 12 <= size <= 48:
                font.setPointSizeF(size)
                self.editor.setFont(font)
                event.accept()
                return
        super().wheelEvent(event)

    def closeEvent(self, event) -> None:
        self._sync_from_ui()
        setup = self.config.current_setup
        if setup is not None:
            self._apply_layout_to_setup(setup)
            self.config.remember_setup(setup)
        save_config(self.config)
        super().closeEvent(event)
