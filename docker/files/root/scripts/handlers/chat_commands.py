from traceback import print_exc
from .base import ChatHandler, ChatPlayer
from .commands.base import ChatCommand


class ChatCommandHandler(ChatHandler):
    commands: list[ChatCommand]

    def __init__(self, game):
        super().__init__(game)
        self.commands = {}

    def register_command(self, command: ChatCommand):
        for name in command.names():
            self.commands[name.lower()] = command

    def handle_chat(self, player: ChatPlayer, message: str):
        if message[0] != "!":
            return

        args = message[1:].split(" ")
        cmd_name = args[0].lower()
        if cmd_name not in self.commands:
            player.send_message(f"Unknown command: {cmd_name}")
            return

        cmd = self.commands[cmd_name]
        args = args[1:]

        try:
            cmd.run(player, args)
        except Exception as e:
            player.send_message(f"Error during command: {e}")
            print_exc()
