from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

from ui.widgets import ActionButton


class Header(QWidget):
    def __init__(self, cfg, actions):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        brand = QLabel("chess.")
        brand.setObjectName("brand")
        layout.addWidget(brand)
        layout.addStretch()
        self.preferences = ActionButton("Preferences", actions.edit_preferences, cfg, "settings")
        self.new_game = ActionButton("New game", actions.new_game, cfg, "plus", primary=True)
        self.new_game.setShortcut("Ctrl+N")
        layout.addWidget(self.preferences)
        layout.addWidget(self.new_game)


class MatchCanvas(QWidget):
    def __init__(self, cfg, header, board, top, bottom, panel):
        super().__init__()
        self.setObjectName("canvas")
        self.cfg = cfg
        self.header, self.board = header, board
        self.top, self.bottom, self.panel = top, bottom, panel
        for widget in (header, board, top, bottom, panel):
            widget.setParent(self)
        self.setMinimumSize(760, 600)

    def resizeEvent(self, event):
        compact = self.height() < 740
        margin, gap, header_height, row = (24, 24, 48, 48) if compact else (32, 32, 48, 52)
        section_gap = 16 if compact else 24
        side = min(self.cfg.sidebar_width, max(236, self.width() // 4))
        available_height = self.height() - margin * 2 - header_height - section_gap
        edge = min(
            available_height - row * 2 - 16,
            self.width() - margin * 2 - gap - side,
            self.cfg.board_max_size,
        )
        edge = max(320, edge)
        width, height = edge + gap + side, edge + row * 2 + 16
        x = (self.width() - width) // 2
        y = max(16, (self.height() - height - header_height - section_gap) // 2)
        body_y = y + header_height + section_gap
        self.header.setGeometry(x, y, width, header_height)
        self.top.setGeometry(x + 14, body_y, edge - 28, row)
        self.board.setGeometry(x, body_y + row + 8, edge, edge)
        self.bottom.setGeometry(x + 14, body_y + row + 16 + edge, edge - 28, row)
        self.panel.setGeometry(x + edge + gap, body_y, side, height)
        super().resizeEvent(event)
