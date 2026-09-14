"""Binary-search font size to fit a rectangle (port of FontHandle)."""

from __future__ import annotations

from PyQt6.QtGui import QFont, QFontMetricsF, QGuiApplication, QPaintDevice

from core.text import new_line

MAX_FONT = 300
MIN_FONT = 5.0
PRECISION = 0.5
# Slight inset so bold CJK strokes are not clipped.
SAFETY = 0.99


def _reference_dpi() -> float:
    """DPI used by QFontMetricsF when no paint device is bound."""
    app = QGuiApplication.instance()
    if app is not None:
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            dpi = float(screen.logicalDotsPerInch())
            if dpi > 0:
                return dpi
    return 96.0


def _measure(
    text: str,
    font: QFont,
    *,
    paint_device: QPaintDevice | None = None,
    dpi: float | None = None,
) -> tuple[float, float]:
    """Return text width/height in the same pixel space as the target rect."""
    if paint_device is not None:
        metrics = QFontMetricsF(font, paint_device)
        scale = 1.0
    else:
        metrics = QFontMetricsF(font)
        target = dpi if dpi and dpi > 0 else _reference_dpi()
        scale = target / _reference_dpi()

    lines = text.split("\n") if text else [""]
    width = max((metrics.horizontalAdvance(line) for line in lines), default=0.0)
    if len(lines) <= 1:
        height = float(metrics.ascent() + metrics.descent())
    else:
        height = float(metrics.ascent() + metrics.descent()) + float(metrics.leading()) * max(len(lines) - 1, 0)
        if height < float(metrics.lineSpacing()) * len(lines) * 0.85:
            height = float(metrics.lineSpacing()) * len(lines)
    return width * scale, height * scale


def fit_font(
    text: str,
    base_font: QFont,
    max_width: float,
    max_height: float,
    *,
    paint_device: QPaintDevice | None = None,
    dpi: float | None = None,
) -> QFont:
    """Return largest font (binary search) that fits within max_width/max_height."""
    family = base_font.family()
    style = base_font.style()
    weight = base_font.weight()
    italic = base_font.italic()
    underline = base_font.underline()

    limit_w = max(1.0, max_width * SAFETY)
    limit_h = max(1.0, max_height * SAFETY)

    lo = MIN_FONT
    hi = min(float(base_font.pointSizeF() or MAX_FONT), float(MAX_FONT))
    best = QFont(family)
    best.setPointSizeF(MIN_FONT)
    best.setWeight(weight)
    best.setItalic(italic)
    best.setUnderline(underline)
    best.setStyle(style)

    while hi - lo > PRECISION:
        mid = (lo + hi) / 2.0
        test = QFont(family)
        test.setPointSizeF(mid)
        test.setWeight(weight)
        test.setItalic(italic)
        test.setUnderline(underline)
        test.setStyle(style)
        w, h = _measure(text, test, paint_device=paint_device, dpi=dpi)
        if w <= limit_w and h <= limit_h:
            best = test
            lo = mid
        else:
            hi = mid
    return best


def fit_font_for_lines(
    lines: list[str],
    base_font: QFont,
    pixel_width: float,
    pixel_height: float,
    margin_ratio: float,
    *,
    paint_device: QPaintDevice | None = None,
    dpi: float | None = None,
) -> QFont:
    """Choose a uniform font size across lines (auto / maximize)."""
    if not lines:
        return base_font

    effective_w = pixel_width * (1.0 - margin_ratio)
    effective_h = pixel_height * (1.0 - margin_ratio)

    max_w_text = ""
    max_h_text = ""
    max_w = 0.0
    max_h = 0.0
    probe = QFont(base_font)
    probe.setPointSizeF(MAX_FONT)

    for line in lines:
        text = new_line(line)
        w, h = _measure(text, probe, paint_device=paint_device, dpi=dpi)
        if w > max_w:
            max_w = w
            max_w_text = text
        if h > max_h:
            max_h = h
            max_h_text = text

    seed = QFont(base_font)
    seed.setPointSizeF(MAX_FONT)
    font_w = fit_font(
        max_w_text, seed, effective_w, effective_h, paint_device=paint_device, dpi=dpi
    )
    font_h = fit_font(
        max_h_text, seed, effective_w, effective_h, paint_device=paint_device, dpi=dpi
    )
    if font_w.pointSizeF() <= font_h.pointSizeF():
        return font_w
    return font_h


def fit_font_in_rect(
    text: str,
    base_font: QFont,
    width: float,
    height: float,
    margin_ratio: float,
    *,
    paint_device: QPaintDevice | None = None,
    dpi: float | None = None,
) -> QFont:
    text = new_line(text or "")
    effective_w = width * (1.0 - margin_ratio)
    effective_h = height * (1.0 - margin_ratio)
    return fit_font(
        text,
        base_font,
        effective_w,
        effective_h,
        paint_device=paint_device,
        dpi=dpi,
    )
