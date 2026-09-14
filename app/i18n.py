"""Install Qt Chinese translations for built-in dialogs (color picker, buttons)."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator
from PyQt6.QtWidgets import QApplication

from core.paths import resource_dir

_STEMS = ("qtbase_zh_CN", "qt_zh_CN")


def _translation_dirs() -> list[Path]:
    dirs: list[Path] = [resource_dir() / "translations"]
    try:
        qt_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        if qt_dir:
            dirs.append(Path(qt_dir))
    except Exception:  # noqa: BLE001
        pass
    try:
        import PyQt6

        dirs.append(Path(PyQt6.__file__).resolve().parent / "Qt6" / "translations")
    except Exception:  # noqa: BLE001
        pass
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        dirs.append(Path(sys._MEIPASS) / "translations")
    seen: set[str] = set()
    unique: list[Path] = []
    for folder in dirs:
        key = str(folder.resolve()) if folder.exists() else str(folder)
        if key in seen:
            continue
        seen.add(key)
        unique.append(folder)
    return unique


def install_qt_zh(app: QApplication) -> None:
    locale = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
    QLocale.setDefault(locale)
    kept: list[QTranslator] = []
    loaded: set[str] = set()
    for folder in _translation_dirs():
        if not folder.is_dir():
            continue
        for stem in _STEMS:
            if stem in loaded:
                continue
            translator = QTranslator(app)
            path = folder / f"{stem}.qm"
            ok = translator.load(str(path) if path.is_file() else stem, str(folder))
            if ok:
                app.installTranslator(translator)
                kept.append(translator)
                loaded.add(stem)
    app.setProperty("_qt_translators", kept)
