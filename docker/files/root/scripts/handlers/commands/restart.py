from .base import ChatCommand
from handlers.base import ChatPlayer
from threading import Thread

class LoadSaveCommand(ChatCommand):
    def run(self, player: ChatPlayer, args: list[str]):
        thread = Thread(name="Server restart", target=self.player.game.restart)
        thread.start()

    def names(self) -> list[str]:
        return ["restart"]

