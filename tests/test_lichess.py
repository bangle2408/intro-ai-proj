from unittest.mock import Mock

import chess
import pytest

from services.lichess import LichessBot


def bot(cfg):
    cfg.lichess.token = "test-token"
    instance = LichessBot(cfg)
    instance.account_id = "testbot"
    instance.request = Mock()
    return instance


def test_lichess_needs_token(cfg):
    cfg.lichess.token = ""
    with pytest.raises(ValueError, match="LICHESS_TOKEN"):
        LichessBot(cfg)


def test_challenge_acceptance_and_variant_filter(cfg):
    instance = bot(cfg)
    challenge = dict(
        id="123",
        variant=dict(key="standard"),
        rated=False,
        timeControl=dict(type="clock", limit=180),
    )
    instance.accept_challenge(challenge)
    instance.request.assert_called_with("POST", "/challenge/123/accept")
    challenge["variant"]["key"] = "atomic"
    instance.accept_challenge(challenge)
    instance.request.assert_called_with("POST", "/challenge/123/decline")


def test_stream_to_legal_move_without_live_network(cfg):
    instance = bot(cfg)
    instance.stream = lambda _: iter(
        [
            dict(
                type="gameFull",
                white=dict(id="testbot"),
                initialFen="startpos",
                state=dict(status="started", moves="", wtime=60000, winc=0),
            ),
            dict(type="gameState", status="mate", moves="e2e4"),
        ]
    )
    instance.play_game("game123")
    method, path = instance.request.call_args.args
    assert method == "POST"
    assert path.startswith("/bot/game/game123/move/")
    assert chess.Move.from_uci(path.rsplit("/", 1)[1]) in chess.Board().legal_moves
    assert "game123" not in instance.engines
