from dataclasses import dataclass
from math import hypot

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QPainterPath, QPainterPathStroker, QPen, QPolygonF


@dataclass
class Drawing:
    source: int
    target: int | None
    modifiers: int

    def color(self):
        if self.modifiers & Qt.AltModifier:
            return "blue"
        if self.modifiers & Qt.ShiftModifier:
            return "green"
        circle = self.source == self.target
        if self.modifiers & Qt.ControlModifier:
            return "yellow" if circle else "red"
        return "red" if circle else "yellow"


class BoardAnnotations:
    def setup_annotations(self):
        self.annotations = {}
        self.drawing = None

    def begin_drawing(self, event):
        self.cancelled.emit()
        self.reset_pointer()
        source = self.square_at_point(event.localPos())
        if source is not None:
            self.drawing = Drawing(source, source, int(event.modifiers()))
            self.setCursor(Qt.CrossCursor)
            self.update()

    def track_drawing(self, event):
        if not event.buttons() & Qt.RightButton:
            self.reset_pointer()
            return
        target = self.square_at_point(event.localPos())
        if target != self.drawing.target:
            self.drawing.target = target
            self.update()

    def finish_drawing(self, event):
        current = self.drawing
        if current:
            current.target = self.square_at_point(event.localPos())
            if current.target is not None:
                key, color = (current.source, current.target), current.color()
                if self.annotations.get(key) == color:
                    del self.annotations[key]
                else:
                    self.annotations.pop(key, None)
                    self.annotations[key] = color
            self.drawing = None
            self.unsetCursor()
            self.update()

    def clear_annotations(self):
        self.annotations.clear()
        if self.drawing:
            self.unsetCursor()
        self.drawing = None
        self.update()

    def paint_annotations(self, painter):
        current = self.drawing
        preview = (current.source, current.target) if current else None
        painter.save()
        x, y, cell = self.geometry_values()
        painter.setClipRect(int(x), int(y), round(cell * 8), round(cell * 8))
        for (source, target), color in self.annotations.items():
            if (source, target) != preview:
                self.paint_annotation(painter, source, target, color)
        if current and current.target is not None:
            self.paint_annotation(painter, current.source, current.target, current.color(), True)
        painter.restore()

    def paint_annotation(self, painter, source, target, name, preview=False):
        _, _, cell = self.geometry_values()
        start, end = self.square_rect(source).center(), self.square_rect(target).center()
        color = QColor(self.cfg.annotation_colors[name])
        color.setAlphaF(self.cfg.annotation_opacity * (0.8 if preview else 1))
        if source == target:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(color, cell * 0.065))
            painter.drawEllipse(start, cell * 0.42, cell * 0.42)
            return
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawPath(arrow_path(start, end, cell, self.cfg.annotation_knight_bend))


def arrow_path(start, end, cell, bend=False):
    delta = end - start
    corner = None
    steps = sorted((round(abs(delta.x()) / cell), round(abs(delta.y()) / cell)))
    if bend and steps == [1, 2]:
        corner = (
            QPointF(end.x(), start.y())
            if abs(delta.x()) > abs(delta.y())
            else QPointF(start.x(), end.y())
        )
    first = (corner if corner is not None else end) - start
    last = end - (corner if corner is not None else start)
    first /= hypot(first.x(), first.y())
    last /= hypot(last.x(), last.y())
    shaft = QPainterPath(start + first * (cell * 0.12))
    if corner is not None:
        shaft.lineTo(corner)
    base = end - last * (cell * 0.3)
    shaft.lineTo(base)
    stroke = QPainterPathStroker()
    stroke.setWidth(cell * 0.125)
    stroke.setCapStyle(Qt.RoundCap)
    stroke.setJoinStyle(Qt.RoundJoin)
    wing = QPointF(-last.y(), last.x()) * (cell * 0.22)
    head = QPainterPath()
    head.addPolygon(QPolygonF([end, base + wing, base - wing]))
    head.closeSubpath()
    return stroke.createStroke(shaft).united(head)
