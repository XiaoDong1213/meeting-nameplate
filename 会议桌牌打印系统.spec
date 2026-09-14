# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — 会议桌牌打印系统."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path(SPECPATH).resolve()
resources = project_root / "resources"

APP_NAME = "会议桌牌打印系统"

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(resources / "icon.ico"), "."),
        (str(resources / "install.mark"), "."),
        (str(resources / "styles"), "styles"),
        (str(resources / "icons"), "icons"),
        (str(resources / "translations"), "translations"),
    ],
    hiddenimports=[
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtPrintSupport",
        *collect_submodules("app"),
        *collect_submodules("core"),
        *collect_submodules("render"),
        *collect_submodules("ui"),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(resources / "icon.ico"),
    version=str(Path(SPECPATH) / "file_version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
