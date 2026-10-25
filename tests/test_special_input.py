from types import SimpleNamespace

import chess
import pytest
from PyQt5.QtWidgets import QDialog

from tests.gui_helpers import click_square, drag_piece


def queue(window, source, target):
    click_square(window, source)
    click_square(window, target)


def test_black_can_drag_premove_before_white_first_move(waiting_window):
    window = waiting_window
    window.cfg.ui.player_color = "black"
    window.start_position(chess.Board())
    window.refresh()
    drag_piece(window, "e7", "e5")
    assert window.premoves
    window.apply_move(chess.Move.from_uci("e2e4"))
    assert window.position.peek().uci() == "e7e5"
    assert len(window.position.move_stack) == 2


def test_premove_en_passant_is_validated_in_resulting_position(waiting_window):
    window = waiting_window
    window.start_position(chess.Board("7k/3p4/8/4P3/8/8/8/7K b - - 0 1"))
    window.refresh()
    queue(window, "e5", "d6")
    window.apply_move(chess.Move.from_uci("d7d5"))
    assert window.position.peek().uci() == "e5d6"
    assert window.position.piece_at(chess.D5) is None


@pytest.mark.parametrize("reply,allowed", [("h8h7", True), ("h8f8", False)])
def test_premove_castling_rechecks_attacked_squares(waiting_window, reply, allowed):
    window = waiting_window
    window.start_position(chess.Board("4k2r/8/8/8/8/8/8/4K2R b K - 0 1"))
    window.refresh()
    queue(window, "e1", "g1")
    window.apply_move(chess.Move.from_uci(reply))
    assert not window.premoves
    assert (window.position.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)) == allowed
    assert len(window.position.move_stack) == (2 if allowed else 1)


@pytest.mark.parametrize("mate", [False, True])
def test_ai_reply_during_promotion_dialog_cannot_submit_stale_move(
    waiting_window, monkeypatch, mate
):
    window = waiting_window
    fen = "8/7P/8/8/8/2k5/3q4/K7 b - - 0 1" if mate else "7k/7P/8/8/8/8/8/K7 b - - 0 1"
    window.start_position(chess.Board(fen))
    window.refresh()

    class ReplyDuringDialog:
        def __init__(self, parent):
            self.piece = SimpleNamespace(currentData=lambda: chess.QUEEN)

        def exec_(self):
            window.apply_move(chess.Move.from_uci("d2b2" if mate else "h8g7"))
            return QDialog.Accepted

    monkeypatch.setattr("ui.input.PromotionDialog", ReplyDuringDialog)
    queue(window, "h7", "h8")
    if mate:
        assert window.result == "0-1"
        assert len(window.position.move_stack) == 1
        assert window.position.piece_at(chess.H7) == chess.Piece(chess.PAWN, chess.WHITE)
    else:
        assert window.position.piece_at(chess.H8) == chess.Piece(chess.QUEEN, chess.WHITE)
        assert len(window.position.move_stack) == 2
