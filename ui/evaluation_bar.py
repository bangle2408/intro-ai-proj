from math import tanh

from PyQt5.QtCore import QEasingCurve, QRectF, Qt, QVariantAnimation
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget


class EvaluationBar(QWidget):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.fraction = self.target = 0.5
        self.flipped = False
        self.setAccessibleName("Evaluation bar")
        self.setFocusPolicy(Qt.NoFocus)
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(160)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.valueChanged.connect(self.advance)

    def set_position(self, score, flipped, result=None):
        target = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}.get(result)
        if target is None:
            target = 0.5 + 0.48 * tanh(score / 400)
        self.flipped = flipped
        if not self.cfg.animation_ms:
            self.animation.stop()
            self.fraction = target
        if target != self.target:
            self.animation.stop()
            self.target = target
            if self.cfg.animation_ms and self.isVisible():
                self.animation.setStartValue(self.fraction)
                self.animation.setEndValue(target)
                self.animation.start()
            else:
                self.fraction = target
        description = "Balanced position"
        if target > 0.52:
            description = "White has the advantage"
        elif target < 0.48:
            description = "Black has the advantage"
        self.setAccessibleDescription(description)
        self.update()

    def advance(self, value):
        self.fraction = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        clip = QPainterPath()
        clip.addRoundedRect(rect, 4, 4)
        painter.setClipPath(clip)
        painter.fillRect(rect, QColor(self.cfg.evaluation_black))
        height = rect.height() * self.fraction
        top = rect.top() if self.flipped else rect.bottom() - height
        painter.fillRect(
            QRectF(rect.left(), top, rect.width(), height), QColor(self.cfg.evaluation_white)
        )
        painter.setClipping(False)
        painter.setPen(QPen(QColor(self.cfg.evaluation_border), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(clip)
        painter.drawLine(0, self.height() // 2, 3, self.height() // 2)
