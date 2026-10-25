import chess


class KingEvaluation:
    def king_safety(self, board, color, endgame):
        king = board.king(color)
        file, rank = chess.square_file(king), chess.square_rank(king)
        direction = 1 if color else -1
        penalty = 0
        if file <= 2 or file >= 5:
            for offset, weight in zip((-1, 0, 1), self.cfg.shield[:3]):
                col, row = file + offset, rank + direction
                if 0 <= col < 8 and 0 <= row < 8:
                    piece = board.piece_at(chess.square(col, row))
                    if piece != chess.Piece(chess.PAWN, color):
                        penalty += weight
            penalty *= penalty
        enemy_rooks = len(board.pieces(chess.ROOK, not color))
        if enemy_rooks > 1 or (enemy_rooks and board.pieces(chess.QUEEN, not color)):
            for col in range(max(0, file - 1), min(8, file + 2)):
                mask = chess.BB_FILES[col]
                if not board.pieces_mask(chess.PAWN, color) & mask:
                    penalty += 25 if col == file else 15
                    if not board.pieces_mask(chess.PAWN, not color) & mask:
                        penalty += 15 if col == file else 10
        weight = 1 - endgame
        if not board.queens:
            weight *= 0.6
        return -int(penalty * weight)

    def mop_up(self, board, color, advantage, endgame):
        if advantage <= 2 * self.values[chess.PAWN]:
            return 0
        ours, theirs = board.king(color), board.king(not color)
        distance = chess.square_manhattan_distance(ours, theirs)
        center = min(
            chess.square_manhattan_distance(theirs, p)
            for p in (chess.D4, chess.D5, chess.E4, chess.E5)
        )
        return int(((14 - distance) * 4 + center * 10) * endgame)
