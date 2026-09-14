"""Shared small UI helpers: combo popup + absolute slider."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QSize, QTimer, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QListView,
    QProxyStyle,
    QSlider,
    QStyledItemDelegate,
    QStyle,
    QStyleOptionViewItem,
    QWidget,
)

COMBO_MAX_VISIBLE = 8
_ROW_H = 34
_LIST_PAD = 8
_BOX_CHROME = 4

# Popup list only — scrollbar look comes from global app.qss
COMBO_POPUP_QSS = """
QListView#comboPopup {
    background: #FFFFFF;
    border: none;
    outline: 0;
    padding: 4px;
}
"""

CONTAINER_QSS = (
    "QFrame, QWidget {"
    "background-color: #FFFFFF;"
    "border: 1px solid #D4DEE8;"
    "border-radius: 2px;"
    "}"
)


class _AbsoluteSliderStyle(QProxyStyle):
    """Left-click on groove jumps handle to that position (not page-step)."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):  # noqa: N802
        if hint == QStyle.StyleHint.SH_Slider_AbsoluteSetButtons:
            return Qt.MouseButton.LeftButton.value
        return super().styleHint(hint, option, widget, returnData)


def tune_slider(slider: QSlider) -> None:
    """浓度等滑块：点到哪停到哪。"""
    slider.setStyle(_AbsoluteSliderStyle(slider.style()))
    slider.setCursor(Qt.CursorShape.PointingHandCursor)


class _PlainComboDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):  # noqa: N802
        size = super().sizeHint(option, index)
        return QSize(size.width(), _ROW_H)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # noqa: N802
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        rect = opt.rect.adjusted(2, 1, -2, -1)
        if selected:
            painter.fillRect(rect, QColor("#0070C0"))
            color = QColor("#FFFFFF")
        elif hovered:
            painter.fillRect(rect, QColor("#E8F1F8"))
            color = QColor("#1A2332")
        else:
            color = QColor("#1A2332")
        painter.setPen(color)
        painter.drawText(
            rect.adjusted(12, 0, -8, 0),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            opt.text,
        )
        painter.restore()


class _CappedListView(QListView):
    def __init__(self, combo: QComboBox, parent=None):
        super().__init__(parent)
        self._combo = combo

    def sizeHint(self) -> QSize:  # noqa: N802
        rows = max(1, min(self._combo.count(), COMBO_MAX_VISIBLE))
        return QSize(super().sizeHint().width(), rows * _ROW_H + _LIST_PAD)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self.sizeHint()


def _view_h(combo: QComboBox) -> int:
    rows = max(1, min(combo.count(), COMBO_MAX_VISIBLE))
    return rows * _ROW_H + _LIST_PAD


def _popup_h(combo: QComboBox) -> int:
    return _view_h(combo) + _BOX_CHROME


def _kill_popup_arrows(box: QWidget, view: QListView) -> None:
    lay = box.layout()
    if lay is not None:
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.setEnabled(False)
    for ch in box.children():
        if isinstance(ch, QWidget) and ch is not view:
            ch.hide()


def _place_popup(combo: QComboBox, box: QWidget, view: QListView, min_w: int) -> None:
    try:
        w = max(combo.width(), min_w, 120)
        h = _popup_h(combo)
        vh = _view_h(combo)
        fits = combo.count() <= COMBO_MAX_VISIBLE

        box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        box.setStyleSheet(CONTAINER_QSS)
        view.setStyleSheet(COMBO_POPUP_QSS)

        if fits:
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            view.setAutoScroll(False)
            view.verticalScrollBar().setEnabled(False)
            view.verticalScrollBar().setValue(0)
        else:
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            view.setAutoScroll(True)
            view.verticalScrollBar().setEnabled(True)

        _kill_popup_arrows(box, view)
        box.setFixedSize(w, h)
        view.setGeometry(1, 1, max(w - 2, 1), vh)
        view.show()
        view.raise_()

        gap = 1
        below = combo.mapToGlobal(QPoint(0, combo.height() + gap))
        screen = combo.screen()
        if screen is not None:
            avail = screen.availableGeometry()
            if below.y() + h > avail.bottom() and combo.mapToGlobal(QPoint(0, 0)).y() - h - gap >= avail.top():
                box.move(combo.mapToGlobal(QPoint(0, -h - gap)))
            else:
                x = min(max(avail.left(), below.x()), avail.right() - w + 1)
                box.move(QPoint(x, below.y()))
        else:
            box.move(below)
    except Exception:  # noqa: BLE001
        # Fall back to Qt's default popup geometry rather than crashing.
        pass


def tune_combo(combo: QComboBox, min_w: int = 100) -> None:
    """Uniform popup: ≤8 rows visible; scrollbar only when the list is longer."""
    combo.setMaxVisibleItems(COMBO_MAX_VISIBLE)
    combo.setMinimumWidth(min_w)
    combo.setMinimumHeight(34)
    # Reserve enough glyph slots for CJK (~14px/char) so closed-state text is not clipped.
    combo.setMinimumContentsLength(max(4, (min_w - 40) // 14))
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)

    view = _CappedListView(combo, combo)
    view.setObjectName("comboPopup")
    view.setFrameShape(QFrame.Shape.NoFrame)
    view.setUniformItemSizes(True)
    view.setAlternatingRowColors(False)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerItem)
    view.setMinimumWidth(max(min_w, 120))
    view.setItemDelegate(_PlainComboDelegate(view))
    view.setStyleSheet(COMBO_POPUP_QSS)
    combo.setView(view)

    def show_popup() -> None:
        view.setMaximumHeight(_view_h(combo))
        QComboBox.showPopup(combo)

        def polish() -> None:
            box = view.window()
            if box is not None:
                _place_popup(combo, box, view, min_w)

        QTimer.singleShot(0, polish)

    combo.showPopup = show_popup  # type: ignore[method-assign]
