import chess
import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ui.preferences import PreferencesDialog


@pytest.mark.parametrize("score", [0, -400, 400, -2000, 2000])
def test_bar_shows_white_or_black_advantage_without_numbers(window, score):
    window.cfg.ui.animation_ms = 0
    bar = window.evaluation_bar
    bar.set_position(score, False)
    assert 0 < bar.fraction < 1
    assert (bar.fraction > 0.5) == (score > 0)
    assert (bar.fraction < 0.5) == (score < 0)
    assert bar.toolTip() == ""
    assert not any(char.isdigit() for char in bar.accessibleDescription())


@pytest.mark.parametrize("result,fraction", [("1-0", 1.0), ("0-1", 0.0), ("1/2-1/2", 0.5)])
def test_game_result_sets_full_or_balanced_bar(window, result, fraction):
    window.cfg.ui.animation_ms = 0
    window.finish(result, "Game ended")
    assert window.evaluation_bar.fraction == fraction


def test_white_advantage_is_independent_of_turn_and_bar_flips_with_board(window):
    window.cfg.ui.mode = "human_human"
    window.cfg.ui.animation_ms = 0
    board = chess.Board("7k/8/8/8/8/8/3Q4/K7 w - - 0 1")
    window.start_position(board)
    bar = window.evaluation_bar
    fraction = bar.fraction
    assert fraction > 0.8
    board.turn = chess.BLACK
    window.start_position(board)
    assert bar.fraction == pytest.approx(fraction)
    before = bar.grab().toImage()
    top = max(2, round(bar.height() * (1 - fraction) / 2))
    bottom = bar.height() - top - 1
    assert before.pixelColor(6, bottom) == QColor(window.cfg.ui.evaluation_white)
    assert before.pixelColor(6, top) == QColor(window.cfg.ui.evaluation_black)
    window.flip()
    after = bar.grab().toImage()
    assert bar.fraction == pytest.approx(fraction) and bar.flipped
    assert after.pixelColor(6, top) == QColor(window.cfg.ui.evaluation_white)
    assert after.pixelColor(6, bottom) == QColor(window.cfg.ui.evaluation_black)


def test_preferences_hides_and_restores_bar_without_changing_position(window):
    fen = window.position.fen()

    def hide():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog)
        dialog.evaluation.setChecked(False)
        dialog.accept()

    QTimer.singleShot(0, hide)
    QTest.mouseClick(window.header.preferences, Qt.LeftButton)
    assert window.evaluation_bar.isHidden()
    assert window.position.fen() == fen
    window.cfg.ui.show_evaluation = True
    window.refresh()
    assert not window.evaluation_bar.isHidden()
    assert window.position.fen() == fen


def test_animation_can_reverse_smoothly_and_obeys_reduced_motion(window):
    bar = window.evaluation_bar
    bar.set_position(500, False)
    QTest.qWait(50)
    assert 0.5 < bar.fraction < bar.target
    bar.set_position(-500, False)
    QTest.qWait(200)
    assert bar.fraction == pytest.approx(bar.target) and bar.fraction < 0.5
    bar.set_position(500, False)
    window.cfg.ui.animation_ms = 0
    bar.set_position(500, False)
    assert bar.fraction == bar.target
    assert bar.animation.state() == bar.animation.Stopped
