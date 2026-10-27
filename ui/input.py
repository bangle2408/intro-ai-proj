import chess
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import QDialog

from ui.dialogs import PromotionDialog
from ui.mobility import premove_targets


class GameInput:
    def input_color(self):
        if not self.active or self.result or self.cfg.ui.mode == "ai_ai":
            return None
        if self.cfg.ui.mode == "human_human":
            return self.position.turn
        return self.cfg.ui.player_color == "white"

    def can_premove(self):
        color = self.input_color()
        return color is not None and color != self.position.turn and self.cfg.ui.premoves

    def destinations(self, source, board):
        if source is None:
            return set()
        if self.can_premove():
            return premove_targets(board, source)
        return {m.to_square for m in self.position.legal_moves if m.from_square == source}

    def refresh_input(self):
        preview = self.premoves.preview(self.position)
        color = self.input_color()
        allowed = color is not None and (color == self.position.turn or self.can_premove())
        movable = {
            sq for sq, piece in preview.piece_map().items() if allowed and piece.color == color
        }
        targets = self.destinations(self.board_view.selected, preview) if allowed else set()
        self.board_view.sync(self.position, preview, self.premoves.items, movable, targets)
        if self.premoves:
            moves = " → ".join(plan.move.uci() for plan in self.premoves.items)
            self.panel.premove_status.setText(f"Queued · {moves}\nRight-click or Esc to cancel")
        else:
            self.panel.premove_status.clear()
        self.panel.premove_status.setVisible(bool(self.premoves))

    def begin_selection(self, square):
        view = self.board_view
        if square in view.movable and square not in view.targets:
            view.selected = square
            self.refresh_input()

    def select_square(self, square):
        view = self.board_view
        source = view.selected
        if square == source:
            view.selected = None
        elif source is not None and square in view.targets:
            self.submit_move(source, square)
            return
        else:
            view.selected = square if square in view.movable else None
        self.refresh_input()

    def drop_piece(self, source, target):
        self.submit_move(source, target, dragged=True)

    def submit_move(self, source, target, dragged=False):
        view = self.board_view
        preview = self.premoves.preview(self.position)
        piece = preview.piece_at(source)
        color = self.input_color()
        if (
            piece is None
            or piece.color != color
            or target not in self.destinations(source, preview)
        ):
            view.selected = None
            self.refresh_input()
            return
        promotion = None
        if piece.piece_type == chess.PAWN and target // 8 in (0, 7):
            promotion = self.promotion_choice()
            if promotion is None:
                return
        move = chess.Move(source, target, promotion=promotion)
        if (
            self.input_color() != color
            or self.premoves.preview(self.position).piece_at(source) != piece
        ):
            return
        view.selected = None
        if self.can_premove():
            queued = self.premoves.append(self.position, move)
            self.refresh_input()
            if not queued:
                self.panel.premove_status.setText(
                    f"Queue full ({self.premoves.limit} moves). Esc cancels."
                )
        elif self.position.turn == color and move in self.position.legal_moves:
            self.apply_move(move, animate=not dragged)
        else:
            self.refresh_input()

    def promotion_choice(self):
        if self.cfg.ui.auto_queen:
            return chess.QUEEN
        generation = self.generation
        dialog = PromotionDialog(self)
        accepted = dialog.exec_() == QDialog.Accepted
        return dialog.piece.currentData() if accepted and generation == self.generation else None

    def clear_input(self, annotations=True):
        self.premoves.clear()
        if annotations:
            self.board_view.clear_annotations()
        self.board_view.reset_pointer()
        self.board_view.selected = None
        self.board_view.stop_animation()
        self.refresh_input()

    def event(self, event):
        if event.type() in (QEvent.WindowDeactivate, QEvent.Hide) and hasattr(self, "board_view"):
            self.board_view.reset_pointer()
        return super().event(event)

    def eventFilter(self, watched, event):
        if (
            event.type() in (QEvent.ShortcutOverride, QEvent.KeyPress)
            and event.key() == Qt.Key_Escape
        ):
            if event.type() == QEvent.KeyPress:
                self.clear_input()
            event.accept()
            return True
        return super().eventFilter(watched, event)
