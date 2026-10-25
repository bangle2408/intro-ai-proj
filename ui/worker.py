from PyQt5.QtCore import QObject, pyqtSignal


class EngineWorker(QObject):
    result = pyqtSignal(object)
    failure = pyqtSignal(str)
    iteration = pyqtSignal(object)

    def __init__(self, service, board, depth, budget, parent=None):
        super().__init__(parent)
        self.service = service
        self.board = board.copy(stack=True)
        self.depth = depth
        self.budget = budget
        self.job = None
        self.active = False
        service.message.connect(self.receive)

    def start(self):
        self.active = True
        self.job = self.service.submit(self.board, self.depth, self.budget)

    def isRunning(self):
        return self.active

    def receive(self, job, kind, value):
        if not self.active or job != self.job:
            return
        if kind == "iteration":
            self.iteration.emit(value)
        elif kind == "result":
            self.active = False
            self.result.emit(value)
        elif kind == "failure":
            self.active = False
            self.failure.emit(value)

    def cancel(self):
        self.active = False
        if self.job is not None:
            self.service.cancel(self.job)
