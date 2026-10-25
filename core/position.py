import chess


def make_board(position="startpos", moves=()):
    fen = chess.STARTING_FEN if position == "startpos" else position
    board = chess.Board(fen)
    if not board.is_valid():
        raise ValueError("Invalid chess position")
    for move in moves:
        board.push_uci(move)
    return board


def terminal_score(board, ply=0):
    if board.is_checkmate():
        return -100000 + ply
    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.is_fifty_moves()
        or board.is_repetition(3)
    ):
        return 0
    return None
