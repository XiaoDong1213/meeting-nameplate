"""Minimal unit tests for core logic (no UI)."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.config import PrintConfig, load_config, save_config
from core.layout import calculate_layout, centered_rect, prefer_landscape
from core.specs import Setup, default_title_xy
from core.text import IDEOGRAPHIC_SPACE, build_content_list, insert_ideographic_spaces


class TestSetupParse:
    def test_valid_star(self):
        s = Setup.parse("200*100mm")
        assert s is not None
        assert s.width_mm == 200
        assert s.height_mm == 100
        assert s.mirror is True

    def test_legacy_suffix_ignored(self):
        s = Setup.parse("210*105mm-L")
        assert s is not None
        assert s.landscape is None
        assert s.mirror is True

    def test_out_of_range(self):
        assert Setup.parse("10*10mm") is None
        assert Setup.parse("400*100mm") is None

    def test_invalid(self):
        assert Setup.parse("abc") is None
        assert Setup.parse("") is None


class TestDefaultTitleXY:
    def test_header_common_sizes(self):
        assert default_title_xy(90, 55, True) == (6, 5)
        assert default_title_xy(220, 110, True) == (10, 6)
        assert default_title_xy(210, 70, True) == (10, 5)
        assert default_title_xy(148, 210, True) == (7, 8)

    def test_footer_bottom_right(self):
        assert default_title_xy(90, 55, False) == (48, 44)
        assert default_title_xy(220, 110, False) == (122, 98)
        x, y = default_title_xy(210, 70, False)
        assert x > 100
        assert y >= 50


class TestIdeographicSpaces:
    def test_two_char_name(self):
        text, n = insert_ideographic_spaces("嫦娥\n猪八戒")
        assert n == 1
        assert text.splitlines()[0] == f"嫦{IDEOGRAPHIC_SPACE}娥"
        assert "猪八戒" in text

    def test_already_spaced(self):
        src = f"嫦{IDEOGRAPHIC_SPACE}娥"
        text, n = insert_ideographic_spaces(src)
        assert n == 0
        assert text == src

    def test_tab_first_column_only(self):
        text, n = insert_ideographic_spaces("张三\t单位A")
        assert n == 1
        assert text.startswith(f"张{IDEOGRAPHIC_SPACE}三\t")


class TestBuildContentList:
    def test_skips_blank(self):
        assert build_content_list(["a", "  ", "", "b"]) == ["a", "b"]


class TestPagePacking:
    def test_small_cards_pack_several(self):
        setup = Setup.parse("90*55mm")
        assert setup is not None
        rects, _ = setup.get_rectangles(2100, 2970, dpi=10, lock_page=True)
        assert len(rects) > 1

    def test_overflow_keeps_full_size(self):
        rect = centered_rect(210, 297, 220, 220)
        assert rect.width == 220
        assert rect.height == 220
        assert rect.x < 0

    def test_landscape_when_it_overflows_less(self):
        assert prefer_landscape(210, 297, 297, 200) is True
        assert prefer_landscape(210, 297, 90, 110) is False


class TestCalculateLayout:
    def test_packs_at_least_one(self):
        rects, landscape = calculate_layout(2100, 2970, 800, 800, None)
        assert len(rects) >= 1
        assert isinstance(landscape, bool)

    def test_rejects_zero(self):
        with pytest.raises(ValueError):
            calculate_layout(100, 100, 0, 50, None)


class TestConfigRoundtrip:
    def test_save_load(self, tmp_path: Path):
        path = tmp_path / "config.json"
        cfg = PrintConfig.default()
        cfg.font_name = "黑体"
        cfg.lines = ["甲", "乙"]
        cfg.border_alpha = 120
        save_config(cfg, path)
        loaded = load_config(path)
        assert loaded.warning is None
        assert loaded.config.font_name == "黑体"
        assert loaded.config.lines == ["甲", "乙"]
        assert loaded.config.border_alpha == 120
        assert loaded.config.bg_argb == 0xFFFFFFFF

    def test_bg_argb_roundtrip(self, tmp_path: Path):
        path = tmp_path / "config.json"
        cfg = PrintConfig.default()
        cfg.bg_argb = 0xFF0070C0
        save_config(cfg, path)
        loaded = load_config(path)
        assert loaded.warning is None
        assert loaded.config.bg_argb == 0xFF0070C0

    def test_bad_json_falls_back(self, tmp_path: Path):
        path = tmp_path / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        loaded = load_config(path)
        assert loaded.warning is not None
        assert loaded.config.font_name == PrintConfig.default().font_name

    def test_clamps_alpha(self):
        cfg = PrintConfig.from_dict({"border_alpha": 999})
        assert cfg.border_alpha == 255
        cfg2 = PrintConfig.from_dict({"border_alpha": -3})
        assert cfg2.border_alpha == 0

    def test_migrates_font_size_labels(self):
        cfg = PrintConfig.from_dict({"font_size_text": "自动"})
        assert cfg.font_size_text == "自动适应"
        cfg2 = PrintConfig.from_dict({"font_size_text": "最大化"})
        assert cfg2.font_size_text == "每牌尽量大"


@pytest.fixture(scope="module")
def qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestResolveFontSize:
    def test_modes(self, qapp):
        from core.config import PrintConfig
        from render.document import resolve_font_size
        from render.fonts import MAX_FONT

        setup = Setup.parse("200*100mm")
        assert setup is not None
        cfg = PrintConfig.default()
        lines = ["张三", "李四"]

        cfg.font_size_text = "每牌尽量大"
        assert resolve_font_size(cfg, setup, lines) == float(MAX_FONT)

        cfg.font_size_text = "24"
        assert resolve_font_size(cfg, setup, lines) == 24.0

        cfg.font_size_text = "自动适应"
        size = resolve_font_size(cfg, setup, lines)
        assert 1.0 <= size <= float(MAX_FONT)


class TestRenderSheets:
    def test_small_cards_share_a_sheet(self, qapp):
        from render.document import render_sheets

        cfg = PrintConfig.default()
        cfg.size_text = "90*55mm"
        cfg.lines = ["甲", "乙", "丙"]
        images = render_sheets(cfg)
        assert len(images) == 1
        assert images[0].width() > 0
