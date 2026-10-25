import chess
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QTableView


class MoveModel(QAbstractTableModel):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.rows = []
        self.moves = []
        self.board = chess.Board()
        self.last = None

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else 3

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("", "White", "Black")[section]

    def data(self, index, role):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if role == Qt.DisplayRole:
            return self.rows[row][col]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter | Qt.AlignLeft
        if role == Qt.ForegroundRole:
            return QColor(self.cfg.muted if col == 0 else self.cfg.text)
        if role == Qt.BackgroundRole and (row, col) == self.last:
            return QColor(self.cfg.surface_alt)
        if role == Qt.FontRole:
            font = QFont(self.cfg.font, 11)
            font.setBold((row, col) == self.last)
            return font

    def set_board(self, position):
        root = position.root()
        moves = position.move_stack
        if root.fen() != self.board.root().fen() or list(moves[: len(self.moves)]) != self.moves:
            self.beginResetModel()
            self.rows, self.moves, self.last = [], [], None
            self.board = root
            self.endResetModel()
        for move in moves[len(self.moves) :]:
            number = str(self.board.fullmove_number)
            if not self.rows or self.rows[-1][0] != number:
                self.beginInsertRows(QModelIndex(), len(self.rows), len(self.rows))
                self.rows.append([number, "", ""])
                self.endInsertRows()
            previous = self.last
            self.last = len(self.rows) - 1, 1 if self.board.turn else 2
            self.rows[-1][self.last[1]] = self.board.san(move)
            self.board.push(move)
            self.moves.append(move)
            if previous:
                index = self.index(*previous)
                self.dataChanged.emit(index, index)
            index = self.index(*self.last)
            self.dataChanged.emit(index, index)


class MoveHistory(QTableView):
    def __init__(self, cfg):
        super().__init__()
        self.moves = MoveModel(cfg)
        self.setModel(self.moves)
        self.setAccessibleName("Move history")
        self.setShowGrid(False)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(36)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.setColumnWidth(0, 36)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def set_board(self, position):
        self.moves.set_board(position)
        self.scrollToBottom()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.scrollToBottom)
