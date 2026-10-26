"""Capture the running game.py application and its actual search messages.

Run from the repository root:
    QT_QPA_PLATFORM=offscreen .venv/bin/python -B paper/scripts/capture_deployment.py

The harness observes the GUI and supplies legal demonstration moves. It leaves
the engine, worker protocol, and application source files unchanged.
"""

import json
import os
import runpy
import sys
from dataclasses import asdict
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_SCALE_FACTOR"] = "2"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
CAPTURES = PAPER / "figures/captures"
DATA = PAPER / "data"
CAPTURES.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

import chess
import chess.polyglot
from PyQt5.QtCore import QPoint, QTimer, Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ui.window import ChessWindow


def result_data(result):
    data = asdict(result)
    data["move"] = result.move.uci() if result.move else None
    return data


def board_from(moves):
    board = chess.Board()
    for move in moves:
        board.push_uci(move)
    return board


class Capture:
    def __init__(self, window):
        self.window = window
        self.phase = "overview"
        self.records = {"captures": {}, "searches": {}, "entry_point": "game.py"}
        self.captured_thinking = False
        self.failed = False

    def guard(self, callback):
        def invoke():
            try:
                callback()
            except Exception as error:
                self.failed = True
                self.records["error"] = repr(error)
                self.finish()
                raise

        return invoke

    def later(self, callback, delay=80):
        QTimer.singleShot(delay, self.guard(callback))

    def start(self):
        self.window.resize(760, 600)
        self.window.cfg.ui.player_color = "white"
        self.window.start_position(
            board_from(
                ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6",
                 "b5a4", "g8f6", "e1g1", "f8e7", "f1e1", "b7b5"]
            )
        )
        self.later(self.overview)

    def rect(self, widget):
        point = widget.mapTo(self.window, QPoint(0, 0))
        return [point.x(), point.y(), widget.width(), widget.height()]

    def snapshot(self, name, full=False):
        window = self.window
        view = window.board_view
        widget = window if full else view
        widget.repaint()
        pixmap = QPixmap(widget.width() * 2, widget.height() * 2)
        pixmap.fill(QColor(window.cfg.ui.background))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(2, 2)
        widget.render(painter)
        painter.end()
        path = CAPTURES / f"capture-{name}.png"
        assert pixmap.save(str(path))
        board = window.position
        score = window.evaluator.evaluate(board) * (1 if board.turn else -1)
        item = {
            "file": path.relative_to(PAPER).as_posix(),
            "fen": board.fen(),
            "moves": [move.uci() for move in board.move_stack],
            "size": [pixmap.width(), pixmap.height()],
            "logical_size": [widget.width(), widget.height()],
            "status": window.panel.status.text(),
            "position_estimate_white_cp": score,
            "material_balance_white_cp": (
                window.evaluator.material(board, chess.WHITE)
                - window.evaluator.material(board, chess.BLACK)
            ),
            "phase_white": window.evaluator.endgame(board, chess.BLACK),
            "phase_black": window.evaluator.endgame(board, chess.WHITE),
            "square_centers": {
                chess.square_name(square): [
                    view.square_rect(square).center().x(),
                    view.square_rect(square).center().y(),
                ]
                for square in chess.SQUARES
            },
            "board_rect": self.rect(view),
            "status_rect": self.rect(window.panel.status),
            "history_rect": self.rect(window.panel.history),
            "estimate_rect": self.rect(window.panel.evaluation),
            "clock_rect": self.rect(window.top_player.clock),
        }
        self.records["captures"][name] = item
        print(f"Captured {name}: {board.fen()}", flush=True)

    def click_move(self, source, target):
        view = self.window.board_view
        for square in (source, target):
            point = view.square_rect(chess.parse_square(square)).center().toPoint()
            QTest.mouseClick(view, Qt.LeftButton, pos=point)

    def overview(self):
        self.window.begin_selection(chess.F3)
        self.snapshot("interface", full=True)
        self.window.clear_input()
        self.phase = "opening"
        self.window.start_position(chess.Board())
        self.later(self.opening)

    def opening(self):
        self.click_move("e2", "e4")

    def iteration(self, result):
        record = self.records["searches"].setdefault(self.phase, {"iterations": []})
        record["iterations"].append(result_data(result))
        if self.phase == "tactics" and result.depth >= 2 and not self.captured_thinking:
            self.captured_thinking = True
            self.snapshot("thinking", full=True)

    def result(self, board, result):
        record = self.records["searches"].setdefault(self.phase, {"iterations": []})
        record.update(
            input_fen=board.fen(),
            input_moves=[move.uci() for move in board.move_stack],
            result=result_data(result),
            san=board.san(result.move) if result.move else None,
        )
        if self.phase == "opening":
            with chess.polyglot.open_reader(str(ROOT / "assets/openings.bin")) as reader:
                entries = list(reader.find_all(board))
            cutoff = max(entry.weight for entry in entries) * self.window.cfg.engine.book_threshold
            record["eligible_book_actions"] = [
                {"uci": entry.move.uci(), "san": board.san(entry.move), "weight": entry.weight}
                for entry in entries if entry.weight >= cutoff
            ]
        self.later(self.after_result)

    def after_result(self):
        if self.phase == "opening":
            self.snapshot("opening")
            self.phase = "tactics"
            self.window.cfg.engine.book = None
            self.window.cfg.engine.depth = 8
            self.window.cfg.engine.time_ms = 1800
            self.window.start_position(
                board_from(["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"])
            )
            self.later(self.tactics)
        elif self.phase == "tactics":
            self.snapshot("tactic-recapture")
            self.snapshot("committed", full=True)
            self.phase = "endgame"
            self.window.cfg.ui.player_color = "black"
            self.window.cfg.engine.depth = 3
            self.window.cfg.engine.time_ms = 1500
            self.window.start_position(chess.Board("8/7k/8/8/8/2K5/PPP5/8 w - - 0 1"))
        elif self.phase == "endgame":
            self.snapshot("endgame-after")
            self.finish()

    def tactics(self):
        self.snapshot("tactic-before")
        self.click_move("b5", "c6")
        self.snapshot("tactic-capture")

    def finish(self):
        (DATA / "deployment-trace.json").write_text(
            json.dumps(self.records, indent=2), encoding="utf-8"
        )
        self.window.dirty = False
        self.window.close()
        QTimer.singleShot(400, QApplication.instance().quit)


