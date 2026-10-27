import chess
import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest

from tests.gui_helpers import click_square, draw_annotation, move_pointer, square_point


@pytest.mark.parametrize(
    "target,modifier,color",
    [
        ("e4", Qt.NoModifier, "yellow"),
        ("e4", Qt.ControlModifier, "red"),
        ("e4", Qt.AltModifier, "blue"),
        ("e4", Qt.ShiftModifier, "green"),
        ("e2", Qt.NoModifier, "red"),
        ("e2", Qt.ControlModifier, "yellow"),
        ("e2", Qt.AltModifier, "blue"),
        ("e2", Qt.ShiftModifier, "green"),
    ],
)
def test_right_mouse_draws_arrow_or_circle_without_moving(window, target, modifier, color):
    draw_annotation(window, "e2", target, modifier)
    assert window.board_view.annotations == {(chess.E2, chess.parse_square(target)): color}
    assert not window.position.move_stack
    assert not window.dirty
    assert window.board_view.gesture is None


def test_preview_follows_squares_and_commits_only_on_release(window):
    view = window.board_view
    QTest.mousePress(view, Qt.RightButton, pos=square_point(window, "g1"))
    move_pointer(window, square_point(window, "f3"), button=Qt.RightButton)
    assert view.drawing.source == chess.G1 and view.drawing.target == chess.F3
    assert not view.annotations
    assert view.grab().toImage() != view.surface.toImage()
    QTest.mouseRelease(view, Qt.RightButton, pos=square_point(window, "f3"))
    assert view.drawing is None
    assert view.annotations == {(chess.G1, chess.F3): "yellow"}


def test_redraw_toggles_one_shape_and_new_color_replaces_it(window):
    draw_annotation(window, "e2", "e4")
    draw_annotation(window, "d4")
    draw_annotation(window, "e2", "e4", Qt.AltModifier)
    assert window.board_view.annotations == {
        (chess.E2, chess.E4): "blue",
        (chess.D4, chess.D4): "red",
    }
    draw_annotation(window, "e2", "e4", Qt.AltModifier)
    assert window.board_view.annotations == {(chess.D4, chess.D4): "red"}
    draw_annotation(window, "d4")
    assert not window.board_view.annotations


def test_fast_right_drag_checks_release_even_without_motion_events(window):
    QTest.mousePress(window.board_view, Qt.RightButton, pos=square_point(window, "a1"))
    QTest.mouseRelease(window.board_view, Qt.RightButton, pos=square_point(window, "h6"))
    assert window.board_view.annotations == {(chess.A1, chess.H6): "yellow"}


def test_right_drag_outside_board_cancels_only_draft(window):
    draw_annotation(window, "d4")
    QTest.mousePress(window.board_view, Qt.RightButton, pos=square_point(window, "a1"))
    move_pointer(window, QPoint(-20, -20), button=Qt.RightButton)
    assert window.board_view.drawing.target is None
    QTest.mouseRelease(window.board_view, Qt.RightButton, pos=QPoint(-20, -20))
    assert window.board_view.annotations == {(chess.D4, chess.D4): "red"}
    assert window.board_view.drawing is None


def test_drawing_clears_old_selection_so_erasing_cannot_play_a_move(window):
    click_square(window, "e2")
    draw_annotation(window, "d2", "d4")
    assert window.board_view.selected is None
    click_square(window, "e4")
    assert not window.position.move_stack
    assert not window.board_view.annotations
    click_square(window, "e2")
    click_square(window, "e4")
    assert window.position.peek().uci() == "e2e4"


def test_annotations_reproject_when_flipped_or_resized(window, qapp):
    draw_annotation(window, "b1", "c3")
    before = window.board_view.grab().toImage()
    window.flip()
    window.resize(1140, 860)
    qapp.processEvents()
    assert window.board_view.annotations == {(chess.B1, chess.C3): "yellow"}
    assert window.board_view.grab().toImage() != before
    draw_annotation(window, "b1", "c3")
    assert not window.board_view.annotations


@pytest.mark.parametrize("modifier", [Qt.NoModifier, Qt.ShiftModifier, Qt.AltModifier])
def test_drawing_preview_reuses_static_board_surface(window, monkeypatch, modifier):
    view = window.board_view
    draw_annotation(window, "e2", "e4", modifier)
    QTest.mousePress(view, Qt.RightButton, pos=square_point(window, "b1"))
    view.grab()
    surface = view.surface
    monkeypatch.setattr(view, "paint_board", lambda *_: pytest.fail("Repainted stationary board"))
    for square in ("c3", "d4", "h8", "b1"):
        move_pointer(window, square_point(window, square), button=Qt.RightButton)
        view.grab()
        assert view.surface is surface
    QTest.mouseRelease(view, Qt.RightButton, pos=square_point(window, "c3"))
