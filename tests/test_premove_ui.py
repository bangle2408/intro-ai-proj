import chess
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QFileDialog

from tests.gui_helpers import click_square, drag_piece, move_pointer, square_point
from utils.persistence import save_game


def queue_move(window, source="g1", target="f3", drag=False):
    if drag:
        drag_piece(window, source, target)
    else:
        click_square(window, source)
        click_square(window, target)


@pytest.mark.parametrize("drag", [False, True])
def test_premove_is_only_preview_until_opponent_moves(waiting_window, drag):
    window = waiting_window
    before = window.position.fen()
    queue_move(window, drag=drag)
    assert window.position.fen() == before
    assert window.premoves
    assert window.board_view.board.piece_at(chess.F3) == chess.Piece(chess.KNIGHT, chess.WHITE)
    assert window.position.piece_at(chess.G1) == chess.Piece(chess.KNIGHT, chess.WHITE)
    window.apply_move(chess.Move.from_uci("a7a6"))
    assert [m.uci() for m in window.position.move_stack] == ["e2e4", "a7a6", "g1f3"]
    assert not window.premoves
    assert not window.board_view.animated_pieces


def test_premove_queue_plays_one_move_per_opponent_reply(waiting_window):
    window = waiting_window
    queue_move(window, "g1", "f3")
    queue_move(window, "b1", "c3")
    window.apply_move(chess.Move.from_uci("e7e5"))
    assert window.position.peek().uci() == "g1f3"
    assert len(window.premoves.items) == 1
    window.apply_move(chess.Move.from_uci("b8c6"))
    assert window.position.peek().uci() == "b1c3"
    assert not window.premoves


def test_conditional_recapture_can_target_current_friendly_piece(waiting_window):
    window = waiting_window
    board = chess.Board("3r3k/8/8/8/3N4/8/8/3Q3K b - - 0 1")
    window.start_position(board)
    window.refresh()
    queue_move(window, "d1", "d4")
    assert window.position.piece_at(chess.D4) == chess.Piece(chess.KNIGHT, chess.WHITE)
    window.apply_move(chess.Move.from_uci("d8d4"))
    assert window.position.peek().uci() == "d1d4"
    assert window.position.piece_at(chess.D4) == chess.Piece(chess.QUEEN, chess.WHITE)


@pytest.mark.parametrize("reply", ["d8e8", "d8d4"])
def test_check_or_captured_source_cancels_queue(waiting_window, reply):
    window = waiting_window
    board = chess.Board("3r2k1/8/8/8/3N4/8/8/4K1N1 b - - 0 1")
    window.start_position(board)
    window.refresh()
    source, target = ("g1", "f3") if reply == "d8e8" else ("d4", "f5")
    queue_move(window, source, target)
    window.apply_move(chess.Move.from_uci(reply))
    assert len(window.position.move_stack) == 1
    assert not window.premoves
    assert not window.board_view.queued_squares


@pytest.mark.parametrize("action", ["new_position", "undo", "right", "escape", "disable"])
def test_cancel_paths_clear_pending_moves(waiting_window, action):
    window = waiting_window
    queue_move(window)
    assert window.premoves
    if action == "new_position":
        window.cancel_search()
        window.start_position(chess.Board())
    elif action == "right":
        QTest.mouseClick(window.board_view, Qt.RightButton)
    elif action == "escape":
        QTest.keyClick(window.board_view, Qt.Key_Escape)
    elif action == "disable":
        window.cfg.ui.premoves = False
        window.clear_input()
    else:
        getattr(window, action)()
    assert not window.premoves
    assert not window.board_view.queued_squares


def test_loading_does_not_replay_old_premove(waiting_window, tmp_path, monkeypatch):
    window = waiting_window
    path = tmp_path / "saved.chess"
    save_game(path, window.position, window.cfg.ui, window.clock.snapshot())
    queue_move(window)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    window.load()
    assert not window.premoves
    assert window.active


def test_premove_chooses_underpromotion_before_execution(waiting_window, monkeypatch):
    window = waiting_window
    window.start_position(chess.Board("7k/P7/8/8/8/8/8/7K b - - 0 1"))
    window.refresh()
    monkeypatch.setattr(window, "promotion_choice", lambda: chess.ROOK)
    queue_move(window, "a7", "a8")
    assert window.premoves.items[0].move.promotion == chess.ROOK
    window.apply_move(chess.Move.from_uci("h8g8"))
    assert window.position.piece_at(chess.A8) == chess.Piece(chess.ROOK, chess.WHITE)


def test_premove_charges_minimum_time_before_increment(waiting_window, monkeypatch):
    window = waiting_window
    monkeypatch.setattr("ui.clock.monotonic", lambda: 100)
    window.clock.enabled = True
    window.clock.remaining = {chess.WHITE: 1000, chess.BLACK: 1000}
    window.clock.increments = {chess.WHITE: 2000, chess.BLACK: 2000}
    window.clock.start(chess.BLACK)
    queue_move(window)
    window.apply_move(chess.Move.from_uci("e7e5"))
    assert window.clock.remaining[chess.WHITE] == 2900
    assert window.clock.remaining[chess.BLACK] == 3000


def test_premove_cannot_rescue_expired_clock_with_increment(waiting_window, monkeypatch):
    window = waiting_window
    monkeypatch.setattr("ui.clock.monotonic", lambda: 100)
    window.clock.enabled = True
    window.clock.remaining = {chess.WHITE: 80, chess.BLACK: 1000}
    window.clock.increments = {chess.WHITE: 2000, chess.BLACK: 2000}
    window.clock.start(chess.BLACK)
    queue_move(window)
    window.apply_move(chess.Move.from_uci("e7e5"))
    assert window.result == "0-1"
    assert window.position.peek().uci() == "e7e5"
    assert window.clock.remaining[chess.WHITE] == 0
    assert not window.premoves


def test_source_captured_while_dragging_cannot_be_released(waiting_window):
    window = waiting_window
    window.start_position(chess.Board("3r2k1/8/8/8/3N4/8/8/4K1N1 b - - 0 1"))
    window.refresh()
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=square_point(window, "d4"))
    move_pointer(window, square_point(window, "f5"))
    window.apply_move(chess.Move.from_uci("d8d4"))
    QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=square_point(window, "f5"))
    assert len(window.position.move_stack) == 1
    assert window.board_view.gesture is None
