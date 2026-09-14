"""Shared enums."""

from __future__ import annotations

from enum import Enum


class FontStyle(str, Enum):
    REGULAR = "常规"
    BOLD = "加粗"
    ITALIC = "倾斜"
    UNDERLINE = "下划线"


class DashStyle(str, Enum):
    SOLID = "实线"
    DASH = "虚线"
    DOT = "点"
    CORNER = "角"
    NONE = "无"
