import chess


def premove_targets(board, source):
    piece = board.piece_at(source)
    if piece is None:
        return set()
    file, rank = chess.square_file(source), chess.square_rank(source)
    targets = set()
    for destination in chess.SQUARES:
        dx = chess.square_file(destination) - file
        dy = chess.square_rank(destination) - rank
        if not (dx or dy):
            continue
        if piece.piece_type == chess.PAWN:
            forward = 1 if piece.color else -1
            possible = dy == forward and abs(dx) <= 1
            possible |= dx == 0 and dy == 2 * forward and rank == (1 if piece.color else 6)
        elif piece.piece_type == chess.KNIGHT:
            possible = sorted((abs(dx), abs(dy))) == [1, 2]
        elif piece.piece_type == chess.KING:
            possible = max(abs(dx), abs(dy)) == 1
            if file == 4 and rank == (0 if piece.color else 7) and dy == 0:
                possible |= dx == 2 and board.has_kingside_castling_rights(piece.color)
                possible |= dx == -2 and board.has_queenside_castling_rights(piece.color)
        else:
            diagonal = abs(dx) == abs(dy)
            straight = dx == 0 or dy == 0
            possible = (
                piece.piece_type in (chess.BISHOP, chess.QUEEN)
                and diagonal
                or piece.piece_type in (chess.ROOK, chess.QUEEN)
                and straight
            )
        if possible and board.piece_at(destination) != chess.Piece(chess.KING, piece.color):
            targets.add(destination)
    return targets
