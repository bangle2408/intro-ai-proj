import chess
from PyQt5.QtCore import QEasingCurve, QVariantAnimation


class BoardAnimation:
    def setup_animation(self):
        self.animated_pieces = []
        self.animation_progress = 1.0
        self.animation = QVariantAnimation(self)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.valueChanged.connect(self.animation_step)
        self.animation.finished.connect(self.stop_animation)

    def animation_step(self, progress):
        self.animation_progress = progress
        self.update()

    def animate_move(self, move, previous):
        self.stop_animation()
        if self.cfg.animation_ms == 0 or self.gesture:
            return
        piece = self.board.piece_at(move.to_square)
        if not piece:
            return
        self.animated_pieces = [(piece, move.from_square, move.to_square)]
        if previous.is_castling(move):
            rank = chess.square_rank(move.from_square)
            right = move.to_square > move.from_square
            origin, target = (
                chess.square(7 if right else 0, rank),
                chess.square(5 if right else 3, rank),
            )
            rook = self.board.piece_at(target)
            if rook:
                self.animated_pieces.append((rook, origin, target))
        self.animation_progress = 0.0
        self.invalidate_board()
        self.animation.setDuration(self.cfg.animation_ms)
        self.animation.start()

    def stop_animation(self):
        self.animation.stop()
        self.animated_pieces = []
        self.invalidate_board()
