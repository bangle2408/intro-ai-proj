from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def icon(name, color):
    image = QPixmap(40, 40)
    image.setDevicePixelRatio(2)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(color), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if name == "plus":
        painter.drawLine(4, 10, 16, 10)
        painter.drawLine(10, 4, 10, 16)
    elif name == "undo":
        painter.drawLine(7, 4, 3, 8)
        painter.drawLine(3, 8, 7, 12)
        painter.drawLine(3, 8, 12, 8)
        painter.drawArc(8, 8, 9, 9, -90 * 16, 180 * 16)
    elif name == "flip":
        painter.drawLine(4, 6, 16, 6)
        painter.drawLine(13, 3, 16, 6)
        painter.drawLine(16, 6, 13, 9)
        painter.drawLine(16, 14, 4, 14)
        painter.drawLine(7, 11, 4, 14)
        painter.drawLine(4, 14, 7, 17)
    elif name == "settings":
        for y, x in ((5, 7), (10, 13), (15, 8)):
            painter.drawLine(3, y, x - 2, y)
            painter.drawLine(x + 2, y, 17, y)
            painter.drawEllipse(x - 2, y - 2, 4, 4)
    elif name == "more":
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        for x in (5, 10, 15):
            painter.drawEllipse(x - 1, 9, 2, 2)
    painter.end()
    return QIcon(image)
