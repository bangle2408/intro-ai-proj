from PyQt5.QtCore import QTimer

from core.time_control import think_time
from ui.worker import EngineWorker


class GameMoves:
    def is_ai_turn(self):
        return self.cfg.ui.mode == "ai_ai" or (
            self.cfg.ui.mode == "human_ai"
            and self.position.turn != (self.cfg.ui.player_color == "white")
        )

    def apply_move(self, move, animate=True, premove=False):
        if move not in self.position.legal_moves or self.result or not self.active:
            return
        before = self.clock.snapshot()
        cost = self.cfg.ui.premove_cost_ms if premove else 0
        if self.result or not self.clock.finish_move(self.position.turn, cost):
            return
        self.clock_history.append(before)
        previous = self.position.copy(stack=False)
        self.position.push(move)
        self.dirty = True
        outcome = self.position.outcome(claim_draw=True)
        if outcome:
            self.finish(outcome.result(), outcome.termination.name.replace("_", " ").title())
            return
        if self.premoves and not self.is_ai_turn():
            queued = self.premoves.take(self.position)
            if queued:
                self.apply_move(queued, animate=False, premove=True)
                return
        self.refresh()
        if animate:
            self.board_view.animate_move(move, previous)
        QTimer.singleShot(0, self.request_ai)

    def request_ai(self):
        if not self.active or self.result or self.worker or not self.is_ai_turn():
            return
        if self.position.is_game_over(claim_draw=True):
            outcome = self.position.outcome(claim_draw=True)
            self.finish(outcome.result(), outcome.termination.name)
            return
        budget = self.cfg.engine.time_ms
        if self.clock.enabled:
            color = self.position.turn
            clock_budget = think_time(
                self.cfg.engine, self.clock.remaining[color], self.clock.increments[color]
            )
            budget = min(budget, clock_budget) if budget is not None else clock_budget
        generation = self.generation
        worker = EngineWorker(self.search, self.position, self.cfg.engine.depth, budget, self)
        self.worker = worker
        worker.result.connect(lambda result: self.receive_move(generation, result))
        worker.failure.connect(lambda message: self.receive_error(generation, message))
        worker.iteration.connect(lambda result: self.search_progress(generation, result))
        worker.start()
        self.refresh()

    def cancel_search(self):
        self.generation += 1
        self.clear_input()
        if self.worker:
            self.worker.cancel()
            self.worker.deleteLater()
            self.worker = None

    def receive_move(self, generation, result):
        if generation != self.generation:
            return
        self.worker.deleteLater()
        self.worker = None
        self.last_search = result
        if result.move:
            self.apply_move(result.move)
        else:
            self.refresh()

    def receive_error(self, generation, message):
        if generation != self.generation:
            return
        self.cancel_search()
        self.active = False
        self.clock.pause()
        self.show_error(message)
        self.refresh()

    def search_progress(self, generation, result):
        if generation == self.generation:
            self.last_search = result
