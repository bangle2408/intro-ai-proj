import os

import pytest

from utils.config import load_config

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def cfg():
    return load_config(["engine.book=null", "engine.depth=2", "engine.time_ms=500"])


@pytest.fixture(scope="session")
def qapp():
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


@pytest.fixture
def window(cfg, qapp):
    from ui.theme import apply_theme
    from ui.window import ChessWindow

    apply_theme(qapp, cfg.ui)
    widget = ChessWindow(cfg)
    widget.show()
    qapp.setActiveWindow(widget)
    qapp.processEvents()
    yield widget
    widget.cancel_search()
    widget.dirty = False
    widget.close()
    from PyQt5.QtCore import QEvent

    from tests.gui_helpers import wait_until

    wait_until(qapp, lambda: not widget.isVisible())
    widget.deleteLater()
    qapp.sendPostedEvents(None, QEvent.DeferredDelete)


@pytest.fixture
def waiting_window(window, monkeypatch):
    import chess

    monkeypatch.setattr(window, "request_ai", lambda: None)
    board = chess.Board()
    board.push_uci("e2e4")
    window.start_position(board)
    window.refresh()
    return window
