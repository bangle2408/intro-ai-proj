import chess
from PyQt5.QtCore import QRectF, Qt, pyqtSignal
from PyQt5.QtWidgets import QSizePolicy, QWidget

from ui.annotations import BoardAnnotations
from ui.board_animation import BoardAnimation
from ui.board_paint import BoardPainting
from ui.board_pointer import BoardPointer


class BoardView(BoardPointer, BoardPainting, BoardAnimation, BoardAnnotations, QWidget):
    pressed = pyqtSignal(int)
    clicked = pyqtSignal(int)
    dropped = pyqtSignal(int, int)
    cancelled = pyqtSignal()

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.position = chess.Board()
        self.board = self.position.copy()
        self.selected = None
        self.flipped = False
        self.gesture = None
        self.press_square = None
        self.input_enabled = False
        self.movable = set()
        self.targets = set()
        self.queued_squares = set()
        self.surface = None
        self.setup_annotations()
        self.setup_animation()
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def geometry_values(self):
        size = min(self.width(), self.height()) - 28
        return (self.width() - size) / 2, (self.height() - size) / 2, size / 8

    def square_at(self, row, col):
        return chess.square(7 - col if self.flipped else col, row if self.flipped else 7 - row)

    def square_at_point(self, point):
        x, y, cell = self.geometry_values()
        col, row = int((point.x() - x) // cell), int((point.y() - y) // cell)
        return self.square_at(row, col) if 0 <= row < 8 and 0 <= col < 8 else None

    def square_rect(self, square):
        x, y, cell = self.geometry_values()
        col, row = chess.square_file(square), 7 - chess.square_rank(square)
        if self.flipped:
            row, col = 7 - row, 7 - col
        return QRectF(x + col * cell, y + row * cell, cell, cell)

    def sync(self, position, preview, plans, movable, targets):
        if self.position != position:
            self.clear_annotations()
        self.position = position.copy(stack=True)
        self.board = preview
        self.movable = movable
        self.input_enabled = bool(movable)
        self.targets = targets
        self.queued_squares = {
            square for plan in plans for square in (plan.move.from_square, plan.move.to_square)
        }
        if self.gesture and preview.piece_at(self.gesture.source) != self.gesture.piece:
            self.reset_pointer()
            self.selected = None
            self.targets = set()
        if self.selected not in movable:
            self.selected = None
            self.targets = set()
        self.invalidate_board()

    def invalidate_board(self):
        self.surface = None
        self.update()
