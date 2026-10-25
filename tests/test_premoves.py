import chess
import pytest

from ui.mobility import premove_targets
from ui.premoves import PremoveQueue


def position(fen=None):
    board = chess.Board(fen) if fen else chess.Board()
    board.turn = chess.BLACK
    return board


def test_geometry_allows_conditional_recapture_and_ignores_blockers():
    board = position()
    assert chess.D2 in premove_targets(board, chess.D1)
    assert chess.A4 in premove_targets(board, chess.D1)
    assert chess.E1 not in premove_targets(board, chess.D1)
    assert chess.F3 in premove_targets(board, chess.G1)
    assert chess.G1 in premove_targets(board, chess.E1)
    assert chess.E4 in premove_targets(board, chess.E2)
    assert chess.D3 in premove_targets(board, chess.E2)
    assert chess.E1 not in premove_targets(board, chess.E2)


def test_queue_projects_future_pieces_without_changing_real_board():
    board, queue = position(), PremoveQueue(5)
    initial = board.fen()
    for uci in ("g1f3", "f3g5", "g5f7", "f7h8", "h8f7"):
        assert queue.append(board, chess.Move.from_uci(uci))
    assert not queue.append(board, chess.Move.from_uci("f7h6"))
    assert queue.preview(board).piece_at(chess.F7) == chess.Piece(chess.KNIGHT, chess.WHITE)
    assert board.fen() == initial
    assert not board.move_stack


def test_invalid_head_clears_entire_queue():
    board = position("3r2k1/8/8/8/8/8/8/4K1N1 b - - 0 1")
    queue = PremoveQueue(5)
    assert queue.append(board, chess.Move.from_uci("g1f3"))
    assert queue.append(board, chess.Move.from_uci("f3e5"))
    board.push_uci("d8e8")
    assert board.is_check()
    assert queue.take(board) is None
    assert not queue


@pytest.mark.parametrize("uci", ["e2e5", "e2d1q", "g1g3", "g1f3q", "e7e5"])
def test_impossible_geometry_or_wrong_color_is_rejected(uci):
    queue = PremoveQueue(5)
    assert not queue.append(position(), chess.Move.from_uci(uci))


def test_promotion_and_castling_preview():
    board = position("7k/P7/8/8/8/8/8/4K2R b K - 0 1")
    queue = PremoveQueue(5)
    assert queue.append(board, chess.Move.from_uci("a7a8n"))
    assert queue.append(board, chess.Move.from_uci("e1g1"))
    preview = queue.preview(board)
    assert preview.piece_at(chess.A8) == chess.Piece(chess.KNIGHT, chess.WHITE)
    assert preview.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert preview.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)
    assert board.piece_at(chess.E1) == chess.Piece(chess.KING, chess.WHITE)
