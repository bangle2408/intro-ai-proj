import chess
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from tests.gui_helpers import click_square, wait_until
from ui.dialogs import NewGameDialog
from ui.preferences import PreferencesDialog


def test_human_move_ai_reply_and_undo(window, qapp):
    click_square(window, "e2")
    click_square(window, "e4")
    wait_until(qapp, lambda: len(window.position.move_stack) == 2 and not window.worker)
    assert window.position.move_stack[0].uci() == "e2e4"
    assert len(window.panel.history.moves.moves) == 2
    window.undo()
    assert window.position.fen() == chess.STARTING_FEN
    assert window.active


def test_two_players_and_flip(window):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    window.flip()
    click_square(window, "e2")
    click_square(window, "e4")
    click_square(window, "e7")
    click_square(window, "e5")
    assert [m.uci() for m in window.position.move_stack] == ["e2e4", "e7e5"]
    assert window.worker is None


def test_ai_vs_ai_can_be_replaced(window, qapp):
    window.cfg.ui.mode = "ai_ai"
    window.request_ai()
    wait_until(qapp, lambda: len(window.position.move_stack) >= 2)
    window.cancel_search()
    window.cfg.ui.mode = "human_human"
    window.start_position(chess.Board())
    QTest.qWait(150)
    qapp.processEvents()
    assert window.active and window.worker is None
    assert not window.position.move_stack


def test_save_load_through_ui(window, tmp_path, monkeypatch):
    window.cfg.ui.mode = "human_human"
    window.refresh()
    click_square(window, "e2")
    click_square(window, "e4")
    path = str(tmp_path / "game.chess")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (path, ""))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (path, ""))
    window.save()
    assert not window.dirty
    window.start_position(chess.Board())
    window.load()
    assert window.position.peek().uci() == "e2e4"
    assert window.active


def test_clock_increment_and_timeout(window):
    window.cfg.ui.timed = True
    window.cfg.ui.base_seconds = 1
    window.cfg.ui.increment_seconds = 2
    window.cfg.ui.mode = "human_human"
    window.start_position(chess.Board())
    window.refresh()
    click_square(window, "e2")
    click_square(window, "e4")
    assert 2800 <= window.clock.remaining[chess.WHITE] <= 3000
    window.clock.remaining[chess.BLACK] = 0
    window.clock.tick()
    assert window.result == "1-0"
    assert not window.active


def test_dialog_difficulty_and_render(window, tmp_path):
    dialog = NewGameDialog(window.cfg, window)
    assert dialog.settings()["mode"] == "human_ai"
    dialog.close()
    settings = PreferencesDialog(window.cfg, window)
    settings.level.setCurrentIndex(settings.level.findData("hard"))
    assert settings.settings()["engine"]["depth"] == 8
    assert settings.settings()["engine"]["time_ms"] == 12000
    settings.close()
    assert window.grab().save(str(tmp_path / "board.png"))


def test_resignation_stops_search(window, monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    window.resign()
    assert window.result == "0-1"
    assert not window.active and window.worker is None


def test_black_player_starts_after_white_ai(window, qapp):
    window.cfg.ui.player_color = "black"
    window.start_position(chess.Board())
    window.refresh()
    wait_until(qapp, lambda: len(window.position.move_stack) == 1 and not window.worker)
    assert window.position.turn == chess.BLACK
    assert window.board_view.flipped


def test_castling_and_en_passant(window):
    window.cfg.ui.mode = "human_human"
    board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    window.start_position(board)
    window.refresh()
    click_square(window, "e1")
    click_square(window, "g1")
    assert window.position.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)
    board = chess.Board()
    for move in ("e2e4", "a7a6", "e4e5", "d7d5"):
        board.push_uci(move)
    window.start_position(board)
    window.refresh()
    click_square(window, "e5")
    click_square(window, "d6")
    assert window.position.piece_at(chess.D5) is None
    assert chess.Piece(chess.PAWN, chess.BLACK) in window.bottom_player.captures.pieces
