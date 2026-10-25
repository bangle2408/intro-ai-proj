import json
from datetime import datetime, timezone
from pathlib import Path

from core.position import make_board


def save_game(path, board, settings, clock, flipped=False, result=None):
    data = dict(
        version="3.0",
        initial_fen=board.root().fen(),
        fen=board.fen(),
        move_history=[m.uci() for m in board.move_stack],
        mode=settings.mode,
        player_color=settings.player_color,
        base_seconds=settings.base_seconds,
        increment_seconds=settings.increment_seconds,
        board_flipped=flipped,
        timer_settings=clock,
        result=result,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(target)


def load_game(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Save file must contain an object")
    history = data.get("move_history", [])
    board = make_board(data.get("initial_fen", "startpos"), history)
    if "fen" in data and board.fen() != data["fen"]:
        if history:
            raise ValueError("Saved position does not match move history")
        board = make_board(data["fen"])
    mode = data.get("mode", "human_ai")
    if mode not in {"human_ai", "ai_ai", "human_human"}:
        raise ValueError("Unsupported game mode")
    if data.get("player_color", "white") not in {"white", "black"}:
        raise ValueError("Invalid player color")
    for key, minimum in (("base_seconds", 1), ("increment_seconds", 0)):
        if key in data and (type(data[key]) is not int or data[key] < minimum):
            raise ValueError(f"Invalid clock control: {key}")
    clock = data.get("timer_settings", {})
    for key in ("white_time_ms", "black_time_ms", "white_increment_ms", "black_increment_ms"):
        if not isinstance(clock.get(key, 0), (int, float)) or clock.get(key, 0) < 0:
            raise ValueError(f"Invalid clock field: {key}")
    return board, data
