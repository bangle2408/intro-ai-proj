import json
import sys
from dataclasses import asdict
from queue import Queue
from threading import Event, Lock, Thread

from omegaconf import OmegaConf

from core.engine import ChessEngine
from core.position import make_board


class SearchWorker:
    def __init__(self):
        self.jobs = Queue()
        self.events = {}
        self.lock = Lock()

    @staticmethod
    def send(kind, job, result=None, error=None):
        data = {"kind": kind, "id": job}
        if result is not None:
            data["result"] = asdict(result)
            data["result"]["move"] = result.move.uci() if result.move else None
        if error is not None:
            data["error"] = str(error)
        print(json.dumps(data), flush=True)

    def read_commands(self):
        try:
            for line in sys.stdin:
                message = json.loads(line)
                kind, job = message["kind"], message.get("id")
                with self.lock:
                    if kind == "search":
                        event = Event()
                        self.events[job] = event
                        self.jobs.put((message, event))
                    elif kind == "cancel":
                        if job in self.events:
                            self.events[job].set()
                    elif kind == "clear":
                        self.jobs.put((message, None))
        finally:
            with self.lock:
                for event in self.events.values():
                    event.set()
            self.jobs.put((None, None))

    def run(self):
        Thread(target=self.read_commands, daemon=True).start()
        engine, settings = None, None
        while True:
            message, cancelled = self.jobs.get()
            if message is None:
                return
            if message["kind"] == "clear":
                if engine:
                    engine.cache.clear()
                continue
            job = message["id"]
            try:
                if cancelled.is_set():
                    continue
                if message["config"] != settings:
                    engine = ChessEngine(OmegaConf.create(message["config"]))
                    settings = message["config"]
                engine.cancelled = cancelled
                board = make_board(message["position"], message["moves"])
                result = engine.choose(
                    board,
                    message["depth"],
                    message["budget"],
                    lambda result: self.send("iteration", job, result),
                )
                if not cancelled.is_set():
                    self.send("result", job, result)
            except Exception as error:
                self.send("failure", job, error=error)
            finally:
                with self.lock:
                    self.events.pop(job, None)


def run(cfg):
    SearchWorker().run()
