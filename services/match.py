import random
from datetime import date
from shutil import which
from time import monotonic

import chess
import chess.engine
import chess.pgn
from omegaconf import OmegaConf

from core.engine import ChessEngine
from core.position import make_board
from core.time_control import think_time
from services.analysis import analyze
from utils.config import project_path


def executable(value):
    found = which(value)
    path = project_path(value)
    if found:
        return found
    if path.is_file():
        return str(path)
    raise FileNotFoundError(f"Engine executable not found: {value}")


def play_game(cfg, my_color, opponent, number):
    engine = ChessEngine(cfg)
    rival = ChessEngine(cfg) if opponent is None else opponent
    base, increment = map(float, cfg.match.time_control.split("+"))
    if base <= 0 or increment < 0:
        raise ValueError("match.time_control must be positive seconds+increment")
    clocks = {color: base * 1000 for color in chess.COLORS}
    board = make_board(cfg.position, cfg.moves)
    game = chess.pgn.Game.from_board(board)
    node = game.end()
    opponent_name = "SelfPlay" if opponent is None else f"Stockfish {cfg.match.opponent_elo}"
    game.headers.update(
        Event="Engine match",
        Date=date.today().strftime("%Y.%m.%d"),
        Round=str(number),
        TimeControl=cfg.match.time_control,
        White="MyAI" if my_color else opponent_name,
        Black=opponent_name if my_color else "MyAI",
    )
    result, reason = "*", "Ply limit"
    for _ in range(cfg.match.max_plies):
        outcome = board.outcome(claim_draw=True)
        if outcome:
            result, reason = outcome.result(), outcome.termination.name
            break
        color = board.turn
        budget = think_time(cfg.engine, clocks[color], increment * 1000)
        if cfg.engine.time_ms is not None:
            budget = min(budget, cfg.engine.time_ms)
        started = monotonic()
        if color == my_color or opponent is None:
            actor = engine if color == my_color else rival
            move = actor.choose(board, time_ms=budget).move
        else:
            move = rival.play(board, chess.engine.Limit(time=budget / 1000), game=game).move
        clocks[color] -= (monotonic() - started) * 1000
        if clocks[color] <= 0:
            winner = not color
            result = (
                "1/2-1/2" if board.has_insufficient_material(winner) else "1-0" if winner else "0-1"
            )
            reason = "Time forfeit"
            break
        if move not in board.legal_moves:
            raise RuntimeError(f"Engine returned an illegal move: {move}")
        clocks[color] += increment * 1000
        node = node.add_variation(move)
        board.push(move)
    else:
        outcome = board.outcome(claim_draw=True)
        if outcome:
            result, reason = outcome.result(), outcome.termination.name
    game.headers.update(Result=result, Termination=reason)
    return game


def run(cfg):
    if cfg.match.games < 1 or cfg.match.max_plies < 1:
        raise ValueError("match.games and match.max_plies must be positive")
    if cfg.match.opponent not in {"self", "stockfish"}:
        raise ValueError("match.opponent must be self or stockfish")
    path = project_path(cfg.match.output)
    command = executable(cfg.match.stockfish) if cfg.match.opponent == "stockfish" else None
    if cfg.match.dry_run:
        print(f"{cfg.match.games} games vs {command or 'self'}, PGN: {path}")
        return
    opponent = None
    try:
        if command:
            opponent = chess.engine.SimpleEngine.popen_uci([command])
            options = opponent.options
            if not (options["UCI_Elo"].min <= cfg.match.opponent_elo <= options["UCI_Elo"].max):
                raise ValueError("Requested Elo is outside this Stockfish's supported range")
            opponent.configure(
                {
                    "UCI_LimitStrength": True,
                    "UCI_Elo": cfg.match.opponent_elo,
                    "Threads": cfg.match.threads,
                    "Hash": cfg.match.hash_mb,
                }
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {
            key: OmegaConf.to_container(cfg[key], resolve=True)
            for key in ("engine", "evaluation", "match")
        }
        metadata.update(position=cfg.position, moves=list(cfg.moves))
        metadata["opponent_engine"] = dict(opponent.id) if opponent else "SelfPlay"
        path.with_suffix(".yaml").write_text(OmegaConf.to_yaml(metadata), encoding="utf-8")
        with path.open("w", encoding="utf-8") as file:
            for number in range(cfg.match.games):
                random.seed(cfg.match.seed + number // 2)
                game = play_game(cfg, number % 2 == 0, opponent, number + 1)
                print(game, file=file, end="\n\n", flush=True)
                print(
                    f"Game {number + 1}: {game.headers['Result']} ({game.headers['Termination']})"
                )
        print(f"PGN: {path}")
        print(analyze(path, "MyAI", cfg.match.opponent_elo if opponent else None))
    finally:
        if opponent:
            opponent.quit()
