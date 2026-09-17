"""Print configuration and JSON persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.colors import WHITE_ARGB
from core.enums import DashStyle, FontStyle
from core.pages import PAGE_ORIENT_KEY_SET, PAGE_SIZE_NAME_SET
from core.paths import data_dir
from core.specs import DEFAULT_SIZE_LIST, Setup, merge_size_list
from core.text import build_content_list

DEFAULT_CONFIG_NAME = "config.json"


@dataclass
class PrintConfig:
    font_name: str = "楷体"
    font_style: FontStyle = FontStyle.REGULAR
    font_size_text: str = "自动适应"
    font_em_size: float = 48.0
    argb: int = 0xFF000000
    bg_argb: int = WHITE_ARGB
    image_file: Optional[str] = None
    size_text: str = "200*100mm"
    size_list: list[str] = field(default_factory=lambda: list(DEFAULT_SIZE_LIST))
    lines: list[str] = field(default_factory=list)
    printer_name: str = ""
    line_style: DashStyle = DashStyle.SOLID
    insert_blank: bool = True
    border_alpha: int = 75
    border_top: bool = True
    border_bottom: bool = True
    border_left: bool = True
    border_right: bool = True
    border_fold: bool = True  # 对折内折线
    # Positive = inset (inward); negative = outset (outward). Unit: mm.
    border_inset_top_mm: int = 0
    border_inset_bottom_mm: int = 0
    border_inset_left_mm: int = 0
    border_inset_right_mm: int = 0
    page_size: str = "A4"  # A4 / A5 / A3 / Letter
    page_orientation: str = "auto"  # auto / portrait / landscape
    setups: dict[str, Setup] = field(default_factory=dict)

    @classmethod
    def default(cls) -> PrintConfig:
        return cls()

    @property
    def content_list(self) -> list[str]:
        return build_content_list(self.lines)

    @property
    def current_setup(self) -> Optional[Setup]:
        if self.size_text in self.setups:
            setup = self.setups[self.size_text]
            if setup.text == self.size_text:
                return setup
        parsed = Setup.parse(self.size_text)
        if parsed is None:
            return None
        # Preserve advanced settings if previously stored under same text
        stored = self.setups.get(self.size_text)
        if stored is not None:
            parsed.margin_ratio = stored.margin_ratio
            parsed.offset_x_mm = stored.offset_x_mm
            parsed.offset_y_mm = stored.offset_y_mm
            parsed.title1 = stored.title1
            parsed.title2 = stored.title2
            parsed.mirror = stored.mirror
            parsed.card_landscape = stored.card_landscape
        self.setups[self.size_text] = parsed
        if self.size_text not in self.size_list:
            self.size_list.append(self.size_text)
        return parsed

    def remember_setup(self, setup: Setup) -> None:
        self.setups[setup.text] = setup
        self.size_text = setup.text
        if setup.text not in self.size_list:
            self.size_list.append(setup.text)

    def to_dict(self) -> dict:
        return {
            "font_name": self.font_name,
            "font_style": self.font_style.value,
            "font_size_text": self.font_size_text,
            "font_em_size": self.font_em_size,
            "argb": self.argb,
            "bg_argb": self.bg_argb,
            "image_file": self.image_file,
            "size_text": self.size_text,
            "size_list": list(self.size_list),
            "lines": list(self.lines),
            "printer_name": self.printer_name,
            "line_style": self.line_style.value,
            "insert_blank": self.insert_blank,
            "border_alpha": self.border_alpha,
            "border_top": self.border_top,
            "border_bottom": self.border_bottom,
            "border_left": self.border_left,
            "border_right": self.border_right,
            "border_fold": self.border_fold,
            "border_inset_top_mm": self.border_inset_top_mm,
            "border_inset_bottom_mm": self.border_inset_bottom_mm,
            "border_inset_left_mm": self.border_inset_left_mm,
            "border_inset_right_mm": self.border_inset_right_mm,
            "page_size": self.page_size,
            "page_orientation": self.page_orientation,
            "setups": {k: v.to_dict() for k, v in self.setups.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> PrintConfig:
        cfg = cls.default()
        if not data:
            return cfg
        cfg.font_name = str(data.get("font_name", cfg.font_name))
        try:
            cfg.font_style = FontStyle(data.get("font_style", FontStyle.REGULAR.value))
        except ValueError:
            cfg.font_style = FontStyle.REGULAR
        cfg.font_size_text = str(data.get("font_size_text", cfg.font_size_text))
        # Migrate legacy size labels
        if cfg.font_size_text == "自动":
            cfg.font_size_text = "自动适应"
        elif cfg.font_size_text == "最大化":
            cfg.font_size_text = "每牌尽量大"
        try:
            cfg.font_em_size = float(data.get("font_em_size", cfg.font_em_size))
        except (TypeError, ValueError):
            cfg.font_em_size = 48.0
        if cfg.font_em_size <= 0:
            cfg.font_em_size = 48.0
        try:
            cfg.argb = int(data.get("argb", cfg.argb))
        except (TypeError, ValueError):
            cfg.argb = 0xFF000000
        try:
            cfg.bg_argb = int(data.get("bg_argb", WHITE_ARGB))
        except (TypeError, ValueError):
            cfg.bg_argb = WHITE_ARGB
        image = data.get("image_file")
        cfg.image_file = str(image) if image else None
        cfg.size_text = str(data.get("size_text", cfg.size_text))
        size_list = data.get("size_list")
        if isinstance(size_list, list) and size_list:
            cfg.size_list = merge_size_list([str(x) for x in size_list])
        else:
            cfg.size_list = list(DEFAULT_SIZE_LIST)
        lines = data.get("lines")
        if isinstance(lines, list):
            cfg.lines = [str(x) for x in lines]
        cfg.printer_name = str(data.get("printer_name", ""))
        try:
            cfg.line_style = DashStyle(data.get("line_style", DashStyle.SOLID.value))
        except ValueError:
            cfg.line_style = DashStyle.SOLID
        cfg.insert_blank = bool(data.get("insert_blank", True))
        try:
            alpha = int(data.get("border_alpha", 75))
        except (TypeError, ValueError):
            alpha = 75
        cfg.border_alpha = max(0, min(255, alpha))
        cfg.border_top = bool(data.get("border_top", True))
        cfg.border_bottom = bool(data.get("border_bottom", True))
        cfg.border_left = bool(data.get("border_left", True))
        cfg.border_right = bool(data.get("border_right", True))
        cfg.border_fold = bool(data.get("border_fold", True))

        def _inset(key: str) -> int:
            try:
                return int(data.get(key, 0))
            except (TypeError, ValueError):
                return 0

        cfg.border_inset_top_mm = _inset("border_inset_top_mm")
        cfg.border_inset_bottom_mm = _inset("border_inset_bottom_mm")
        cfg.border_inset_left_mm = _inset("border_inset_left_mm")
        cfg.border_inset_right_mm = _inset("border_inset_right_mm")
        page_size = str(data.get("page_size", "A4"))
        cfg.page_size = page_size if page_size in PAGE_SIZE_NAME_SET else "A4"
        orient = str(data.get("page_orientation", "auto")).lower()
        cfg.page_orientation = orient if orient in PAGE_ORIENT_KEY_SET else "auto"
        setups = data.get("setups") or {}
        if isinstance(setups, dict):
            cfg.setups = {k: Setup.from_dict(v) for k, v in setups.items() if isinstance(v, dict)}
        return cfg


@dataclass(frozen=True)
class ConfigLoadResult:
    config: PrintConfig
    warning: str | None = None


def default_config_path() -> Path:
    return data_dir() / DEFAULT_CONFIG_NAME


def load_config(path: Path | None = None) -> ConfigLoadResult:
    """Load config; on missing/corrupt file return defaults + optional warning."""
    cfg_path = path or default_config_path()
    if not cfg_path.exists():
        return ConfigLoadResult(PrintConfig.default())
    try:
        raw = cfg_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return ConfigLoadResult(
                PrintConfig.default(),
                f"配置文件格式无效（需要 JSON 对象），已使用默认设置：\n{cfg_path}",
            )
        return ConfigLoadResult(PrintConfig.from_dict(data))
    except json.JSONDecodeError as exc:
        return ConfigLoadResult(
            PrintConfig.default(),
            f"配置文件损坏或不是合法 JSON，已使用默认设置：\n{cfg_path}\n\n{exc}",
        )
    except (OSError, TypeError, ValueError) as exc:
        return ConfigLoadResult(
            PrintConfig.default(),
            f"无法读取配置文件，已使用默认设置：\n{cfg_path}\n\n{exc}",
        )


def save_config(config: PrintConfig, path: Path | None = None) -> None:
    cfg_path = path or default_config_path()
    cfg_path.write_text(
        json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
