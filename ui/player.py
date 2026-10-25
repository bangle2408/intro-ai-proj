from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.pieces import CapturedPieces


class PlayerRow(QWidget):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.color = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.dot = QLabel()
        self.dot.setFixedSize(12, 12)
        layout.addWidget(self.dot)
        identity = QVBoxLayout()
        identity.setSpacing(2)
        self.name = QLabel()
        self.name.setObjectName("playerName")
        self.captures = CapturedPieces(cfg)
        identity.addWidget(self.name)
        identity.addWidget(self.captures)
        layout.addLayout(identity, 1)
        self.clock = QLabel()
        self.clock.setObjectName("playerClock")
        self.clock.setAlignment(Qt.AlignCenter)
        self.clock.setMinimumWidth(106)
        layout.addWidget(self.clock)
        self.cfg = cfg

    def display(self, color, name, time, active):
        if self.color != color:
            fill = self.cfg.white_piece if color else self.cfg.black_piece
            self.dot.setStyleSheet(
                f"background: {fill}; border: 1px solid {self.cfg.text}; border-radius: 6px;"
            )
            self.color = color
        self.name.setText(name)
        self.name.setAccessibleName(f"{name}, {'White' if color else 'Black'}")
        self.clock.setText(time)
        self.clock.setVisible(bool(time))
        if self.clock.property("active") != active:
            self.clock.setProperty("active", active)
            self.clock.style().unpolish(self.clock)
            self.clock.style().polish(self.clock)

    def set_captures(self, pieces):
        self.captures.set_pieces(pieces, self.color)
