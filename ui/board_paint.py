import chess
from PyQt5.QtCore import QRectF, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QPixmap

from ui.pieces import draw_piece


class BoardPainting:
    def paintEvent(self, event):
        ratio = self.devicePixelRatioF()
        if self.surface is None or self.surface.devicePixelRatioF() != ratio:
            size = QSize(round(self.width() * ratio), round(self.height() * ratio))
            self.surface = QPixmap(size)
            self.surface.setDevicePixelRatio(ratio)
            self.surface.fill(Qt.transparent)
            background = QPainter(self.surface)
            background.setRenderHint(QPainter.Antialiasing)
            self.paint_board(background)
            background.end()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, self.surface)
        self.paint_motion(painter)
        self.paint_annotations(painter)

    def paint_board(self, painter):
        _, _, cell = self.geometry_values()
        last = self.position.peek() if self.position.move_stack else None
        checked = self.position.king(self.position.turn) if self.position.is_check() else None
        hidden = {target for _, _, target in self.animated_pieces}
        drag = self.gesture if self.gesture and self.gesture.dragging else None
        if drag:
            hidden.add(drag.source)
        for row in range(8):
            for col in range(8):
                square = self.square_at(row, col)
                rect = self.square_rect(square)
                light = (row + col) % 2 == 0
                color = self.cfg.light_square if light else self.cfg.dark_square
                if last and square in (last.from_square, last.to_square):
                    color = self.cfg.last_move
                if square in self.queued_squares:
                    color = self.cfg.premove_color
                if square == self.selected:
                    color = self.cfg.selected
                if square == checked:
                    color = self.cfg.check
                painter.fillRect(rect, QColor(color))
                piece = self.board.piece_at(square)
                if drag and square == drag.source:
                    painter.setOpacity(0.25)
                    self.draw_piece(painter, drag.piece, rect, cell)
                    painter.setOpacity(1)
                elif piece and square not in hidden:
                    self.draw_piece(painter, piece, rect, cell)
                if square in self.targets and self.cfg.show_destinations:
                    self.draw_target(painter, rect, bool(piece), cell)
                if square == self.selected:
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QPen(QColor(self.cfg.text), 1.5))
                    painter.drawRect(rect.adjusted(2, 2, -2, -2))
                self.draw_coordinates(painter, rect, square, row, col, light, cell)

    def paint_motion(self, painter):
        _, _, cell = self.geometry_values()
        drag = self.gesture if self.gesture and self.gesture.dragging else None
        for piece, source, target in self.animated_pieces:
            origin, destination = self.square_rect(source), self.square_rect(target)
            offset = (destination.center() - origin.center()) * self.animation_progress
            self.draw_piece(painter, piece, origin.translated(offset), cell)
        if drag:
            hovered = self.square_at_point(drag.position)
            if hovered is not None:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor(self.cfg.text), 2))
                painter.drawRect(self.square_rect(hovered).adjusted(2, 2, -2, -2))
            rect = QRectF(drag.position.x() - cell / 2, drag.position.y() - cell / 2, cell, cell)
            self.draw_piece(painter, drag.piece, rect, cell)

    def draw_target(self, painter, rect, occupied, cell):
        color = QColor(self.cfg.target_color)
        color.setAlpha(150)
        painter.setPen(QPen(color, cell * 0.07) if occupied else Qt.NoPen)
        painter.setBrush(Qt.NoBrush if occupied else color)
        radius = cell * (0.44 if occupied else 0.12)
        painter.drawEllipse(rect.center(), radius, radius)

    def draw_coordinates(self, painter, rect, square, row, col, light, cell):
        painter.setFont(QFont(self.cfg.font, 9))
        painter.setPen(QColor(self.cfg.muted))
        if col == 0:
            painter.drawText(
                QRectF(rect.x() - 14, rect.y(), 10, cell),
                Qt.AlignVCenter | Qt.AlignRight,
                str(chess.square_rank(square) + 1),
            )
        if row == 7:
            painter.drawText(
                QRectF(rect.x(), rect.bottom() + 2, cell, 14),
                Qt.AlignVCenter | Qt.AlignHCenter,
                chess.FILE_NAMES[chess.square_file(square)],
            )

    def draw_piece(self, painter, piece, rect, cell):
        if piece is None:
            return
        inset = cell * 0.05
        draw_piece(painter, piece, rect.adjusted(inset, inset, -inset, -inset), self.cfg)
