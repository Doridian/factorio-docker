#!/usr/bin/env python3

from sys import stderr, stdout, stdin, argv
from os import setresgid, setresuid, getuid, getenv
from pwd import getpwnam
from subprocess import Popen, PIPE
from threading import Thread
from queue import Queue
from time import sleep
from re import search
from signal import signal, SIGHUP, SIGTERM, SIGINT
from traceback import print_exc
from handlers.base import ConsoleLineHandler, ChatHandler, ChatPlayer
from handlers.autopause import AutoPauseHandler
from handlers.chat_commands import ChatCommandHandler
from handlers.commands.saves import LoadSaveCommand, ListSavesCommand

class AsynchronousFileReader(Thread):
    def __init__(self, fd):
        assert callable(fd.readline)
        Thread.__init__(self, daemon=True)
        self._fd = fd
        self.queue = Queue()

    def run(self):
        for line in iter(self._fd.readline, ""):
            self.queue.put(line)

    def eof(self):
        return not self.is_alive() and self.queue.empty()

def write_stderr(text):
    stderr.write(text)
    stderr.flush()

def suexec():
    write_stderr("Switching users...")
    current_uid = getuid()
    if current_uid != 0:
        write_stderr(" Not root, skipping!\n")
        return

    user = getpwnam("factorio")
    uid = user.pw_uid
    gid = user.pw_gid
    setresgid(gid, gid, gid)
    setresuid(uid, uid, uid)
    write_stderr(" Done!\n")

class FactorioGame:
    args: list[str]
    process: Popen
    console_line_handlers: list[ConsoleLineHandler]
    chat_handlers: list[ChatHandler]

    def __init__(self, args, cmdin=None):
        self.args = args
        self.cmdin = cmdin
        self.process = None
        self.console_line_handlers = []
        self.chat_handlers = []

    def send_console(self, line):
        self.process.stdin.write(f"{line.strip()}\n")
        self.process.stdin.flush()

    def write_stderr(self, text):
        write_stderr(text)

    def stop(self):
        if self.process is not None:
            self.process.send_signal(SIGINT)

    def wait(self):
        if self.process is not None:
            self.process.wait()

    def run(self):
        self.process = Popen(self.args, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding="utf-8")

        stdout_reader = AsynchronousFileReader(self.process.stdout)
        stdout_reader.start()
        stderr_reader = AsynchronousFileReader(self.process.stderr)
        stderr_reader.start()

        cmdin_reader = None
        if self.cmdin is not None:
            cmdin_reader = AsynchronousFileReader(self.cmdin)
            cmdin_reader.start()

        while not stdout_reader.eof() or not stderr_reader.eof():
            while not stdout_reader.queue.empty():
                line = stdout_reader.queue.get()
                self.handle_line(line, stdout)

            while not stderr_reader.queue.empty():
                line = stderr_reader.queue.get()
                self.handle_line(line, stderr)

            while cmdin_reader is not None and not cmdin_reader.queue.empty():
                self.send_console(cmdin_reader.queue.get())

            sleep(.1)

        self.process.stdout.close()
        self.process.stderr.close()
        self.process.stdin.close()

        stdout_reader.join()
        stderr_reader.join()

        self.process.wait()
        self.process = None

    def handle_chat_line(self, line):
        m = search("\\[CHAT\\] ([^:]+): (.*)$", line)
        if not m:
            return

        player_name = m[1]
        message = m[2].strip()
        
        for handler in self.chat_handlers:
            handler.handle_chat(ChatPlayer.get_by_name(self, player_name), message)

    def handle_line(self, line, stream):
        stream.write(line)
        stream.flush()

        try:
            if "[CHAT]" in line:
                self.handle_chat_line(line)
                return

            for handler in self.console_line_handlers:
                handler.handle_line(line)
        except Exception:
            print_exc()

def main():
    pause_env_var = getenv("PAUSE_DURING_JOIN", "false").lower()
    pause_during_join = len(pause_env_var) > 0 and pause_env_var != "false"

    suexec()
    game = FactorioGame(args=argv[1:], cmdin=stdin)

    if pause_during_join:
        game.console_line_handlers.append(AutoPauseHandler(game))

    command_handler = ChatCommandHandler(game)
    command_handler.register_command(LoadSaveCommand())
    command_handler.register_command(ListSavesCommand())
    game.chat_handlers.append(command_handler)
    
    should_run = True
    def sighandler_exit(signum, frame):
        nonlocal should_run
        should_run = False
        game.stop()

    signal(SIGINT, sighandler_exit)
    signal(SIGHUP, sighandler_exit)
    signal(SIGTERM, sighandler_exit)

    if should_run:
        game.run()

if __name__ == "__main__":
    main()
