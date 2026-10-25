from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest

from tests.gui_helpers import move_pointer, square_point


def test_board_has_no_hover_tooltip(window):
    assert window.board_view.toolTip() == ""


def test_drag_reuses_stationary_board_render(waiting_window, monkeypatch):
    window = waiting_window
    view = window.board_view
    paints = []
    original = view.paint_board

    def paint(painter):
        paints.append(1)
        original(painter)

    monkeypatch.setattr(view, "paint_board", paint)
    QTest.mousePress(view, Qt.LeftButton, pos=square_point(window, "g1"))
    point = square_point(window, "f3")
    move_pointer(window, point)
    view.grab()
    count = len(paints)
    assert count > 0
    for offset in range(1, 10):
        move_pointer(window, point + QPoint(offset, 0))
        view.grab()
    assert len(paints) == count
    cached = view.grab().toImage()
    view.invalidate_board()
    assert view.grab().toImage() == cached


def test_orientation_invalidates_cached_board(window):
    view = window.board_view
    before = view.grab().toImage()
    window.flip()
    assert view.grab().toImage() != before
