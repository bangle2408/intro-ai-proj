import random

import chess.polyglot

from utils.config import project_path


class OpeningBook:
    def __init__(self, cfg):
        self.cfg = cfg
        self.path = project_path(cfg.book) if cfg.book else None
        if self.path and not self.path.is_file():
            raise FileNotFoundError(f"Opening book not found: {self.path}")

    def choose(self, board):
        if not self.path or board.ply() >= self.cfg.book_plies:
            return None
        with chess.polyglot.open_reader(self.path) as reader:
            entries = list(reader.find_all(board))
        if not entries:
            return None
        threshold = max(e.weight for e in entries) * self.cfg.book_threshold
        return random.choice([e.move for e in entries if e.weight >= threshold])
