import logging
import sys
from threading import Lock, Thread

import chess

from core.engine import ChessEngine
from core.position import make_board
from core.time_control import think_time


class UCIEngine:
    def __init__(self, cfg, output=None):
        self.cfg = cfg
        self.engine = ChessEngine(cfg)
        self.board = chess.Board()
        self.output = output or sys.stdout
        self.lock = Lock()
        self.worker = None
        self.depth = cfg.engine.depth

    def write(self, message):
        with self.lock:
            self.output.write(message + "\n")
            self.output.flush()

    def stop(self):
        self.engine.stop()
        if self.worker:
            self.worker.join()
            self.worker = None

    def position(self, tokens):
        self.stop()
        split = tokens.index("moves") if "moves" in tokens else len(tokens)
        fen = " ".join(tokens[2:split]) if tokens[1] == "fen" else "startpos"
        self.board = make_board(fen, tokens[split + 1 :])

    @staticmethod
    def number(tokens, key, default=None):
        return int(tokens[tokens.index(key) + 1]) if key in tokens else default

    def go(self, tokens):
        self.stop()
        self.engine.cancelled.clear()
        depth = self.number(tokens, "depth", self.depth)
        depth = max(1, min(20, depth))
        budget = self.number(tokens, "movetime", self.cfg.engine.time_ms)
        side = "w" if self.board.turn else "b"
        if side + "time" in tokens:
            budget = think_time(
                self.cfg.engine,
                self.number(tokens, side + "time"),
                self.number(tokens, side + "inc", 0),
            )
        if "infinite" in tokens:
            depth = 20
            budget = None
        elif "depth" in tokens and not any(key in tokens for key in ("movetime", "wtime", "btime")):
            budget = None
        position = self.board.copy(stack=True)

        def search():
            try:
                result = self.engine.choose(position, depth, budget, self.report)
                self.write(f"bestmove {result.move.uci() if result.move else '0000'}")
            except Exception:
                logging.exception("UCI search failed")
                self.write("bestmove 0000")

        self.worker = Thread(target=search, daemon=True)
        self.worker.start()

    def report(self, result):
        if abs(result.score) > 99000:
            distance = (100000 - abs(result.score) + 1) // 2
            score = f"mate {distance if result.score > 0 else -distance}"
        else:
            score = f"cp {result.score}"
        self.write(
            f"info depth {result.depth} score {score} nodes {result.nodes} "
            f"time {result.elapsed_ms} pv {result.move.uci()}"
        )

    def handle(self, line):
        tokens = line.split()
        if not tokens:
            return True
        command = tokens[0]
        if command == "uci":
            self.write("id name MyChessBot")
            self.write("id author chess-ai-project")
            self.write(f"option name MyAI_DefaultDepth type spin default {self.depth} min 1 max 20")
            self.write("uciok")
        elif command == "isready":
            self.write("readyok")
        elif command == "setoption" and "MyAI_DefaultDepth" in tokens:
            self.depth = max(1, min(20, self.number(tokens, "value", self.depth)))
        elif command == "position":
            self.position(tokens)
        elif command == "go":
            self.go(tokens)
        elif command in {"stop", "quit", "ucinewgame"}:
            self.stop()
            if command == "ucinewgame":
                self.engine.cache.clear()
                self.board.reset()
        return command != "quit"

    def run(self, source=None):
        try:
            for line in source or sys.stdin:
                try:
                    if not self.handle(line):
                        break
                except (ValueError, IndexError) as error:
                    self.write(f"info string {error}")
        finally:
            self.stop()


def run(cfg):
    UCIEngine(cfg).run()
