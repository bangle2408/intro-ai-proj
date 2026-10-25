from collections import defaultdict

import chess


class MoveOrdering:
    def __init__(self, values):
        self.values = values
        self.killers = defaultdict(list)
        self.history = defaultdict(int)

    def ordered(self, board, moves, preferred=None, ply=0):
        def score(move):
            if move == preferred:
                return 10000000
            if board.is_capture(move):
                victim = board.piece_type_at(move.to_square) or chess.PAWN
                attacker = board.piece_type_at(move.from_square)
                return 1000000 + 10 * self.values[victim] - self.values[attacker]
            bonus = 800000 if move.promotion else 0
            bonus += 500000 if move in self.killers[ply] else 0
            return bonus + self.history[(board.turn, move)]

        return sorted(moves, key=score, reverse=True)

    def cutoff(self, board, move, depth, ply):
        if board.is_capture(move) or move.promotion:
            return
        killers = self.killers[ply]
        if move not in killers:
            self.killers[ply] = [move, *killers[:1]]
        self.history[(board.turn, move)] += depth * depth
