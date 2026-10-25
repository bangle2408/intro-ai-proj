import sys

from PyQt5.QtWidgets import QApplication

from ui.theme import apply_theme
from ui.window import ChessWindow


def run(cfg):
    app = QApplication.instance() or QApplication([sys.argv[0]])
    apply_theme(app, cfg.ui)
    window = ChessWindow(cfg)
    window.show()
    app.exec_()
