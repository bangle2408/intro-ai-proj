import chess
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel

from tests.gui_helpers import click_square, draw_annotation, wait_until
from ui.preferences import PreferencesDialog
from utils.config import load_config


@pytest.mark.parametrize("name", ["light", "dark"])
def test_hydra_appearance_resolves_ui_palette(name):
    cfg = load_config([f"appearance={name}"])
    assert cfg.appearance.name == name
    assert cfg.ui.background == cfg.appearance.background
    assert cfg.ui.annotation_colors.blue == cfg.appearance.annotation_colors.blue


def test_appearance_button_preserves_game_and_drawings(window):
    window.cfg.ui.mode = "human_human"
    click_square(window, "e2")
    click_square(window, "e4")
    draw_annotation(window, "e7", "e5")
    fen, generation, dirty = window.position.fen(), window.generation, window.dirty
    before = window.board_view.grab().toImage()
    icon = window.header.new_game.icon().cacheKey()
    QTest.mouseClick(window.header.appearance, Qt.LeftButton)
    assert window.cfg.appearance.name == "light"
    assert window.cfg.ui.background == "#F6F5F1"
    assert window.header.appearance.symbol == "sun"
    assert not window.header.appearance.isChecked()
    assert window.position.fen() == fen and window.generation == generation
    assert window.dirty == dirty
    assert window.board_view.annotations == {(chess.E7, chess.E5): "yellow"}
    assert window.board_view.grab().toImage() != before
    assert window.header.new_game.icon().cacheKey() != icon
    QTest.mouseClick(window.header.appearance, Qt.LeftButton)
    assert window.cfg.appearance.name == "dark"
    assert window.header.appearance.isChecked()
    assert window.board_view.grab().toImage() == before


@pytest.mark.parametrize("name", ["dark", "light"])
def test_dialogs_and_capture_icons_follow_appearance(window, name):
    window.set_appearance(name)
    dialog = PreferencesDialog(window.cfg, window)
    assert dialog.cfg.background == window.cfg.appearance.background
    assert dialog.evaluation.accessibleName() == "Evaluation bar"
    assert "Position estimate" not in [label.text() for label in window.findChildren(QLabel)]
    dialog.show()
    QApplication.processEvents()
    assert not dialog.evaluation.grab().isNull()
    dialog.close()
    captured = window.bottom_player.captures
    captured.set_pieces([chess.Piece(chess.PAWN, False)], chess.WHITE)
    assert not captured.grab().isNull()


@pytest.mark.parametrize("size", [(760, 600), (800, 650), (1140, 860), (1440, 1000)])
@pytest.mark.parametrize("name", ["light", "dark"])
def test_bar_and_header_fit_compact_and_large_windows(window, qapp, size, name):
    window.set_appearance(name)
    window.resize(*size)
    qapp.processEvents()
    bar, board = window.evaluation_bar, window.board_view
    assert window.canvas.rect().contains(bar.geometry())
    assert bar.geometry().right() < board.geometry().left()
    assert bar.height() == board.height() - 28
    assert bar.y() == board.y() + 14
    buttons = [window.header.appearance, window.header.preferences, window.header.new_game]
    for button in buttons:
        assert window.header.rect().contains(button.geometry())
    assert all(not a.geometry().intersects(b.geometry()) for a, b in zip(buttons, buttons[1:]))


def test_theme_switch_keeps_real_ai_job_and_premove(window, qapp):
    window.cfg.engine.depth = 20
    window.cfg.engine.time_ms = 1800
    board = chess.Board()
    board.push_uci("e2e4")
    window.start_position(board)
    events = []
    window.search.message.connect(lambda job, kind, result: events.append(kind))
    window.request_ai()
    wait_until(qapp, lambda: "iteration" in events)
    click_square(window, "g1")
    click_square(window, "f3")
    job, generation = window.worker.job, window.generation
    pid = window.search.process.processId()
    QTest.mouseClick(window.header.appearance, Qt.LeftButton)
    assert window.worker.isRunning() and window.worker.job == job
    assert window.search.process.processId() == pid
    assert window.generation == generation
    assert window.premoves.items[0].move.uci() == "g1f3"
    assert len(window.position.move_stack) == 1
    window.cancel_search()
