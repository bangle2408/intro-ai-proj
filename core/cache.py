from dataclasses import dataclass

import chess.polyglot


@dataclass(frozen=True)
class Entry:
    depth: int
    score: int
    bound: str
    move: object


class PositionCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = {}

    def clear(self):
        self.entries.clear()

    def get(self, board):
        return self.entries.get(self.key(board))

    def put(self, board, depth, score, bound, move, ply):
        if abs(score) > 99000:
            score += ply if score > 0 else -ply
        key = self.key(board)
        if key not in self.entries and len(self.entries) >= self.capacity:
            self.entries.pop(next(iter(self.entries)))
        self.entries[key] = Entry(depth, score, bound, move)

    @staticmethod
    def key(board):
        return chess.polyglot.zobrist_hash(board), board.halfmove_clock

    @staticmethod
    def score(entry, ply):
        score = entry.score
        if abs(score) > 99000:
            score -= ply if score > 0 else -ply
        return score
