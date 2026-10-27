from omegaconf import OmegaConf
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget

from core.evaluation import Evaluation
from core.position import make_board
from ui.actions import GameActions
from ui.appearance import GameAppearance
from ui.board import BoardView
from ui.clock import ChessClock
from ui.controls import ControlPanel
from ui.engine_process import EngineProcess
from ui.evaluation_bar import EvaluationBar
from ui.input import GameInput
from ui.layout import Header, MatchCanvas
from ui.moves import GameMoves
from ui.player import PlayerRow
from ui.premoves import PremoveQueue
from ui.view import GameView


class ChessWindow(GameActions, GameAppearance, GameInput, GameMoves, GameView, QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = OmegaConf.create(OmegaConf.to_container(cfg, resolve=False))
        self.evaluator = Evaluation(self.cfg.evaluation)
        self.search = EngineProcess(self.cfg, self)
        self.search.closed.connect(self.close, Qt.QueuedConnection)
        self.closing = False
        self.worker = None
        self.generation = 0
        self.dirty = False
        self.result = None
        self.result_reason = ""
        self.last_search = None
        self.active = True
        self.clock_history = []
        self.premoves = PremoveQueue(cfg.ui.max_premoves)
        self.position = make_board(cfg.position, cfg.moves)
        self.clock = ChessClock(self.cfg.ui, self)
        self.build_layout()
        self.clock.changed.connect(self.refresh_clocks)
        self.clock.expired.connect(self.time_expired)
        self.setWindowTitle(cfg.ui.title)
        screen = self.screen().availableGeometry()
        self.resize(
            min(cfg.ui.width, screen.width() - 48), min(cfg.ui.height, screen.height() - 48)
        )
        self.start_position(self.position)

    def build_layout(self):
        self.board_view = BoardView(self.cfg.ui)
        self.evaluation_bar = EvaluationBar(self.cfg.ui)
        self.board_view.pressed.connect(self.begin_selection)
        self.board_view.clicked.connect(self.select_square)
        self.board_view.dropped.connect(self.drop_piece)
        self.board_view.cancelled.connect(lambda: self.clear_input(annotations=False))
        self.top_player = PlayerRow(self.cfg.ui)
        self.bottom_player = PlayerRow(self.cfg.ui)
        self.panel = ControlPanel(self.cfg, self)
        self.header = Header(self.cfg.ui, self)
        self.canvas = MatchCanvas(
            self.cfg.ui,
            self.header,
            self.board_view,
            self.top_player,
            self.bottom_player,
            self.panel,
            self.evaluation_bar,
        )
        self.setCentralWidget(self.canvas)
        for widget in (self, *self.findChildren(QWidget)):
            widget.installEventFilter(self)

    def start_position(self, board):
        self.clock.pause()
        self.position = board.copy(stack=True)
        self.search.clear()
        self.clock.reset(self.cfg.ui)
        self.clock_history = []
        self.clear_input()
        self.result = None
        self.result_reason = ""
        self.dirty = False
        self.last_search = None
        self.board_view.selected = None
        self.board_view.flipped = self.cfg.ui.player_color == "black"
        outcome = self.position.outcome(claim_draw=True)
        if outcome:
            self.result = outcome.result()
            self.result_reason = outcome.termination.name.replace("_", " ").title()
        self.active = not bool(self.result)
        if self.active:
            self.clock.start(self.position.turn)
        self.refresh()
        self.board_view.setFocus(Qt.OtherFocusReason)
        if self.active and self.is_ai_turn():
            QTimer.singleShot(0, self.request_ai)
