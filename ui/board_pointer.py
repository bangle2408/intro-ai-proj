from dataclasses import dataclass

import chess
from PyQt5.QtCore import QPointF, Qt


@dataclass
class PointerGesture:
    source: int
    piece: chess.Piece
    origin: QPointF
    position: QPointF
    previously_selected: bool
    dragging: bool = False


class BoardPointer:
    def mousePressEvent(self, event):
        self.setFocus(Qt.MouseFocusReason)
        if event.button() == Qt.RightButton:
            self.begin_drawing(event)
            return
        if event.button() == Qt.LeftButton:
            self.clear_annotations()
        if event.buttons() & Qt.RightButton:
            self.reset_pointer()
            return
        if event.button() != Qt.LeftButton or not self.input_enabled:
            return
        self.reset_pointer()
        self.stop_animation()
        square = self.square_at_point(event.localPos())
        if square is None:
            self.cancelled.emit()
            return
        previous = self.selected
        self.pressed.emit(square)
        self.press_square = square
        if square in self.movable and self.selected == square:
            self.gesture = PointerGesture(
                square,
                self.board.piece_at(square),
                event.localPos(),
                event.localPos(),
                previous == square,
            )

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.track_drawing(event)
            return
        gesture = self.gesture
        if gesture and self.cfg.move_method != "click":
            if not event.buttons() & Qt.LeftButton:
                self.reset_pointer()
                return
            self.track_pointer(event.localPos())
            if gesture.dragging:
                self.setCursor(Qt.ClosedHandCursor)
                self.update()
                return
        square = self.square_at_point(event.localPos())
        cursor = Qt.ArrowCursor
        if square in self.movable:
            cursor = Qt.PointingHandCursor if self.cfg.move_method == "click" else Qt.OpenHandCursor
        elif square in self.targets:
            cursor = Qt.PointingHandCursor
        self.setCursor(cursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.finish_drawing(event)
            return
        if event.button() != Qt.LeftButton:
            return
        if self.gesture and self.cfg.move_method != "click":
            self.track_pointer(event.localPos())
        square = self.square_at_point(event.localPos())
        gesture, pressed = self.gesture, self.press_square
        self.reset_pointer()
        if pressed is None or not self.input_enabled:
            return
        if gesture and gesture.dragging:
            if square is not None and square != gesture.source:
                self.dropped.emit(gesture.source, square)
            else:
                self.selected = None
                self.targets = set()
                self.update()
        elif self.cfg.move_method != "drag" and square == pressed:
            if not gesture or gesture.previously_selected:
                self.clicked.emit(square)

    def track_pointer(self, point):
        self.gesture.position = point
        distance = point - self.gesture.origin
        if (
            not self.gesture.dragging
            and distance.x() ** 2 + distance.y() ** 2 >= self.cfg.drag_threshold_px**2
        ):
            self.gesture.dragging = True
            self.invalidate_board()

    def reset_pointer(self):
        self.drawing = None
        self.gesture = None
        self.press_square = None
        self.unsetCursor()
        self.invalidate_board()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clear_annotations()
            self.cancelled.emit()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        event.accept()

    def resizeEvent(self, event):
        self.reset_pointer()
        super().resizeEvent(event)
