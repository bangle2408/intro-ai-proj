import json

import chess
import pytest

from core.position import make_board
from utils.persistence import load_game, save_game


def test_save_roundtrip_preserves_custom_root_and_history(cfg, tmp_path):
    board = make_board("7k/8/6K1/8/8/8/4P3/8 w - - 0 1", ["e2e4", "h8g8"])
    path = tmp_path / "game.chess"
    clock = dict(enabled=True, white_time_ms=12345, black_time_ms=67890)
    save_game(path, board, cfg.ui, clock, flipped=True)
    restored, data = load_game(path)
    assert restored.fen() == board.fen()
    assert restored.move_stack == board.move_stack
    assert restored.root().fen() == board.root().fen()
    assert data["timer_settings"] == clock
    assert data["board_flipped"] is True


def test_legacy_save_is_supported(tmp_path):
    board = make_board(moves=["e2e4", "e7e5"])
    path = tmp_path / "old.chess"
    path.write_text(
        json.dumps(
            dict(version="2.0", fen=board.fen(), move_history=["e2e4", "e7e5"], mode="human_ai")
        )
    )
    restored, _ = load_game(path)
    assert restored.move_stack == board.move_stack


def test_corrupt_save_is_rejected(tmp_path):
    path = tmp_path / "bad.chess"
    path.write_text(json.dumps(dict(fen=chess.STARTING_FEN, move_history=["e2e4"])))
    with pytest.raises(ValueError, match="history"):
        load_game(path)
