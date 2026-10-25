import subprocess
import sys

import chess
import chess.engine

from utils.config import ROOT


def command(*overrides):
    return [sys.executable, str(ROOT / "game.py"), "mode=uci", "engine.book=null", *overrides]


def test_handshake_and_clean_stdout():
    result = subprocess.run(
        command(), input="uci\nisready\nquit\n", text=True, capture_output=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert "uciok" in result.stdout and "readyok" in result.stdout
    assert all(
        line.startswith(("id ", "option ", "uciok", "readyok"))
        for line in result.stdout.splitlines()
    )


def test_uci_client_plays_from_history_and_reports_search():
    board = chess.Board()
    board.push_uci("e2e4")
    with chess.engine.SimpleEngine.popen_uci(command()) as engine:
        engine.configure({"MyAI_DefaultDepth": 2})
        result = engine.play(board, chess.engine.Limit(time=0.2), info=chess.engine.INFO_ALL)
        assert result.move in board.legal_moves
        assert result.info["depth"] >= 1
        engine.ping()


def test_stop_interrupts_infinite_search():
    with chess.engine.SimpleEngine.popen_uci(command("engine.depth=20")) as engine:
        with engine.analysis(chess.Board()) as analysis:
            first = analysis.get()
            assert first["depth"] >= 1
            analysis.stop()
            best = analysis.wait()
            assert best.move in chess.Board().legal_moves
        engine.ping()


def test_terminal_position_returns_null_move():
    board = chess.Board("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
    with chess.engine.SimpleEngine.popen_uci(command()) as engine:
        assert not engine.play(board, chess.engine.Limit(depth=1)).move
