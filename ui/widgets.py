from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from ui.icons import icon


class ActionButton(QPushButton):
    def __init__(self, title, action, cfg, symbol=None, primary=False):
        super().__init__(title)
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName(title)
        self.setObjectName("primary" if primary else "quiet")
        if symbol:
            self.setIcon(icon(symbol, cfg.surface if primary else cfg.text))
        if action:
            self.clicked.connect(action)


class Toggle(QAbstractButton):
    def __init__(self, name, checked, cfg):
        super().__init__()
        self.cfg = cfg
        self.setCheckable(True)
        self.setChecked(checked)
        self.setAccessibleName(name)
        self.setFixedSize(44, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        if not self.isEnabled():
            painter.setOpacity(0.45)
        painter.setBrush(QColor(self.cfg.accent if self.isChecked() else "#7E8D82"))
        painter.drawRoundedRect(3, 6, 38, 20, 10, 10)
        painter.setBrush(QColor(self.cfg.surface))
        painter.drawEllipse(23 if self.isChecked() else 5, 8, 16, 16)
        if self.hasFocus():
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(self.cfg.focus), 1))
            painter.drawRoundedRect(1, 3, 42, 26, 13, 13)


class Choice(QComboBox):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setMinimumHeight(40)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(self.cfg.muted), 1.5, Qt.SolidLine, Qt.RoundCap))
        x, y = self.width() - 19, self.height() // 2
        painter.drawLine(x - 4, y - 2, x, y + 2)
        painter.drawLine(x, y + 2, x + 4, y - 2)


class Segments(QWidget):
    changed = pyqtSignal(object)

    def __init__(self, choices, current):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.values = [value for _, value in choices]
        self.group = QButtonGroup(self)
        for index, (label, value) in enumerate(choices):
            button = QPushButton(label)
            button.setObjectName("segment")
            button.setCheckable(True)
            button.setMinimumHeight(40)
            button.setCursor(Qt.PointingHandCursor)
            self.group.addButton(button, index)
            layout.addWidget(button)
            button.setChecked(value == current)
        self.group.idClicked.connect(lambda index: self.changed.emit(self.values[index]))

    def currentData(self):
        return self.values[max(0, self.group.checkedId())]
