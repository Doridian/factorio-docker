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

class AsynchronousFileReader(Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd):
        assert callable(fd.readline)
        Thread.__init__(self, daemon=True)
        self._fd = fd
        self.queue = Queue()

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self.queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
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
    def __init__(self, args, pause_during_join, cmdin=None):
        self.args = args
        self.cmdin = cmdin
        self.pause_during_join = pause_during_join
        self.process = None
        self.peers = {}
        self.paused_states = set(["Ready", "ConnectedWaitingForMap", "ConnectedDownloadingMap", "ConnectedLoadingMap", "TryingToCatchUp", "WaitingForCommandToStartSendingTickClosures"])
        self.is_paused = False

    def send_lua(self, command):
        self.send_console(f"/sc {command}\n")

    def send_console(self, line):
        self.process.stdin.write(line)
        self.process.stdin.flush()

    def stop(self):
        if self.process is not None:
            self.process.send_signal(SIGINT)

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
            # Show what we received from standard output.
            while not stdout_reader.queue.empty():
                line = stdout_reader.queue.get()
                self.handle_line(line, stdout)

            # Show what we received from standard error.
            while not stderr_reader.queue.empty():
                line = stderr_reader.queue.get()
                self.handle_line(line, stderr)

            while cmdin_reader is not None and not cmdin_reader.queue.empty():
                self.send_console(cmdin_reader.queue.get())

            # Sleep a bit before asking the readers again.
            sleep(.1)

        # Close subprocess' file descriptors.
        self.process.stdout.close()
        self.process.stderr.close()
        self.process.stdin.close()

        # Let's be tidy and join the threads we've started.
        stdout_reader.join()
        stderr_reader.join()

        self.process.wait()
        self.process = None

    def handle_autopause(self):
        should_pause = False
        for peer_id, state in self.peers.items():
            if state in self.paused_states:
                should_pause = True
                break

        if should_pause == self.is_paused:
            return

        write_stderr(f"Setting game pause to {should_pause}\n")

        if should_pause:
            self.send_lua("game.tick_paused = true; game.print(\"Pausing game for joining player\")")
        else:
            self.send_lua("game.tick_paused = false; game.print(\"Unpausing game as join finished\")")

        self.is_paused = should_pause

    def handle_add_peer(self, line):
        m = search("adding peer *\\((\\d+)\\)", line)
        if not m:
            return
        peer_id = m[1]
        self.peers[peer_id] = "Ready"

    def handle_state_changed(self, line):
        m = search("received stateChanged peerID *\\((\\d+)\\) oldState *\\(([^()]+)\\) newState *\\(([^()]+)\\)", line)
        if not m:
            return
        peer_id = m[1]
        new_state = m[3]
        self.peers[peer_id] = new_state

    def handle_remove_peer(self, line):
        m = search("removing peer *\\((\\d+)\\)", line)
        if not m:
            return
        peer_id = m[1]
        if peer_id in self.peers:
            self.peers.pop(peer_id)

    def handle_line(self, line, stream):
        stream.write(line)
        stream.flush()

        if not self.pause_during_join:
            return

        if 'received stateChanged' in line:
            self.handle_state_changed(line)
        elif 'adding peer' in line:
            self.handle_add_peer(line)
        elif 'removing peer' in line:
            self.handle_remove_peer(line)
        else:
            return

        self.handle_autopause()

def main():
    pause_env_var = getenv("PAUSE_DURING_JOIN", "false").lower()
    pause_during_join = len(pause_env_var) > 0 and pause_env_var != "false"

    suexec()
    game = FactorioGame(args=argv[1:], pause_during_join=pause_during_join, cmdin=stdin)
    
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
