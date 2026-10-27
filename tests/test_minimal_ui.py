import chess
import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton

from tests.gui_helpers import click_square, drag_piece
from ui.dialogs import NewGameDialog
from ui.preferences import PreferencesDialog


def test_board_is_playable_without_start_or_pause(window):
    assert window.active
    assert not hasattr(window, "toggle_pause")
    assert not any(
        "Pause" in button.text() or "Start" in button.text()
        for button in window.findChildren(QPushButton)
    )
    assert not window.evaluation_bar.isHidden()
    assert window.top_player.clock.isHidden()
    assert window.bottom_player.clock.isHidden()
    click_square(window, "e2")
    click_square(window, "e4")
    assert window.position.peek().uci() == "e2e4"


@pytest.mark.parametrize("size", [(760, 600), (800, 650), (1140, 860), (1440, 1000)])
def test_layout_keeps_board_and_controls_inside_window(window, qapp, size):
    window.resize(*size)
    qapp.processEvents()
    canvas = window.canvas
    widgets = [
        window.header,
        window.board_view,
        window.top_player,
        window.bottom_player,
        window.panel,
    ]
    for widget in widgets:
        assert canvas.rect().contains(widget.geometry()), widget.objectName()
    assert not window.board_view.geometry().intersects(window.panel.geometry())
    assert not window.board_view.geometry().intersects(window.top_player.geometry())
    assert not window.board_view.geometry().intersects(window.bottom_player.geometry())
    assert window.board_view.width() == window.board_view.height()
    assert window.panel.history.height() >= 100


def test_new_game_dialog_replaces_current_game_without_second_prompt(window, monkeypatch):
    window.cfg.ui.mode = "human_human"
    click_square(window, "e2")
    click_square(window, "e4")
    monkeypatch.setattr(window, "confirm_discard", lambda: pytest.fail("Duplicate confirmation"))

    def choose():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, NewGameDialog)
        dialog.mode.group.button(1).click()
        dialog.time.setCurrentIndex(dialog.time.findData("300:3"))
        dialog.accept()

    QTimer.singleShot(0, choose)
    QTest.mouseClick(window.header.new_game, Qt.LeftButton)
    assert window.active and window.cfg.ui.mode == "human_human"
    assert not window.position.move_stack
    assert window.clock.enabled
    assert window.clock.active == chess.WHITE
    assert window.clock.remaining[chess.WHITE] <= 300000


def test_preferences_change_real_input_and_strength(window):
    window.cfg.ui.mode = "human_human"

    def choose():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog)
        assert dialog.depth.isHidden()
        dialog.advanced.click()
        assert not dialog.depth.isHidden()
        dialog.level.setCurrentIndex(dialog.level.findData("hard"))
        dialog.method.setCurrentIndex(dialog.method.findData("drag"))
        dialog.premoves.setChecked(False)
        dialog.motion.setChecked(False)
        dialog.evaluation.setChecked(True)
        dialog.accept()

    QTimer.singleShot(0, choose)
    QTest.mouseClick(window.header.preferences, Qt.LeftButton)
    assert window.cfg.engine.depth == 8 and window.cfg.engine.time_ms == 12000
    assert not window.cfg.ui.premoves and window.cfg.ui.animation_ms == 0
    assert not window.evaluation_bar.isHidden()
    click_square(window, "e2")
    click_square(window, "e4")
    assert not window.position.move_stack
    drag_piece(window, "e2", "e4")
    assert window.position.peek().uci() == "e2e4"


def test_history_pairs_white_and_black_and_updates_on_undo(window):
    window.cfg.ui.mode = "human_human"
    for source, target in [("e2", "e4"), ("e7", "e5"), ("g1", "f3")]:
        click_square(window, source)
        click_square(window, target)
    model = window.panel.history.moves
    assert model.rows == [["1", "e4", "e5"], ["2", "Nf3", ""]]
    window.undo()
    assert model.rows == [["1", "e4", "e5"]]
    assert window.active and window.position.turn == chess.WHITE


def test_custom_search_limit_survives_new_game_dialog(window):
    window.cfg.engine.depth = 6
    window.cfg.engine.time_ms = None
    dialog = NewGameDialog(window.cfg, window)
    assert dialog.engine_settings() == dict(depth=6, time_ms=None)
    dialog.close()


def test_save_shortcut_and_load_preserve_time_control(window, tmp_path, monkeypatch):
    window.cfg.ui.mode = "human_human"
    window.cfg.ui.base_seconds = 180
    window.cfg.ui.increment_seconds = 2
    window.cfg.ui.timed = True
    window.start_position(chess.Board())
    click_square(window, "e2")
    click_square(window, "e4")
    path = str(tmp_path / "game.chess")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (path, ""))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (path, ""))
    QTest.keyClick(window.board_view, Qt.Key_S, Qt.ControlModifier)
    assert (tmp_path / "game.chess").is_file()
    window.cfg.ui.base_seconds = 600
    window.cfg.ui.increment_seconds = 0
    window.load()
    assert window.cfg.ui.base_seconds == 180
    assert window.cfg.ui.increment_seconds == 2
    assert "3 + 2" in window.panel.summary.text()
    assert window.active


def test_more_menu_resign_and_captured_pieces_follow_orientation(window, monkeypatch):
    board = chess.Board()
    for move in ("e2e4", "d7d5", "e4d5"):
        board.push_uci(move)
    window.request_ai = lambda: None
    window.start_position(board)
    assert chess.Piece(chess.PAWN, chess.BLACK) in window.bottom_player.captures.pieces
    window.flip()
    assert chess.Piece(chess.PAWN, chess.BLACK) in window.top_player.captures.pieces
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    window.panel.resign_action.trigger()
    assert not window.active and window.result == "0-1"
    assert window.panel.status.text() == "Computer wins"


def test_history_after_resize_keeps_latest_move_visible(window, qapp):
    board = chess.Board()
    for move in ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4"):
        board.push_uci(move)
    window.request_ai = lambda: None
    window.start_position(board)
    window.resize(800, 650)
    qapp.processEvents()
    QTest.qWait(20)
    history = window.panel.history
    cell = history.visualRect(history.moves.index(*history.moves.last))
    assert history.viewport().rect().contains(cell)
