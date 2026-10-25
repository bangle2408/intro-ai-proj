from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QVBoxLayout, QWidget

from ui.history import MoveHistory
from ui.widgets import ActionButton


def divider():
    line = QFrame()
    line.setObjectName("divider")
    line.setFixedHeight(1)
    return line


class ControlPanel(QWidget):
    def __init__(self, cfg, actions, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 6)
        layout.setSpacing(16)
        self.heading = QLabel("Your game")
        self.heading.setObjectName("title")
        layout.addWidget(self.heading)
        self.summary = QLabel()
        self.summary.setObjectName("muted")
        layout.addWidget(self.summary)
        layout.addSpacing(12)
        self.status = QLabel()
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.subtitle = QLabel()
        self.subtitle.setObjectName("muted")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.subtitle)
        layout.addSpacing(8)
        layout.addWidget(divider())
        label = QLabel("MOVES")
        label.setObjectName("section")
        layout.addWidget(label)
        self.history = MoveHistory(cfg.ui)
        layout.addWidget(self.history, 1)
        self.premove_status = QLabel()
        self.premove_status.setObjectName("muted")
        self.premove_status.setWordWrap(True)
        layout.addWidget(self.premove_status)
        self.evaluation = QLabel()
        self.evaluation.setObjectName("muted")
        layout.addWidget(self.evaluation)
        layout.addWidget(divider())
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        self.buttons = {}
        for title, action, symbol in [
            ("Undo", actions.undo, "undo"),
            ("Flip", actions.flip, "flip"),
        ]:
            button = ActionButton(title, action, cfg.ui, symbol)
            self.buttons[title] = button
            toolbar.addWidget(button)
        toolbar.addStretch()
        more = ActionButton("More", None, cfg.ui, "more")
        more.setText("")
        more.setFixedWidth(40)
        self.menu = QMenu(more)
        for title, action, shortcut in [
            ("Load game", actions.load, "Ctrl+O"),
            ("Save game", actions.save, "Ctrl+S"),
        ]:
            item = self.menu.addAction(title, action)
            item.setShortcut(shortcut)
            actions.addAction(item)
        self.menu.addSeparator()
        self.resign_action = self.menu.addAction("Resign", actions.resign)
        more.setMenu(self.menu)
        toolbar.addWidget(more)
        layout.addLayout(toolbar)
