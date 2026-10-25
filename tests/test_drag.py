import chess
import pytest
from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from tests.gui_helpers import click_square, drag_piece, move_pointer, square_point


def test_drag_follows_pointer_and_commits_only_on_release(window):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    origin, target = square_point(window, "e2"), square_point(window, "e4")
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=origin)
    move_pointer(window, target)
    assert window.board_view.gesture.dragging
    assert window.board_view.gesture.position.toPoint() == target
    assert window.position.fen() == chess.STARTING_FEN
    QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=target)
    assert window.position.peek().uci() == "e2e4"
    assert window.board_view.gesture is None
    assert not window.board_view.animated_pieces


def test_fast_drag_does_not_require_intermediate_move_event(window):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=square_point(window, "e2"))
    QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=square_point(window, "e4"))
    assert window.position.peek().uci() == "e2e4"


@pytest.mark.parametrize("destination", ["e5", "e2", QPoint(-20, -20)])
def test_invalid_drop_or_return_to_origin_cancels(window, destination):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    if destination == "e2":
        point = square_point(window, "e2")
        QTest.mousePress(window.board_view, Qt.LeftButton, pos=point)
        move_pointer(window, square_point(window, "e4"))
        move_pointer(window, point)
        QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=point)
    else:
        drag_piece(window, "e2", destination)
    assert window.position.fen() == chess.STARTING_FEN
    assert window.board_view.gesture is None
    assert window.board_view.selected is None


def test_small_motion_is_a_click_not_a_drag(window):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    origin = square_point(window, "e2")
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=origin)
    move_pointer(window, origin + QPoint(1, 1))
    assert not window.board_view.gesture.dragging
    QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=origin + QPoint(1, 1))
    assert window.board_view.selected == chess.E2
    click_square(window, "e4")
    assert window.position.peek().uci() == "e2e4"


def test_drag_and_click_work_when_board_is_flipped(window):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    window.flip()
    drag_piece(window, "e2", "e4")
    click_square(window, "e7")
    click_square(window, "e5")
    assert [m.uci() for m in window.position.move_stack] == ["e2e4", "e7e5"]


def test_drag_only_does_not_play_two_clicks(window):
    window.cfg.ui.mode = "human_human"
    window.cfg.ui.move_method = "drag"
    window.clear_input()
    window.refresh()
    click_square(window, "e2")
    click_square(window, "e4")
    assert not window.position.move_stack
    drag_piece(window, "e2", "e4")
    assert window.position.peek().uci() == "e2e4"


def test_click_only_ignores_drag(window):
    window.cfg.ui.mode = "human_human"
    window.cfg.ui.move_method = "click"
    window.clear_input()
    window.refresh()
    drag_piece(window, "e2", "e4")
    assert not window.position.move_stack
    click_square(window, "e4")
    assert window.position.peek().uci() == "e2e4"


@pytest.mark.parametrize("cancel", ["right", "escape", "deactivate"])
def test_cancel_during_drag_prevents_late_release(window, cancel):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=square_point(window, "e2"))
    move_pointer(window, square_point(window, "e4"))
    if cancel == "right":
        QTest.mouseClick(window.board_view, Qt.RightButton)
    elif cancel == "escape":
        QTest.keyClick(window.board_view, Qt.Key_Escape)
    else:
        QApplication.sendEvent(window, QEvent(QEvent.WindowDeactivate))
    QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=square_point(window, "e4"))
    assert not window.position.move_stack
    assert window.board_view.gesture is None


def test_click_animation_does_not_block_next_piece(window):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    click_square(window, "e2")
    click_square(window, "e4")
    assert window.board_view.animated_pieces
    drag_piece(window, "e7", "e5")
    assert len(window.position.move_stack) == 2
    assert not window.board_view.animated_pieces


def test_ai_move_during_held_drag_keeps_piece_under_pointer(waiting_window):
    window = waiting_window
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=square_point(window, "g1"))
    move_pointer(window, square_point(window, "f3"))
    window.apply_move(chess.Move.from_uci("e7e5"))
    assert window.board_view.gesture.dragging
    QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=square_point(window, "f3"))
    assert window.position.peek().uci() == "g1f3"
    assert len(window.position.move_stack) == 3
