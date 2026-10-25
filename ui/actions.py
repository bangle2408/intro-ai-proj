import chess
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from ui.dialogs import NewGameDialog
from ui.preferences import PreferencesDialog
from utils.persistence import load_game, save_game


class GameActions:
    def confirm_discard(self):
        if not self.dirty:
            return True
        return (
            QMessageBox.question(
                self, "Unsaved game", "Discard unsaved changes?", QMessageBox.Yes | QMessageBox.No
            )
            == QMessageBox.Yes
        )

    def new_game(self):
        dialog = NewGameDialog(self.cfg, self)
        if dialog.exec_() == QDialog.Accepted:
            self.cancel_search()
            for key, value in dialog.settings().items():
                self.cfg.ui[key] = value
            for key, value in dialog.engine_settings().items():
                self.cfg.engine[key] = value
            self.start_position(chess.Board())

    def edit_preferences(self):
        dialog = PreferencesDialog(self.cfg, self)
        if dialog.exec_() != QDialog.Accepted:
            return
        self.cancel_search()
        for section, values in dialog.settings().items():
            for key, value in values.items():
                self.cfg[section][key] = value
        self.refresh()
        self.request_ai()

    def undo_count(self):
        if (not self.active and not self.result) or self.cfg.ui.mode == "ai_ai":
            return 0
        board = self.position.copy(stack=True)
        count = 0
        while board.move_stack:
            board.pop()
            count += 1
            if self.cfg.ui.mode == "human_human" or board.turn == (
                self.cfg.ui.player_color == "white"
            ):
                return count
        return 0

    def undo(self):
        count = self.undo_count()
        if not count:
            return
        self.cancel_search()
        self.clock.pause()
        for _ in range(count):
            self.position.pop()
            if self.clock_history:
                self.clock.restore(self.clock_history.pop())
        self.result = None
        self.result_reason = ""
        self.active = True
        self.last_search = None
        self.search.clear()
        self.board_view.selected = None
        self.dirty = True
        self.clock.start(self.position.turn)
        self.refresh()
        self.request_ai()

    def flip(self):
        self.board_view.reset_pointer()
        self.board_view.stop_animation()
        self.board_view.flipped = not self.board_view.flipped
        self.dirty = True
        self.board_view.invalidate_board()
        self.refresh_clocks()
        self.refresh_captured()

    def save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save game", "game.chess", "Chess game (*.chess)"
        )
        if not path:
            return
        if not path.endswith(".chess"):
            path += ".chess"
        try:
            save_game(
                path,
                self.position,
                self.cfg.ui,
                self.clock.snapshot(),
                self.board_view.flipped,
                self.result,
            )
            self.dirty = False
        except (OSError, ValueError) as error:
            self.show_error(str(error))

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load game", "", "Chess game (*.chess)")
        if not path:
            return
        try:
            board, data = load_game(path)
            if not self.confirm_discard():
                return
            self.cancel_search()
            for key in ("mode", "player_color", "base_seconds", "increment_seconds"):
                self.cfg.ui[key] = data.get(key, self.cfg.ui[key])
            self.start_position(board)
            self.result = data.get("result") or self.result
            self.board_view.flipped = data.get("board_flipped", False)
            self.clock.restore(data.get("timer_settings", {}))
            self.cfg.ui.timed = self.clock.enabled
            self.active = not bool(self.result)
            if self.active:
                self.clock.start(self.position.turn)
            self.refresh()
        except (OSError, ValueError, TypeError, KeyError) as error:
            self.show_error(str(error))

    def resign(self):
        if self.result:
            return
        if QMessageBox.question(self, "Resign", "Resign this game?") != QMessageBox.Yes:
            return
        loser = (
            self.cfg.ui.player_color == "white"
            if self.cfg.ui.mode == "human_ai"
            else self.position.turn
        )
        self.finish("0-1" if loser else "1-0", "Resignation")

    def finish(self, result, reason):
        self.result = result
        self.result_reason = reason
        self.active = False
        self.clock.pause()
        self.cancel_search()
        self.dirty = True
        self.refresh()

    def time_expired(self, loser):
        winner = not loser
        result = (
            "1/2-1/2"
            if self.position.has_insufficient_material(winner)
            else "1-0"
            if winner
            else "0-1"
        )
        self.finish(result, "Time expired")

    def show_error(self, message):
        QMessageBox.critical(self, "Chess", message)

    def closeEvent(self, event):
        if not self.closing:
            if not self.confirm_discard():
                event.ignore()
                return
            self.closing = True
            self.active = False
            self.cancel_search()
            self.clock.pause()
            self.search.shutdown()
        if self.search.isRunning():
            event.ignore()
        else:
            event.accept()
