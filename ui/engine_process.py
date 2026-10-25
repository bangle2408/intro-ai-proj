import json
import sys

import chess
from omegaconf import OmegaConf
from PyQt5.QtCore import QCoreApplication, QObject, QProcess, pyqtSignal

from core.base import SearchResult
from utils.config import ROOT


class EngineProcess(QObject):
    message = pyqtSignal(int, str, object)
    closed = pyqtSignal()

    def __init__(self, cfg, parent=None):
        super().__init__(parent or QCoreApplication.instance())
        self.cfg = cfg
        self.evaluation_config = OmegaConf.to_container(cfg.evaluation, resolve=True)
        self.process = QProcess(self)
        self.buffer = b""
        self.pending = []
        self.sequence = 0
        self.current = None
        self.closing = False
        self.error_text = ""
        self.process.started.connect(self.flush)
        self.process.readyReadStandardOutput.connect(self.read)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.errorOccurred.connect(self.failed)
        self.process.finished.connect(self.finished)
        QCoreApplication.instance().aboutToQuit.connect(self.shutdown)

    def send(self, data):
        payload = json.dumps(data).encode() + b"\n"
        if self.process.state() == QProcess.Running:
            self.process.write(payload)
        else:
            self.pending.append(payload)

    def submit(self, board, depth, budget):
        if self.closing:
            raise RuntimeError("Engine process is closing")
        self.sequence += 1
        self.current = self.sequence
        if self.process.state() == QProcess.NotRunning:
            self.buffer = b""
            self.error_text = ""
            self.process.start(sys.executable, ["-u", str(ROOT / "game.py"), "mode=worker"])
        config = dict(
            engine=OmegaConf.to_container(self.cfg.engine, resolve=True),
            evaluation=self.evaluation_config,
        )
        self.send(
            dict(
                kind="search",
                id=self.current,
                config=config,
                position=board.root().fen(),
                moves=[m.uci() for m in board.move_stack],
                depth=depth,
                budget=budget,
            )
        )
        return self.current

    def flush(self):
        if self.closing:
            self.process.kill()
            return
        for payload in self.pending:
            self.process.write(payload)
        self.pending.clear()

    def cancel(self, job):
        if self.current == job:
            self.current = None
        self.send(dict(kind="cancel", id=job))

    def clear(self):
        if self.process.state() != QProcess.NotRunning:
            self.send(dict(kind="clear"))

    def read(self):
        self.buffer += bytes(self.process.readAllStandardOutput())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                data = json.loads(line)
                job, kind = data["id"], data["kind"]
                if job != self.current:
                    continue
                value = data.get("error")
                if "result" in data:
                    result = data["result"]
                    result["move"] = chess.Move.from_uci(result["move"]) if result["move"] else None
                    value = SearchResult(**result)
                if kind in ("result", "failure"):
                    self.current = None
                self.message.emit(job, kind, value)
            except (ValueError, KeyError, TypeError) as error:
                self.fail_current(f"Invalid engine response: {error}")

    def read_error(self):
        self.error_text = (
            self.error_text + bytes(self.process.readAllStandardError()).decode(errors="replace")
        )[-4000:]

    def fail_current(self, message):
        job, self.current = self.current, None
        if job is not None and not self.closing:
            self.message.emit(job, "failure", message)

    def failed(self, error):
        if error == QProcess.FailedToStart:
            self.pending.clear()
            self.fail_current(self.process.errorString())

    def finished(self, code, status):
        self.pending.clear()
        self.fail_current(self.error_text or f"Engine process exited ({code})")
        if self.closing:
            self.closed.emit()

    def isRunning(self):
        return self.process.state() != QProcess.NotRunning

    def shutdown(self):
        if self.closing:
            return
        self.closing = True
        self.current = None
        self.pending.clear()
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
        else:
            self.closed.emit()
