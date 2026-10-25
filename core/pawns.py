import chess


class PawnEvaluation:
    def pawn_score(self, board, color):
        pawns = board.pieces(chess.PAWN, color)
        enemies = board.pieces(chess.PAWN, not color)
        score = isolated = 0
        for square in pawns:
            file, rank = chess.square_file(square), chess.square_rank(square)
            if not any(abs(chess.square_file(p) - file) == 1 for p in pawns):
                isolated += 1

            def ahead(p):
                return chess.square_rank(p) > rank if color else chess.square_rank(p) < rank

            if not any(abs(chess.square_file(p) - file) <= 1 and ahead(p) for p in enemies):
                distance = 7 - rank if color else rank
                score += self.cfg.passed_pawns[min(6, distance)]
        return score + self.cfg.isolated_pawns[min(8, isolated)]
