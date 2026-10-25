import chess


class GameView:
    def player_name(self, color):
        side = "White" if color else "Black"
        if self.cfg.ui.mode == "human_human":
            return side
        if self.cfg.ui.mode == "ai_ai":
            return f"Computer · {side}"
        return "You" if color == (self.cfg.ui.player_color == "white") else "Computer"

    def refresh(self):
        self.refresh_input()
        self.refresh_clocks()
        modes = {
            "human_ai": "Computer",
            "human_human": "Two players",
            "ai_ai": "Computer vs computer",
        }
        self.panel.heading.setText("Your game" if self.cfg.ui.mode != "ai_ai" else "Watch a game")
        base = self.cfg.ui.base_seconds
        duration = str(base // 60) if base % 60 == 0 else f"{base}s"
        clock = (
            f"{duration} + {self.cfg.ui.increment_seconds}" if self.clock.enabled else "No clock"
        )
        self.panel.summary.setText(f"{modes[self.cfg.ui.mode]}  ·  {clock}")
        self.panel.history.set_board(self.position)
        self.refresh_status()
        show = self.cfg.ui.show_evaluation
        self.panel.evaluation.setVisible(show)
        if show:
            score = self.evaluator.evaluate(self.position) * (1 if self.position.turn else -1)
            self.panel.evaluation.setText(f"Position estimate  {score / 100:+.2f}")
        self.refresh_captured()
        self.panel.buttons["Undo"].setEnabled(self.undo_count() > 0)
        self.panel.resign_action.setEnabled(self.active and self.cfg.ui.mode != "ai_ai")

    def refresh_status(self):
        side = "White" if self.position.turn else "Black"
        if self.result:
            status = {"1-0": "White wins", "0-1": "Black wins", "1/2-1/2": "Draw"}.get(
                self.result, "Game ended"
            )
            if self.cfg.ui.mode == "human_ai" and self.result in ("1-0", "0-1"):
                won = (self.result == "1-0") == (self.cfg.ui.player_color == "white")
                status = "You won" if won else "Computer wins"
            caption = self.result_reason
        elif not self.active:
            status, caption = "Game stopped", "Start a new game to continue."
        elif self.is_ai_turn():
            status, caption = "Computer is thinking", f"{side} to move"
        else:
            status = "Your move" if self.cfg.ui.mode == "human_ai" else f"{side} to move"
            caption = f"{side} is in check" if self.position.is_check() else f"{side} to move"
        self.panel.status.setText(status)
        self.panel.subtitle.setText(caption)

    def refresh_clocks(self):
        bottom = not self.board_view.flipped
        for row, color in ((self.bottom_player, bottom), (self.top_player, not bottom)):
            time = self.clock.text(color) if self.clock.enabled else ""
            active = self.active and self.clock.active == color
            row.display(color, self.player_name(color), time, active)

    def refresh_captured(self):
        replay = self.position.root()
        lost = {color: [] for color in chess.COLORS}
        for move in self.position.move_stack:
            if replay.is_en_passant(move):
                lost[not replay.turn].append(chess.Piece(chess.PAWN, not replay.turn))
            elif replay.is_capture(move):
                piece = replay.piece_at(move.to_square)
                lost[piece.color].append(piece)
            replay.push(move)
        for row in (self.top_player, self.bottom_player):
            row.set_captures(lost[not row.color])
