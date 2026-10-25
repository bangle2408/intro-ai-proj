from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import Event

import chess


@dataclass(frozen=True)
class SearchResult:
    move: chess.Move | None
    score: int = 0
    depth: int = 0
    nodes: int = 0
    elapsed_ms: int = 0
    source: str = "search"


class BaseEngine(ABC):
    def __init__(self, cfg):
        self.cfg = cfg
        self.cancelled = Event()

    def stop(self):
        self.cancelled.set()

    @abstractmethod
    def choose(self, board, depth=None, time_ms=None, on_iteration=None):
        pass
