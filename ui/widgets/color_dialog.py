"""Qt 自带取色器（非系统原生），界面用中文。"""

from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QPushButton,
    QWidget,
)

_LABELS = {
    "&Basic colors": "基本颜色",
    "Basic colors": "基本颜色",
    "&Custom colors": "自定义颜色",
    "Custom colors": "自定义颜色",
    "Hu&e:": "色相:",
    "Hue:": "色相:",
    "&Sat:": "饱和度:",
    "Sat:": "饱和度:",
    "&Val:": "明度:",
    "Val:": "明度:",
    "&Red:": "红:",
    "Red:": "红:",
    "&Green:": "绿:",
    "Green:": "绿:",
    "Bl&ue:": "蓝:",
    "Blue:": "蓝:",
    "&HTML:": "色值:",
    "HTML:": "色值:",
    "HTML(&H):": "色值(&H):",
    "HTML(&H)：": "色值(&H):",
    "&Pick Screen Color": "取屏幕颜色",
    "Pick Screen Color": "取屏幕颜色",
    "&Add to Custom Colors": "添加到自定义颜色",
    "Add to Custom Colors": "添加到自定义颜色",
    "OK": "确定",
    "&OK": "确定",
    "Cancel": "取消",
    "&Cancel": "取消",
}


def _localize(dialog: QColorDialog) -> None:
    box = dialog.findChild(QDialogButtonBox)
    if box is not None:
        ok = box.button(QDialogButtonBox.StandardButton.Ok)
        if ok is not None:
            ok.setText("确定")
        cancel = box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel is not None:
            cancel.setText("取消")
    for widget in dialog.findChildren(QWidget):
        if not isinstance(widget, (QLabel, QPushButton, QGroupBox)):
            continue
        text = widget.text()
        mapped = _LABELS.get(text) or _LABELS.get(text.replace("&", ""))
        if mapped:
            widget.setText(mapped)


def pick_color(parent: QWidget | None, current: QColor, title: str) -> QColor:
    dialog = QColorDialog(current, parent)
    dialog.setWindowTitle(title)
    dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
    dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
    _localize(dialog)
    if dialog.exec():
        chosen = dialog.selectedColor()
        if chosen.isValid():
            return chosen
    return QColor()
