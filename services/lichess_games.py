import logging

from core.engine import ChessEngine
from core.position import make_board
from core.time_control import think_time


class LichessGames:
    def play_game(self, game_id):
        engine = ChessEngine(self.cfg)
        self.engines[game_id] = engine
        color, initial_fen, last_moves = None, "startpos", None
        try:
            while not self.stopped.is_set():
                try:
                    for event in self.stream(f"/bot/game/stream/{game_id}"):
                        kind = event.get("type")
                        if kind == "gameFull":
                            color = event["white"]["id"].casefold() == self.account_id
                            initial_fen = event.get("initialFen", "startpos")
                            state = event["state"]
                        elif kind == "gameState":
                            state = event
                        else:
                            continue
                        if state.get("status") not in {"started", "created"}:
                            return
                        moves = state.get("moves", "")
                        if color is None or moves == last_moves:
                            continue
                        board = make_board(initial_fen, moves.split())
                        if board.turn != color or board.is_game_over():
                            continue
                        prefix = "w" if color else "b"
                        budget = think_time(
                            self.cfg.engine, state[prefix + "time"], state.get(prefix + "inc", 0)
                        )
                        if self.cfg.engine.time_ms is not None:
                            budget = min(budget, self.cfg.engine.time_ms)
                        result = engine.choose(board, time_ms=budget)
                        if result.move and not self.stopped.is_set():
                            self.request("POST", f"/bot/game/{game_id}/move/{result.move.uci()}")
                            last_moves = moves
                except Exception as error:
                    logging.warning("Game %s: %s", game_id, error)
                if self.stopped.wait(self.cfg.lichess.retry_seconds):
                    return
        finally:
            self.engines.pop(game_id, None)
            self.games.pop(game_id, None)
