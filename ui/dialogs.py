import chess
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ui.pieces import piece_icon
from ui.widgets import Choice, Segments, Toggle


class BaseDialog(QDialog):
    def __init__(self, title, cfg, parent=None, subtitle=""):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumWidth(460)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 28, 28, 24)
        self.layout.setSpacing(20)
        heading = QLabel(title)
        heading.setObjectName("title")
        self.layout.addWidget(heading)
        if subtitle:
            caption = QLabel(subtitle)
            caption.setObjectName("muted")
            caption.setWordWrap(True)
            self.layout.addWidget(caption)
        self.fields = QFormLayout()
        self.fields.setVerticalSpacing(14)
        self.fields.setHorizontalSpacing(24)
        self.fields.setLabelAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.layout.addLayout(self.fields)

    def add_buttons(self, title="Apply"):
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setMinimumHeight(40)
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        primary = QPushButton(title)
        primary.setMinimumHeight(40)
        primary.setObjectName("primary")
        primary.setDefault(True)
        primary.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(primary)
        self.layout.addLayout(buttons)

    def combo(self, title, choices, current):
        field = Choice(self.cfg)
        for label, value in choices:
            field.addItem(label, value)
        field.setCurrentIndex(max(0, field.findData(current)))
        field.setAccessibleName(title)
        self.fields.addRow(title, field)
        return field

    def number(self, title, minimum, maximum, value):
        field = QSpinBox()
        field.setRange(minimum, maximum)
        field.setValue(value)
        field.setButtonSymbols(QSpinBox.NoButtons)
        field.setMinimumHeight(40)
        field.setAccessibleName(title)
        self.fields.addRow(title, field)
        return field

    def toggle(self, title, value):
        field = Toggle(title, value, self.cfg)
        self.fields.addRow(title, field)
        return field


class NewGameDialog(BaseDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(
            "New game",
            cfg.ui,
            parent,
            "Choose your game. Starting a new one replaces the current game.",
        )
        self.mode = Segments(
            [("Computer", "human_ai"), ("Two players", "human_human"), ("Watch", "ai_ai")],
            cfg.ui.mode,
        )
        self.fields.addRow("Play", self.mode)
        self.color = Segments([("White", "white"), ("Black", "black")], cfg.ui.player_color)
        self.fields.addRow("Your side", self.color)
        self.level = self.combo(
            "Computer",
            [("Easy", "easy"), ("Standard", "default"), ("Strong", "hard")],
            level_for_depth(cfg.engine.depth),
        )
        self.original_engine = dict(depth=cfg.engine.depth, time_ms=cfg.engine.time_ms)
        self.level_changed = False
        self.level.currentIndexChanged.connect(self.mark_level_changed)
        self.time = self.combo(
            "Clock",
            [
                ("No clock", "none"),
                ("3 + 2", "180:2"),
                ("5 + 3", "300:3"),
                ("10 + 0", "600:0"),
                ("Custom", "custom"),
            ],
            self.time_value(cfg.ui),
        )
        self.seconds = self.number("Seconds per side", 1, 10800, cfg.ui.base_seconds)
        self.increment = self.number("Increment", 0, 300, cfg.ui.increment_seconds)
        self.time.currentIndexChanged.connect(self.update_fields)
        self.mode.changed.connect(self.update_fields)
        self.update_fields()
        self.add_buttons("Play")

    @staticmethod
    def time_value(cfg):
        value = f"{cfg.base_seconds}:{cfg.increment_seconds}"
        return (
            "none" if not cfg.timed else value if value in ("180:2", "300:3", "600:0") else "custom"
        )

    def update_fields(self, *_):
        custom = self.time.currentData() == "custom"
        for field in (self.seconds, self.increment):
            field.setVisible(custom)
            self.fields.labelForField(field).setVisible(custom)
        for field, visible in (
            (self.color, self.mode.currentData() == "human_ai"),
            (self.level, self.mode.currentData() != "human_human"),
        ):
            field.setVisible(visible)
            self.fields.labelForField(field).setVisible(visible)

    def settings(self):
        clock = self.time.currentData()
        seconds, increment = self.seconds.value(), self.increment.value()
        if clock not in ("none", "custom"):
            seconds, increment = map(int, clock.split(":"))
        return dict(
            mode=self.mode.currentData(),
            player_color=self.color.currentData(),
            timed=clock != "none",
            base_seconds=seconds,
            increment_seconds=increment,
        )

    def engine_settings(self):
        return (
            engine_preset(self.level.currentData()) if self.level_changed else self.original_engine
        )

    def mark_level_changed(self):
        self.level_changed = True


class PromotionDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__("Promote pawn", parent.cfg.ui, parent, "Choose a piece to continue.")
        self.piece = Segments([("Queen", 5), ("Rook", 4), ("Bishop", 3), ("Knight", 2)], 5)
        for index, kind in enumerate(self.piece.values):
            button = self.piece.group.button(index)
            piece = chess.Piece(kind, parent.input_color())
            button.setIcon(piece_icon(piece, parent.cfg.ui))
            button.setIconSize(QSize(28, 28))
        self.fields.addRow(self.piece)
        self.piece.changed.connect(lambda _: self.accept())


def level_for_depth(depth):
    return "easy" if depth <= 2 else "default" if depth <= 4 else "hard"


def engine_preset(name):
    from utils.config import load_config

    cfg = load_config([f"engine={name}"]).engine
    return dict(depth=cfg.depth, time_ms=cfg.time_ms)
