import chess
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from tests.gui_helpers import click_square, move_pointer, square_point, wait_until


def test_premove_while_real_search_worker_is_running(window, qapp):
    window.cfg.engine.depth = 20
    window.cfg.engine.time_ms = 350
    board = chess.Board()
    board.push_uci("e2e4")
    window.start_position(board)
    window.request_ai()
    assert window.worker.isRunning()
    click_square(window, "g1")
    click_square(window, "f3")
    assert window.premoves
    assert len(window.position.move_stack) == 1
    wait_until(qapp, lambda: len(window.position.move_stack) >= 3)
    assert window.position.move_stack[2].uci() == "g1f3"
    window.cancel_search()


def test_selection_survives_turn_change_for_click_input(waiting_window):
    window = waiting_window
    click_square(window, "g1")
    window.apply_move(chess.Move.from_uci("e7e5"))
    assert window.board_view.selected == chess.G1
    click_square(window, "f3")
    assert window.position.peek().uci() == "g1f3"


def test_next_drag_survives_execution_of_earlier_premove(waiting_window):
    window = waiting_window
    click_square(window, "g1")
    click_square(window, "f3")
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=square_point(window, "b1"))
    move_pointer(window, square_point(window, "c3"))
    window.apply_move(chess.Move.from_uci("e7e5"))
    assert window.position.peek().uci() == "g1f3"
    assert window.board_view.gesture.dragging
    QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=square_point(window, "c3"))
    assert window.premoves.items[0].move.uci() == "b1c3"
    assert window.position.piece_at(chess.B1) == chess.Piece(chess.KNIGHT, chess.WHITE)


def test_queue_full_does_not_leave_stale_destinations(waiting_window):
    window = waiting_window
    window.premoves.limit = 1
    click_square(window, "g1")
    click_square(window, "f3")
    click_square(window, "b1")
    click_square(window, "c3")
    assert len(window.premoves.items) == 1
    assert window.board_view.selected is None
    assert not window.board_view.targets
    assert "Queue full" in window.panel.premove_status.text()


def test_disabling_premoves_blocks_input_while_ai_thinks(waiting_window):
    window = waiting_window
    window.cfg.ui.premoves = False
    window.clear_input()
    click_square(window, "g1")
    click_square(window, "f3")
    assert not window.premoves
    assert window.board_view.selected is None


def test_escape_also_cancels_with_sidebar_focused(waiting_window):
    window = waiting_window
    click_square(window, "g1")
    click_square(window, "f3")
    window.header.preferences.setFocus()
    QTest.keyClick(window.header.preferences, Qt.Key_Escape)
    assert not window.premoves


def test_premove_disabled_in_spectator_mode(window):
    window.cfg.ui.mode = "ai_ai"
    window.active = True
    window.refresh()
    assert not window.board_view.input_enabled
    assert not window.board_view.movable


def test_closing_before_scheduled_search_prevents_background_worker(window, qapp, monkeypatch):
    monkeypatch.setattr(window, "confirm_discard", lambda: True)
    window.refresh()
    click_square(window, "e2")
    click_square(window, "e4")
    window.close()
    qapp.processEvents()
    assert not window.active
    assert window.worker is None
    assert not window.premoves
