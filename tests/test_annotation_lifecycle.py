import chess
import pytest
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFileDialog

from tests.gui_helpers import click_square, draw_annotation, move_pointer, square_point, wait_until
from ui.annotations import arrow_path
from utils.persistence import save_game


@pytest.mark.parametrize(
    "action", ["escape", "sidebar_escape", "left_click", "new_game", "undo", "load"]
)
def test_game_actions_clear_annotations(window, tmp_path, monkeypatch, action):
    window.cfg.ui.mode = "human_human"
    click_square(window, "e2")
    click_square(window, "e4")
    draw_annotation(window, "e7", "e5")
    if action == "escape":
        QTest.keyClick(window.board_view, Qt.Key_Escape)
    elif action == "sidebar_escape":
        window.header.preferences.setFocus()
        QTest.keyClick(window.header.preferences, Qt.Key_Escape)
    elif action == "left_click":
        click_square(window, "a3")
    elif action == "new_game":
        window.start_position(chess.Board())
    elif action == "undo":
        window.undo()
    else:
        path = tmp_path / "saved.chess"
        save_game(path, window.position, window.cfg.ui, window.clock.snapshot())
        monkeypatch.setattr(window, "confirm_discard", lambda: True)
        monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
        window.load()
    assert not window.board_view.annotations
    assert window.board_view.drawing is None


def test_right_mouse_still_cancels_premove_and_does_not_stop_ai(waiting_window):
    window = waiting_window
    click_square(window, "g1")
    click_square(window, "f3")
    assert window.premoves
    draw_annotation(window, "d2", "d4")
    assert not window.premoves
    assert window.board_view.selected is None
    assert window.board_view.annotations == {(chess.D2, chess.D4): "yellow"}
    assert window.position.peek().uci() == "e2e4"


@pytest.mark.parametrize("draft", [False, True])
def test_ai_move_clears_old_annotations_and_cancels_stale_release(waiting_window, draft):
    window = waiting_window
    view = window.board_view
    draw_annotation(window, "g1", "f3")
    if draft:
        QTest.mousePress(view, Qt.RightButton, pos=square_point(window, "d2"))
        move_pointer(window, square_point(window, "d4"), button=Qt.RightButton)
    window.apply_move(chess.Move.from_uci("e7e5"))
    QTest.mouseRelease(view, Qt.RightButton, pos=square_point(window, "d4"))
    assert not view.annotations and view.drawing is None
    assert len(window.position.move_stack) == 2


@pytest.mark.parametrize("cancel", ["deactivate", "resize", "lost_button"])
def test_lost_gesture_cancels_draft_and_keeps_completed_shapes(window, cancel):
    view = window.board_view
    draw_annotation(window, "d4")
    QTest.mousePress(view, Qt.RightButton, pos=square_point(window, "g1"))
    move_pointer(window, square_point(window, "f3"), button=Qt.RightButton)
    if cancel == "deactivate":
        QApplication.sendEvent(window, QEvent(QEvent.WindowDeactivate))
    elif cancel == "resize":
        window.resize(1100, 800)
        QApplication.processEvents()
    else:
        move_pointer(window, square_point(window, "f3"), held=False)
    QTest.mouseRelease(view, Qt.RightButton, pos=square_point(window, "f3"))
    assert view.annotations == {(chess.D4, chess.D4): "red"}
    assert view.drawing is None


@pytest.mark.parametrize("mode", ["ai_ai", "finished"])
def test_drawing_works_when_piece_input_is_disabled(window, mode):
    if mode == "finished":
        window.finish("1/2-1/2", "Draw")
    else:
        window.cfg.ui.mode = "ai_ai"
        window.refresh()
    draw_annotation(window, "g1", "f3")
    assert window.board_view.annotations
    click_square(window, "f3")
    assert not window.board_view.annotations
    assert not window.position.move_stack


def test_straight_and_optional_bent_knight_arrows(window):
    view = window.board_view
    start, end = view.square_rect(chess.G1).center(), view.square_rect(chess.F3).center()
    cell = view.geometry_values()[2]
    straight, bent = arrow_path(start, end, cell), arrow_path(start, end, cell, bend=True)
    assert straight != bent
    corner = type(start)(start.x(), end.y())
    assert bent.contains(corner) and not straight.contains(corner)
    draw_annotation(window, "g1", "f3")
    before = view.grab().toImage()
    window.cfg.ui.annotation_knight_bend = True
    assert view.grab().toImage() != before


def test_annotations_can_be_drawn_during_real_engine_search(window, qapp):
    window.cfg.engine.depth = 20
    window.cfg.engine.time_ms = 1800
    board = chess.Board()
    board.push_uci("e2e4")
    window.start_position(board)
    window.request_ai()
    events = []
    window.search.message.connect(lambda job, kind, result: events.append(kind))
    wait_until(qapp, lambda: "iteration" in events)
    draw_annotation(window, "g1", "f3")
    window.board_view.repaint()
    assert window.worker.isRunning()
    assert window.board_view.annotations
    assert not window.premoves
    assert len(window.position.move_stack) == 1
    window.cancel_search()
