from dataclasses import dataclass

import chess

from ui.mobility import premove_targets


@dataclass(frozen=True)
class PlannedMove:
    move: chess.Move
    piece: chess.Piece


class PremoveQueue:
    def __init__(self, limit):
        self.limit = limit
        self.items = []

    def __bool__(self):
        return bool(self.items)

    def clear(self):
        self.items.clear()

    def append(self, position, move):
        preview = self.preview(position)
        piece = preview.piece_at(move.from_square)
        if (
            len(self.items) >= self.limit
            or not piece
            or piece.color == position.turn
            or move.to_square not in premove_targets(preview, move.from_square)
        ):
            return False
        promotes = piece.piece_type == chess.PAWN and move.to_square // 8 in (0, 7)
        if (
            promotes
            and move.promotion not in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
            or not promotes
            and move.promotion is not None
        ):
            return False
        self.items.append(PlannedMove(move, piece))
        return True

    def take(self, board):
        if not self.items:
            return None
        plan = self.items.pop(0)
        if (
            board.piece_at(plan.move.from_square) != plan.piece
            or plan.move not in board.legal_moves
        ):
            self.clear()
            return None
        return plan.move

    def preview(self, position):
        board = position.copy(stack=False)
        for plan in self.items:
            move, piece = plan.move, plan.piece
            if board.piece_at(move.from_square) != piece:
                break
            if board.is_en_passant(move):
                board.remove_piece_at(move.to_square - (8 if piece.color else -8))
            board.remove_piece_at(move.from_square)
            if piece.piece_type == chess.KING and abs(move.to_square - move.from_square) == 2:
                rank = chess.square_rank(move.from_square)
                right = move.to_square > move.from_square
                rook = board.remove_piece_at(chess.square(7 if right else 0, rank))
                if rook:
                    board.set_piece_at(chess.square(5 if right else 3, rank), rook)
            board.set_piece_at(
                move.to_square, chess.Piece(move.promotion or piece.piece_type, piece.color)
            )
        return board
