import subprocess
import sys

import chess.pgn

from services.analysis import analyze
from utils.config import ROOT


def invoke(*args, cwd=None):
    result = subprocess.run(
        [sys.executable, str(ROOT / "game.py"), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_full_selfplay_to_pgn_to_analysis(tmp_path):
    path = tmp_path / "match.pgn"
    output = invoke(
        "mode=match",
        "match.games=2",
        "match.max_plies=12",
        "engine.depth=1",
        "engine.time_ms=30",
        "engine.book=null",
        f"match.output={path}",
        cwd=tmp_path,
    )
    assert "Game 2:" in output
    with path.open() as file:
        games = [chess.pgn.read_game(file), chess.pgn.read_game(file)]
    assert games[0].headers["White"] == games[1].headers["Black"] == "MyAI"
    for game in games:
        board = game.board()
        for move in game.mainline_moves():
            assert move in board.legal_moves
            board.push(move)
        assert len(board.move_stack) == 12
        assert game.headers["Termination"] == "Ply limit"
        assert game.headers["Result"] == "*"
    assert analyze(path, "MyAI")["skipped"] == 2
    assert "skipped: 2" in invoke("mode=analyze", f"pgn={path}", cwd=tmp_path)
    assert path.with_suffix(".yaml").is_file()


def test_completed_games_are_scored(tmp_path):
    path = tmp_path / "mate.pgn"
    invoke(
        "mode=match",
        "match.games=2",
        "engine.book=null",
        "engine.depth=2",
        "position=7k/5Q2/6K1/8/8/8/8/8 w - - 0 1",
        f"match.output={path}",
    )
    stats = analyze(path, "MyAI")
    assert stats["games"] == 2
    assert stats["wins"] == stats["losses"] == 1


def test_move_and_hydra_overrides_from_another_directory(tmp_path):
    move = invoke(
        "mode=move",
        "engine=easy",
        "engine.book=null",
        "engine.time_ms=100",
        "moves=[e2e4,e7e5]",
        cwd=tmp_path,
    ).strip()
    board = chess.Board()
    board.push_uci("e2e4")
    board.push_uci("e7e5")
    assert chess.Move.from_uci(move) in board.legal_moves


def test_repository_stays_shallow_and_small():
    folders = ["core", "ui", "services", "utils", "config", "assets", "tests"]
    for folder in folders:
        for path in (ROOT / folder).rglob("*"):
            if "__pycache__" not in path.parts and path.is_dir():
                assert len(path.relative_to(ROOT).parts) <= 2
        for path in (ROOT / folder).rglob("*.py"):
            assert len(path.read_text().splitlines()) <= 200, path
    assert not (ROOT / "chess.py").exists()
