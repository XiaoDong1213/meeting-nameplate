"""Application entrypoint."""

from __future__ import annotations

import logging
import os
import sys
import traceback
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox, QProxyStyle, QStyle

from app.i18n import install_qt_zh
from app.identity import APP_NAME, APP_USER_MODEL_ID
from core.paths import app_icon_path, load_app_stylesheet, project_root
from ui.main_window import MainWindow


class _NoPrimaryFrameStyle(QProxyStyle):
    """Fusion draws a dark default/focus frame; keep the primary button borderless."""

    def drawPrimitive(self, element, option, painter, widget=None):  # noqa: ANN001
        if widget is not None and widget.objectName() == "primaryButton":
            if element in (
                QStyle.PrimitiveElement.PE_FrameDefaultButton,
                QStyle.PrimitiveElement.PE_FrameFocusRect,
            ):
                return
        super().drawPrimitive(element, option, painter, widget)


def _set_windows_app_id() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:  # noqa: BLE001
        pass


def _crash_log_path() -> Path:
    return project_root() / "crash.log"


def _install_excepthook() -> None:
    """Log uncaught exceptions so UI paint/print failures leave a trail."""

    def hook(exc_type, exc, tb) -> None:
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        logging.error("Uncaught exception:\n%s", text)
        try:
            _crash_log_path().write_text(text, encoding="utf-8")
        except OSError:
            pass
        sys.__excepthook__(exc_type, exc, tb)
        app = QApplication.instance()
        if app is not None:
            try:
                QMessageBox.critical(
                    None,
                    "程序异常",
                    f"发生未处理错误，详情已写入 crash.log：\n{exc}",
                )
            except Exception:  # noqa: BLE001
                pass

    sys.excepthook = hook


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    _install_excepthook()
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setStyle(_NoPrimaryFrameStyle("Fusion"))
    install_qt_zh(app)
    app.setStyleSheet(load_app_stylesheet())
    icon_file = app_icon_path()
    if icon_file.is_file():
        app.setWindowIcon(QIcon(str(icon_file)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
