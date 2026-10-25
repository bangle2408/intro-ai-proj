import chess
import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from tests.gui_helpers import click_square
from ui.dialogs import PromotionDialog
from ui.pieces import piece_pixmap, renderer


@pytest.mark.parametrize("color", chess.COLORS)
def test_all_vector_pieces_render_distinct_transparent_icons(cfg, qapp, color):
    fill = cfg.ui.white_piece if color else cfg.ui.black_piece
    edge = cfg.ui.white_piece_border if color else cfg.ui.black_piece_border
    images = []
    for kind in chess.PIECE_TYPES:
        assert renderer(kind, color, fill, edge).isValid()
        image = piece_pixmap(kind, color, 64, 1, fill, edge).toImage()
        assert image.pixelColor(0, 0).alpha() == 0
        assert any(image.pixelColor(x, 58).alpha() for x in range(64))
        assert all(image != other for other in images)
        images.append(image)


def test_piece_icons_preserve_high_dpi_resolution(cfg, qapp):
    pixmap = piece_pixmap(chess.QUEEN, True, 28, 2, cfg.ui.white_piece, cfg.ui.white_piece_border)
    assert pixmap.width() == pixmap.height() == 56
    assert pixmap.devicePixelRatioF() == 2


@pytest.mark.parametrize(
    "fen,source,target",
    [
        ("k7/7P/8/8/8/8/8/K7 w - - 0 1", "h7", "h8"),
        ("k7/8/8/8/8/8/7p/K7 b - - 0 1", "h2", "h1"),
    ],
)
def test_vector_promotion_choices_still_apply_selected_piece(window, fen, source, target):
    window.cfg.ui.mode = "human_human"
    window.start_position(chess.Board(fen))
    color = window.position.turn

    def choose():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PromotionDialog)
        assert all(not button.icon().isNull() for button in dialog.piece.group.buttons())
        QTest.mouseClick(dialog.piece.group.button(3), Qt.LeftButton)

    QTimer.singleShot(0, choose)
    click_square(window, source)
    click_square(window, target)
    assert window.position.piece_at(chess.parse_square(target)) == chess.Piece(chess.KNIGHT, color)
