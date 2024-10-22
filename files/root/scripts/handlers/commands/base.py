from abc import ABC, abstractmethod

from handlers.base import ChatPlayer


class ChatCommand(ABC):
    @abstractmethod
    def run(self, player: ChatPlayer, args: list[str]):
        pass

    @abstractmethod
    def names(self) -> list[str]:
        pass
