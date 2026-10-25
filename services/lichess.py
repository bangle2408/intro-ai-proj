import logging
from threading import Thread

import requests

from services.lichess_client import LichessClient
from services.lichess_games import LichessGames


class LichessBot(LichessGames, LichessClient):
    def __init__(self, cfg):
        super().__init__(cfg)
        if not cfg.lichess.token:
            raise ValueError("Set LICHESS_TOKEN before starting mode=lichess")
        self.games = {}
        self.engines = {}

    def accept_challenge(self, challenge):
        settings = self.cfg.lichess
        clock = challenge.get("timeControl", {})
        allowed = (
            settings.accept_challenges
            and len(self.games) < settings.max_games
            and challenge.get("variant", {}).get("key") == "standard"
            and clock.get("type") == "clock"
            and clock.get("limit", 0) >= settings.min_seconds
            and (settings.rated or not challenge.get("rated", False))
        )
        action = "accept" if allowed else "decline"
        self.request("POST", f"/challenge/{challenge['id']}/{action}")

    def handle_event(self, event):
        if event.get("type") == "challenge":
            challenge = event["challenge"]
            if challenge.get("challenger", {}).get("id", "").casefold() != self.account_id:
                self.accept_challenge(challenge)
        elif event.get("type") == "gameStart":
            game_id = event["game"]["id"]
            if game_id not in self.games:
                worker = Thread(target=self.play_game, args=(game_id,), daemon=True)
                self.games[game_id] = worker
                worker.start()

    def run(self):
        account = self.request("GET", "/account").json()
        if account.get("title") != "BOT":
            raise ValueError("Lichess account must have BOT status")
        self.account_id = account["id"].casefold()
        settings = self.cfg.lichess
        if settings.challenge_bot:
            self.request(
                "POST",
                f"/challenge/{settings.challenge_bot}",
                data={
                    "clock.limit": settings.challenge_seconds,
                    "clock.increment": settings.challenge_increment,
                    "rated": str(settings.rated).lower(),
                    "variant": "standard",
                },
            )
        try:
            while not self.stopped.is_set():
                try:
                    for event in self.stream("/stream/event"):
                        self.handle_event(event)
                except (requests.RequestException, ValueError) as error:
                    logging.warning("Lichess connection: %s", error)
                self.stopped.wait(settings.retry_seconds)
        except KeyboardInterrupt:
            pass
        finally:
            self.stopped.set()
            for engine in list(self.engines.values()):
                engine.stop()


def run(cfg):
    LichessBot(cfg).run()
