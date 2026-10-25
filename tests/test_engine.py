from time import monotonic

import chess
import pytest

from core.cache import PositionCache
from core.engine import ChessEngine
from core.ordering import MoveOrdering
from core.position import make_board
from utils.config import load_config


def test_search_preserves_position_and_history(cfg):
    board = make_board(moves=["e2e4", "e7e5", "g1f3"])
    initial = board.fen(), list(board.move_stack)
    result = ChessEngine(cfg).choose(board, time_ms=300)
    assert result.move in board.legal_moves
    assert (board.fen(), board.move_stack) == initial
    assert result.depth >= 1


def test_finds_mate_in_one(cfg):
    board = make_board("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1")
    result = ChessEngine(cfg).choose(board, depth=2, time_ms=1000)
    board.push(result.move)
    assert board.is_checkmate()
    assert result.score > 99000


@pytest.mark.parametrize(
    "fen",
    [
        "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1",
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
        "7k/8/6K1/8/8/8/8/8 w - - 0 1",
    ],
)
def test_no_move_when_game_finished(cfg, fen):
    assert ChessEngine(cfg).choose(make_board(fen)).move is None


def test_threefold_requires_three_occurrences(cfg):
    board = chess.Board()
    cycle = ["g1f3", "g8f6", "f3g1", "f6g8"]
    for move in cycle:
        board.push_uci(move)
    assert ChessEngine(cfg).choose(board, time_ms=100).move in board.legal_moves
    for move in cycle:
        board.push_uci(move)
    assert ChessEngine(cfg).choose(board).move is None


def test_quiescence_searches_quiet_check_evasion(cfg):
    board = make_board("8/8/8/8/8/1k6/r7/K7 w - - 0 1")
    assert list(board.legal_moves) == [chess.Move.from_uci("a1b1")]
    engine = ChessEngine(cfg)
    engine.nodes, engine.deadline = 0, float("inf")
    engine.ordering = MoveOrdering(engine.evaluation.values)
    engine.evaluation.evaluate = lambda _: 123
    assert engine.quiescence(board, -1000, 1000, 0) == -123
    assert board.turn == chess.WHITE


def test_timeout_and_cancellation_return_legal_fallback(cfg):
    engine, board = ChessEngine(cfg), chess.Board()
    started = monotonic()
    result = engine.choose(board, depth=20, time_ms=1)
    assert result.move in board.legal_moves
    assert monotonic() - started < 1
    engine.stop()
    result = engine.choose(board, depth=20)
    assert result.move in board.legal_moves
    assert result.depth == 0


def test_book_is_optional_and_legal():
    engine = ChessEngine(load_config())
    result = engine.choose(chess.Board())
    assert result.source == "book"
    assert result.move in chess.Board().legal_moves


def test_cache_bounds_and_mate_distance():
    cache, board = PositionCache(1), chess.Board()
    cache.put(board, 3, 99997, "exact", chess.Move.from_uci("e2e4"), 2)
    assert cache.score(cache.get(board), 5) == 99994
    board.push_uci("e2e4")
    cache.put(board, 1, -1, "lower", None, 0)
    assert len(cache.entries) == 1
    assert cache.get(board).score == -1


def test_evaluation_symmetry(cfg):
    engine = ChessEngine(cfg)
    board = make_board(moves=["e2e4", "d7d5", "e4d5"])
    assert engine.evaluation.evaluate(board) == engine.evaluation.evaluate(board.mirror())


def test_unlimited_budget_completes_requested_depth(cfg):
    result = ChessEngine(cfg).choose(chess.Board(), depth=2, time_ms=None)
    assert result.depth == 2
