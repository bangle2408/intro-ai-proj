from functools import lru_cache
from importlib.resources import files

import chess
from PyQt5.QtCore import QByteArray, QRectF, QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QWidget


@lru_cache(maxsize=12)
def source(piece_type, color):
    side = "white" if color else "black"
    name = f"{side}-{chess.piece_name(piece_type)}.svg"
    return files("assets").joinpath("pieces", name).read_text()


@lru_cache(maxsize=96)
def renderer(piece_type, color, fill, edge, outline=0.65):
    original = ("#FFFCF5", "#344A3B") if color else ("#293E32", "#F7F3E7")
    svg = source(piece_type, color).replace(original[0], "@fill@").replace(original[1], "@edge@")
    svg = svg.replace("@fill@", fill).replace("@edge@", edge)
    if not color:
        svg = svg.replace('stroke-width="0.65"', f'stroke-width="{outline}"')
    return QSvgRenderer(QByteArray(svg.encode()))


def draw_piece(painter, piece, rect, cfg):
    fill = cfg.white_piece if piece.color else cfg.black_piece
    edge = cfg.white_piece_border if piece.color else cfg.black_piece_border
    height = min(rect.height(), rect.width() * 110 / 80)
    width = height * 80 / 110
    target = QRectF(rect.center().x() - width / 2, rect.bottom() - height, width, height)
    renderer(piece.piece_type, piece.color, fill, edge, cfg.black_piece_outline).render(
        painter, target
    )


@lru_cache(maxsize=192)
def piece_pixmap(piece_type, color, size, ratio, fill, edge, outline=0.65):
    pixmap = QPixmap(round(size * ratio), round(size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    width = size * 80 / 110
    renderer(piece_type, color, fill, edge, outline).render(
        painter, QRectF((size - width) / 2, 0, width, size)
    )
    painter.end()
    return pixmap


def piece_icon(piece, cfg, size=28):
    fill = cfg.white_piece if piece.color else cfg.black_piece
    edge = cfg.white_piece_border if piece.color else cfg.black_piece_border
    return QIcon(
        piece_pixmap(piece.piece_type, piece.color, size, 2, fill, edge, cfg.black_piece_outline)
    )


class CapturedPieces(QWidget):
    def __init__(self, cfg):
        super().__init__()
        self.cfg, self.pieces, self.color = cfg, (), chess.WHITE
        self.setFixedHeight(20)

    def sizeHint(self):
        return QSize(40, 20)

    def set_pieces(self, pieces, color):
        pieces = tuple(pieces)
        if (pieces, color) == (self.pieces, self.color):
            return
        self.pieces, self.color = pieces, color
        names = ", ".join(chess.piece_name(piece.piece_type) for piece in pieces)
        self.setAccessibleName(f"Captured pieces: {names or 'none'}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.pieces:
            painter.setPen(QColor(self.cfg.muted))
            font = painter.font()
            font.setPixelSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignVCenter, "White" if self.color else "Black")
            return
        step = min(15, max(0, (self.width() - 16) / max(1, len(self.pieces) - 1)))
        for index, piece in enumerate(self.pieces):
            fill = self.cfg.white_piece if piece.color else self.cfg.captured_black
            edge = self.cfg.white_piece_border if piece.color else self.cfg.background
            pixmap = piece_pixmap(
                piece.piece_type,
                piece.color,
                20,
                self.devicePixelRatioF(),
                fill,
                edge,
                self.cfg.black_piece_outline,
            )
            painter.drawPixmap(round(index * step), 0, pixmap)
