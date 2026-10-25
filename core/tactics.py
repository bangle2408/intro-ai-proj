from core.position import terminal_score


class SearchStopped(Exception):
    pass


class TacticalSearch:
    def quiescence(self, board, alpha, beta, ply):
        self.check_stop()
        terminal = terminal_score(board, ply)
        if terminal is not None:
            return terminal
        score = self.evaluation.evaluate(board)
        if ply >= self.limits.max_ply:
            return score
        in_check = board.is_check()
        if not in_check:
            if score >= beta:
                return score
            alpha = max(alpha, score)
        moves = [m for m in board.legal_moves if in_check or board.is_capture(m) or m.promotion]
        for move in self.ordering.ordered(board, moves, ply=ply):
            board.push(move)
            try:
                score = -self.quiescence(board, -beta, -alpha, ply + 1)
            finally:
                board.pop()
            if score >= beta:
                return score
            alpha = max(alpha, score)
        return alpha
