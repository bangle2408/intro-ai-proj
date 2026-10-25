from time import monotonic

from core.position import terminal_score
from core.tactics import SearchStopped, TacticalSearch


class PositionSearch(TacticalSearch):
    def check_stop(self):
        self.nodes += 1
        if self.cancelled.is_set() or monotonic() >= self.deadline:
            raise SearchStopped

    def search(self, board, depth, alpha, beta, ply=0, extensions=0):
        self.check_stop()
        terminal = terminal_score(board, ply)
        if terminal is not None:
            return terminal, None
        if depth <= 0 or ply >= self.limits.max_ply:
            return self.quiescence(board, alpha, beta, ply), None
        original_alpha = alpha
        entry = self.cache.get(board)
        repeated = board.is_repetition(2)
        if entry and entry.depth >= depth and not repeated:
            score = self.cache.score(entry, ply)
            if (
                entry.bound == "exact"
                or entry.bound == "lower"
                and score >= beta
                or entry.bound == "upper"
                and score <= alpha
            ):
                return score, entry.move
        moves = self.ordering.ordered(board, board.legal_moves, entry.move if entry else None, ply)
        best_move, best_score = None, -1000000
        in_check = board.is_check()
        for index, move in enumerate(moves):
            quiet = not board.is_capture(move) and not move.promotion
            board.push(move)
            try:
                piece = board.piece_at(move.to_square)
                extend = int(
                    extensions < self.limits.max_extensions
                    and (
                        board.is_check() or piece.piece_type == 1 and move.to_square // 8 in (1, 6)
                    )
                )
                next_depth = depth - 1 + extend
                reduce = index >= 3 and depth >= 3 and quiet and not in_check and not extend
                if reduce:
                    score, _ = self.search(
                        board, next_depth - 1, -alpha - 1, -alpha, ply + 1, extensions
                    )
                    score = -score
                if not reduce or score > alpha:
                    score, _ = self.search(
                        board, next_depth, -beta, -alpha, ply + 1, extensions + extend
                    )
                    score = -score
            finally:
                board.pop()
            if score > best_score:
                best_score, best_move = score, move
            alpha = max(alpha, score)
            if alpha >= beta:
                self.ordering.cutoff(board, move, depth, ply)
                break
        bound = (
            "upper" if best_score <= original_alpha else "lower" if best_score >= beta else "exact"
        )
        if not repeated:
            self.cache.put(board, depth, best_score, bound, best_move, ply)
        return best_score, best_move
