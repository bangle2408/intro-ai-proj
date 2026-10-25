import pytest

from services.analysis import analyze


def test_score_and_elo_include_draws_and_exclude_unfinished(tmp_path):
    path = tmp_path / "results.pgn"
    games = [
        ("MyAI", "Rival", "1-0"),
        ("Rival", "MyAI", "1/2-1/2"),
        ("MyAI", "Rival", "0-1"),
        ("MyAI", "Rival", "*"),
        ("Other", "Rival", "1-0"),
    ]
    path.write_text(
        "\n\n".join(
            f'[White "{white}"]\n[Black "{black}"]\n[Result "{result}"]\n\n{result}'
            for white, black, result in games
        )
    )
    stats = analyze(path, "MyAI", 1600)
    assert stats["wins"] == stats["draws"] == stats["losses"] == 1
    assert stats["skipped"] == 2
    assert stats["score"] == 0.5
    assert stats["estimated_elo"] == pytest.approx(1600)
