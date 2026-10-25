from time import monotonic
from types import SimpleNamespace

from omegaconf import OmegaConf

from core.base import BaseEngine, SearchResult
from core.book import OpeningBook
from core.cache import PositionCache
from core.evaluation import Evaluation
from core.ordering import MoveOrdering
from core.position import make_board, terminal_score
from core.search import PositionSearch
from core.tactics import SearchStopped


class ChessEngine(PositionSearch, BaseEngine):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.limits = SimpleNamespace(**OmegaConf.to_container(cfg.engine, resolve=True))
        self.evaluation = Evaluation(cfg.evaluation)
        self.book = OpeningBook(self.limits)
        self.cache = PositionCache(self.limits.hash_entries)

    def choose(self, board, depth=None, time_ms=None, on_iteration=None):
        started = monotonic()
        self.nodes = 0
        self.deadline = float("inf") if time_ms is None else started + time_ms / 1000
        self.ordering = MoveOrdering(self.evaluation.values)
        position = board.copy(stack=True)
        terminal = terminal_score(position)
        if terminal is not None:
            return SearchResult(None, terminal, source="terminal")
        book_move = self.book.choose(position)
        if book_move and not self.cancelled.is_set():
            return SearchResult(book_move, source="book")
        result = SearchResult(next(iter(position.legal_moves)))
        for current_depth in range(1, (depth or self.limits.depth) + 1):
            try:
                score, move = self.search(position, current_depth, -1000000, 1000000)
            except SearchStopped:
                break
            if move:
                result = SearchResult(
                    move, score, current_depth, self.nodes, int((monotonic() - started) * 1000)
                )
            if on_iteration:
                on_iteration(result)
            if abs(score) > 99000:
                break
        return SearchResult(
            result.move,
            result.score,
            result.depth,
            self.nodes,
            int((monotonic() - started) * 1000),
            result.source,
        )


def run(cfg):
    board = make_board(cfg.position, cfg.moves)
    result = ChessEngine(cfg).choose(board, time_ms=cfg.engine.time_ms)
    print(result.move.uci() if result.move else "0000")
