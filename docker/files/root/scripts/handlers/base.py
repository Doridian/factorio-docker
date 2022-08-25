from abc import ABC, abstractmethod


class ConsoleLineHandler(ABC):
    def __init__(self, game):
        self.game = game

    @abstractmethod
    def handle_line(self, line: str):
        pass


class ChatPlayer():
    def __init__(self, game, name: str):
        self.name = name
        self.game = game

    def send_message(self, message: str):
        self.game.send_console(message)

    @staticmethod
    def get_by_name(game, name: str):
        return ChatPlayer(game, name)


class ChatHandler(ABC):
    def __init__(self, game):
        self.game = game

    @abstractmethod
    def handle_chat(self, player: ChatPlayer, message: str):
        pass