original_init = ChessWindow.__init__
original_progress = ChessWindow.search_progress
original_receive = ChessWindow.receive_move
capture = None


def observed_init(window, cfg):
    global capture
    original_init(window, cfg)
    capture = Capture(window)
    capture.later(capture.start)
    QTimer.singleShot(30000, capture.guard(capture.finish))


def observed_progress(window, generation, result):
    original_progress(window, generation, result)
    if generation == window.generation:
        capture.iteration(result)


def observed_receive(window, generation, result):
    if generation != window.generation:
        return original_receive(window, generation, result)
    before = window.position.copy(stack=True)
    original_receive(window, generation, result)
    capture.result(before, result)


ChessWindow.__init__ = observed_init
ChessWindow.search_progress = observed_progress
ChessWindow.receive_move = observed_receive
sys.argv = [
    str(ROOT / "game.py"), "ui.width=760", "ui.height=600",
    "ui.animation_ms=0", "ui.show_evaluation=true", "ui.timed=true",
    "engine.depth=4", "engine.time_ms=1800",
]
runpy.run_path(str(ROOT / "game.py"), run_name="__main__")
if capture is None or capture.failed:
    raise SystemExit(1)
assert {"opening", "tactics", "endgame"} <= capture.records["searches"].keys()
print("Capture complete; application and worker exited.")
