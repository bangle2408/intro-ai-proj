from time import monotonic

import chess
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class ChessClock(QObject):
    changed = pyqtSignal()
    expired = pyqtSignal(bool)

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)
        self.reset(cfg)

    def reset(self, cfg):
        self.timer.stop()
        self.enabled = cfg.timed
        self.remaining = {c: int(cfg.base_seconds * 1000) for c in chess.COLORS}
        self.increments = {c: int(cfg.increment_seconds * 1000) for c in chess.COLORS}
        self.active = None
        self.last = monotonic()
        self.turn_started = self.last
        self.changed.emit()

    def tick(self):
        now = monotonic()
        if self.active is not None and self.enabled:
            self.remaining[self.active] = max(
                0, self.remaining[self.active] - (now - self.last) * 1000
            )
            if self.remaining[self.active] <= 0:
                loser = self.active
                self.pause()
                self.expired.emit(loser)
        self.last = now
        self.changed.emit()

    def start(self, color):
        self.last = monotonic()
        self.turn_started = self.last
        self.active = color
        if self.enabled:
            self.timer.start()

    def pause(self):
        self.timer.stop()
        self.active = None

    def finish_move(self, color, minimum_ms=0):
        if self.enabled:
            self.tick()
            if self.remaining[color] <= 0:
                return False
            elapsed = (monotonic() - self.turn_started) * 1000
            self.remaining[color] = max(0, self.remaining[color] - max(0, minimum_ms - elapsed))
            if self.remaining[color] <= 0:
                self.pause()
                self.expired.emit(color)
                return False
            self.remaining[color] += self.increments[color]
        self.start(not color)
        return True

    def snapshot(self):
        if self.active is not None:
            self.tick()
        return dict(
            enabled=self.enabled,
            white_time_ms=int(self.remaining[chess.WHITE]),
            black_time_ms=int(self.remaining[chess.BLACK]),
            white_increment_ms=self.increments[chess.WHITE],
            black_increment_ms=self.increments[chess.BLACK],
        )

    def restore(self, data):
        self.pause()
        self.enabled = data.get("enabled", False)
        for color, name in ((chess.WHITE, "white"), (chess.BLACK, "black")):
            self.remaining[color] = data.get(f"{name}_time_ms", 0)
            self.increments[color] = data.get(f"{name}_increment_ms", 0)
        self.changed.emit()

    def text(self, color):
        if not self.enabled:
            return "∞"
        remaining = max(0, self.remaining[color]) / 1000
        if remaining < 10:
            return f"{remaining:.1f}"
        seconds = int(remaining)
        return f"{seconds // 60:02}:{seconds % 60:02}"
