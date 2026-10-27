from PyQt5.QtWidgets import QPushButton

from ui.dialogs import BaseDialog, engine_preset, level_for_depth


class PreferencesDialog(BaseDialog):
    def __init__(self, cfg, parent=None):
        super().__init__("Preferences", cfg.ui, parent, "Keep the board the way you like it.")
        self.time_ms = cfg.engine.time_ms
        self.level = self.combo(
            "Computer strength",
            [("Easy", "easy"), ("Standard", "default"), ("Strong", "hard")],
            level_for_depth(cfg.engine.depth),
        )
        self.method = self.combo(
            "Move pieces",
            [("Drag or click", "both"), ("Drag only", "drag"), ("Click only", "click")],
            cfg.ui.move_method,
        )
        self.premoves = self.toggle("Premoves", cfg.ui.premoves)
        self.destinations = self.toggle("Show legal moves", cfg.ui.show_destinations)
        self.queen = self.toggle("Auto-queen", cfg.ui.auto_queen)
        self.motion = self.toggle("Piece animation", cfg.ui.animation_ms > 0)
        self.evaluation = self.toggle("Evaluation bar", cfg.ui.show_evaluation)
        self.advanced = QPushButton("Advanced search settings")
        self.advanced.setObjectName("quiet")
        self.advanced.setCheckable(True)
        self.fields.addRow(self.advanced)
        self.depth = self.number("Search depth", 1, 20, cfg.engine.depth)
        self.depth.hide()
        self.fields.labelForField(self.depth).hide()
        self.advanced.toggled.connect(self.show_advanced)
        self.level.currentIndexChanged.connect(self.change_level)
        self.add_buttons()

    def show_advanced(self, enabled):
        self.depth.setVisible(enabled)
        self.fields.labelForField(self.depth).setVisible(enabled)
        self.advanced.setText("Hide advanced settings" if enabled else "Advanced search settings")
        self.adjustSize()

    def change_level(self):
        settings = engine_preset(self.level.currentData())
        self.depth.setValue(settings["depth"])
        self.time_ms = settings["time_ms"]

    def settings(self):
        return dict(
            engine=dict(depth=self.depth.value(), time_ms=self.time_ms),
            ui=dict(
                move_method=self.method.currentData(),
                premoves=self.premoves.isChecked(),
                show_destinations=self.destinations.isChecked(),
                auto_queen=self.queen.isChecked(),
                animation_ms=100 if self.motion.isChecked() else 0,
                show_evaluation=self.evaluation.isChecked(),
            ),
        )
