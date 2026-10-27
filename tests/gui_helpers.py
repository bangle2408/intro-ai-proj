from time import monotonic

import chess
from PyQt5.QtCore import QEvent, QPointF, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication


def wait_until(qapp, condition, timeout=5):
    deadline = monotonic() + timeout
    while not condition() and monotonic() < deadline:
        qapp.processEvents()
        QTest.qWait(10)
    assert condition()


def square_point(window, name):
    return window.board_view.square_rect(chess.parse_square(name)).center().toPoint()


def click_square(window, name):
    QTest.mouseClick(window.board_view, Qt.LeftButton, pos=square_point(window, name))


def move_pointer(window, point, held=True, button=Qt.LeftButton):
    view = window.board_view
    event = QMouseEvent(
        QEvent.MouseMove,
        QPointF(point),
        Qt.NoButton,
        button if held else Qt.NoButton,
        Qt.NoModifier,
    )
    QApplication.sendEvent(view, event)


def drag_piece(window, source, target):
    origin = square_point(window, source)
    destination = square_point(window, target) if isinstance(target, str) else target
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=origin)
    move_pointer(window, destination)
    QTest.mouseRelease(window.board_view, Qt.LeftButton, pos=destination)


def draw_annotation(window, source, target=None, modifiers=Qt.NoModifier):
    origin = square_point(window, source)
    destination = square_point(window, target or source)
    QTest.mousePress(window.board_view, Qt.RightButton, modifiers, pos=origin)
    move_pointer(window, destination, button=Qt.RightButton)
    QTest.mouseRelease(window.board_view, Qt.RightButton, modifiers, pos=destination)
