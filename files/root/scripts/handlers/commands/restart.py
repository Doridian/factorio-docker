from .base import ChatCommand
from handlers.base import ChatPlayer
from threading import Thread


class RestartCommand(ChatCommand):
    def run(self, player: ChatPlayer, args: list[str]):
        thread = Thread(name="Server restart", target=player.game.restart)
        thread.start()

    def names(self) -> list[str]:
        return ["restart"]


class StopCommand(ChatCommand):
    def run(self, player: ChatPlayer, args: list[str]):
        thread = Thread(name="Server stop", target=player.game.stop)
        thread.start()

    def names(self) -> list[str]:
        return ["stop", "quit"]
