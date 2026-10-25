import math

import chess.pgn

from utils.config import project_path


def analyze(path, engine_name, opponent_elo=None):
    counts = {"wins": 0, "draws": 0, "losses": 0, "skipped": 0}
    with open(path, encoding="utf-8") as file:
        while (game := chess.pgn.read_game(file)) is not None:
            white = game.headers.get("White", "").casefold() == engine_name.casefold()
            black = game.headers.get("Black", "").casefold() == engine_name.casefold()
            result = game.headers.get("Result", "*")
            if white == black or result not in {"1-0", "0-1", "1/2-1/2"}:
                counts["skipped"] += 1
            elif result == "1/2-1/2":
                counts["draws"] += 1
            else:
                won = (result == "1-0") == white
                counts["wins" if won else "losses"] += 1
    total = counts["wins"] + counts["draws"] + counts["losses"]
    score = (counts["wins"] + counts["draws"] / 2) / total if total else None
    delta = 400 * math.log10(score / (1 - score)) if score and score < 1 else None
    elo = opponent_elo + delta if delta is not None and opponent_elo is not None else None
    return dict(counts, games=total, score=score, elo_difference=delta, estimated_elo=elo)


def run(cfg):
    if not cfg.pgn:
        raise ValueError("Set pgn=path/to/match.pgn")
    stats = analyze(project_path(cfg.pgn), cfg.engine_name, cfg.opponent_elo)
    for key, value in stats.items():
        print(f"{key}: {value}")
    print("Elo is an estimate for these match conditions; no confidence interval is computed.")
