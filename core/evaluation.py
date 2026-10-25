from types import SimpleNamespace

import chess
from omegaconf import OmegaConf

from core.pawns import PawnEvaluation
from core.safety import KingEvaluation


class Evaluation(PawnEvaluation, KingEvaluation):
    def __init__(self, cfg):
        self.cfg = SimpleNamespace(**OmegaConf.to_container(cfg, resolve=True))
        self.values = self.cfg.values
        self.tables = self.cfg.tables

    def material(self, board, color):
        return sum(
            len(board.pieces(piece, color)) * self.values[piece]
            for piece in range(chess.PAWN, chess.KING)
        )

    def endgame(self, board, color):
        non_pawns = (
            self.material(board, color) - len(board.pieces(chess.PAWN, color)) * self.values[1]
        )
        return max(0.0, 1 - non_pawns / self.cfg.endgame_material)

    def positional(self, board, color, phase):
        score = 0
        for piece, name in ((2, "knights"), (3, "bishops"), (4, "rooks"), (5, "queens")):
            score += sum(self.table(name, square, color) for square in board.pieces(piece, color))
        for square in board.pieces(chess.PAWN, color):
            score += self.blend("pawns", "pawns_end", square, color, phase)
        return score + self.blend("king_start", "king_end", board.king(color), color, phase)

    def table(self, name, square, color):
        return self.tables[name][chess.square_mirror(square) if color else square]

    def blend(self, early, late, square, color, phase):
        return int(
            self.table(early, square, color) * (1 - phase) + self.table(late, square, color) * phase
        )

    def center(self, board, color):
        score = 0
        for square in (chess.D4, chess.E4, chess.D5, chess.E5):
            piece = board.piece_at(square)
            score += self.cfg.center_occupation if piece and piece.color == color else 0
            score += self.cfg.center_attack * len(board.attackers(color, square))
        for square in (
            chess.C3,
            chess.D3,
            chess.E3,
            chess.F3,
            chess.C4,
            chess.F4,
            chess.C5,
            chess.F5,
            chess.C6,
            chess.D6,
            chess.E6,
            chess.F6,
        ):
            piece = board.piece_at(square)
            score += self.cfg.outer_occupation if piece and piece.color == color else 0
            score += self.cfg.outer_attack if board.is_attacked_by(color, square) else 0
        return score

    def evaluate(self, board):
        material = {color: self.material(board, color) for color in chess.COLORS}
        scores = {}
        for color in chess.COLORS:
            phase = self.endgame(board, not color)
            scores[color] = (
                material[color]
                + self.positional(board, color, phase)
                + self.pawn_score(board, color)
                + self.king_safety(board, color, phase)
                + self.center(board, color)
                + self.mop_up(board, color, material[color] - material[not color], phase)
            )
        score = scores[board.turn] - scores[not board.turn]
        return score - self.cfg.check_penalty if board.is_check() else score
