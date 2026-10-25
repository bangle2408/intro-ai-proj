import os
from time import perf_counter

import chess
import pytest
from PyQt5.QtCore import QEvent, QProcess

from tests.gui_helpers import wait_until
from ui.engine_process import EngineProcess


@pytest.fixture
def service(cfg, qapp):
    process = EngineProcess(cfg)
    yield process
    process.shutdown()
    wait_until(qapp, lambda: not process.isRunning())
    process.deleteLater()
    qapp.sendPostedEvents(None, QEvent.DeferredDelete)


def messages(service):
    received = []
    service.message.connect(lambda job, kind, value: received.append((job, kind, value)))
    return received


def test_search_runs_in_reused_separate_process(service, qapp):
    received = messages(service)
    board = chess.Board()
    first = service.submit(board, 2, 500)
    wait_until(qapp, lambda: any(job == first and kind == "result" for job, kind, _ in received))
    pid = service.process.processId()
    assert pid and pid != os.getpid()
    assert received[-1][2].move in board.legal_moves
    board.push_uci("e2e4")
    second = service.submit(board, 2, 500)
    wait_until(qapp, lambda: any(job == second and kind == "result" for job, kind, _ in received))
    assert service.process.processId() == pid
    assert received[-1][2].move in board.legal_moves


def test_cancel_is_nonblocking_and_old_results_are_discarded(service, qapp):
    received = messages(service)
    first = service.submit(chess.Board(), 20, None)
    wait_until(qapp, lambda: any(kind == "iteration" for _, kind, _ in received))
    started = perf_counter()
    service.cancel(first)
    assert perf_counter() - started < 0.1
    second = service.submit(chess.Board(), 1, 500)
    wait_until(qapp, lambda: any(job == second and kind == "result" for job, kind, _ in received))
    assert not any(job == first and kind == "result" for job, kind, _ in received)


def test_cancellation_before_process_start_does_not_block_new_job(service, qapp):
    received = messages(service)
    first = service.submit(chess.Board(), 20, None)
    service.cancel(first)
    second = service.submit(chess.Board(), 1, 500)
    wait_until(qapp, lambda: any(job == second and kind == "result" for job, kind, _ in received))
    assert not any(job == first and kind == "result" for job, kind, _ in received)


def test_process_failure_is_reported_and_next_request_can_restart(service, qapp):
    received = messages(service)
    first = service.submit(chess.Board(), 20, None)
    wait_until(qapp, lambda: any(kind == "iteration" for _, kind, _ in received))
    service.process.kill()
    wait_until(qapp, lambda: any(job == first and kind == "failure" for job, kind, _ in received))
    assert service.process.state() == QProcess.NotRunning
    second = service.submit(chess.Board(), 1, 500)
    wait_until(qapp, lambda: any(job == second and kind == "result" for job, kind, _ in received))


def test_settings_error_does_not_poison_next_request(service, cfg, qapp):
    received = messages(service)
    cfg.engine.book = "missing-book.bin"
    first = service.submit(chess.Board(), 1, 500)
    wait_until(qapp, lambda: any(job == first and kind == "failure" for job, kind, _ in received))
    cfg.engine.book = None
    second = service.submit(chess.Board(), 1, 500)
    wait_until(qapp, lambda: any(job == second and kind == "result" for job, kind, _ in received))


def test_whole_position_history_reaches_worker(service, qapp):
    received = messages(service)
    board = chess.Board()
    for move in ["g1f3", "g8f6", "f3g1", "f6g8"] * 2:
        board.push_uci(move)
    job = service.submit(board, 2, 500)
    wait_until(qapp, lambda: any(j == job and kind == "result" for j, kind, _ in received))
    assert received[-1][2].move is None
    assert received[-1][2].source == "terminal"
