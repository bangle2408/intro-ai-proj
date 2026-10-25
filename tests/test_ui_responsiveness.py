from time import perf_counter

import chess
from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtTest import QTest

from tests.gui_helpers import move_pointer, square_point, wait_until


def test_drag_and_heartbeat_continue_during_cpu_search(window, qapp):
    window.cfg.engine.depth = 20
    window.cfg.engine.time_ms = 1800
    board = chess.Board()
    board.push_uci("e2e4")
    window.start_position(board)
    iterations = []
    window.search.message.connect(lambda job, kind, value: iterations.append(kind))
    window.request_ai()
    wait_until(qapp, lambda: "iteration" in iterations)
    QTest.mousePress(window.board_view, Qt.LeftButton, pos=square_point(window, "g1"))
    target = square_point(window, "f3")
    ticks = []

    def tick():
        ticks.append(perf_counter())
        move_pointer(window, target + QPoint(len(ticks) % 8, 0))
        window.board_view.repaint()

    timer = QTimer(window)
    timer.setTimerType(Qt.PreciseTimer)
    timer.setInterval(16)
    timer.timeout.connect(tick)
    timer.start()
    QTest.qWait(350)
    timer.stop()
    assert window.worker.isRunning()
    assert len(ticks) >= 10
    assert max(b - a for a, b in zip(ticks, ticks[1:])) < 0.15
    assert window.board_view.gesture.dragging
    started = perf_counter()
    window.cancel_search()
    assert perf_counter() - started < 0.1
    assert window.worker is None
    assert window.board_view.gesture is None
