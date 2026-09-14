"""Resolve project / resource paths and themed stylesheet."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    """Source-tree root (meeting-nameplate)."""
    return Path(__file__).resolve().parents[1]


def resource_dir() -> Path:
    """Read-only resources: styles, icons, install.mark."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return project_root() / "resources"


def app_dir() -> Path:
    """Program directory: next to the EXE, or project root when running from source."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return project_root()


def data_dir() -> Path:
    """Writable config directory: APPDATA when installed, project root in source runs."""
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", str(Path.home())))
        else:
            base = Path.home()
        path = base / "meeting_nameplate"
        path.mkdir(parents=True, exist_ok=True)
        return path
    return project_root()


def resource_path(*parts: str) -> Path:
    return resource_dir().joinpath(*parts)


def app_icon_path() -> Path:
    """Window / taskbar icon lives under resources/ (and next to the EXE when frozen)."""
    for path in (resource_dir() / "icon.ico", app_dir() / "icon.ico"):
        if path.is_file():
            return path
    return resource_dir() / "icon.ico"


def style_sheet_path() -> Path:
    return resource_path("styles", "app.qss")


def load_app_stylesheet() -> str:
    """Load QSS and inject absolute icon URLs (Qt needs real file paths)."""
    path = style_sheet_path()
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    for key, name in (
        ("{{ARROW_DOWN}}", "arrow-down-light.svg"),
        ("{{ARROW_UP}}", "arrow-up-light.svg"),
        ("{{ARROW_DOWN_SPIN}}", "arrow-down-spin-light.svg"),
        ("{{CHECK_WHITE}}", "check-white.svg"),
    ):
        icon = resource_path("icons", name)
        if icon.exists():
            url = icon.resolve().as_posix()
            text = text.replace(key, f'"{url}"')
    return text
