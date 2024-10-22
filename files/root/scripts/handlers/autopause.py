from .base import ConsoleLineHandler
from re import search


class AutoPauseHandler(ConsoleLineHandler):
    def __init__(self, game):
        super().__init__(game)
        self.peers = {}
        self.is_paused = False
        self.paused_states = set(["Ready", "ConnectedWaitingForMap", "ConnectedDownloadingMap",
                                 "ConnectedLoadingMap", "TryingToCatchUp", "WaitingForCommandToStartSendingTickClosures"])

    def handle_line(self, line: str):
        if "received stateChanged" in line:
            self.handle_state_changed(line)
        elif "adding peer" in line:
            self.handle_add_peer(line)
        elif "removing peer" in line:
            self.handle_remove_peer(line)
        else:
            return

        self.handle_autopause()

    def handle_autopause(self):
        should_pause = False
        for _, state in self.peers.items():
            if state in self.paused_states:
                should_pause = True
                break

        if should_pause == self.is_paused:
            return

        self.game.write_stderr(f"Setting game pause to {should_pause}\n")

        if should_pause:
            self.game.send_console("/pause")
            self.game.send_console("Pausing game for joining player")
        else:
            self.game.send_console("/unpause")
            self.game.send_console("Unpausing game as join finished")

        self.is_paused = should_pause

    def handle_add_peer(self, line):
        m = search("adding peer *\\((\\d+)\\)", line)
        if not m:
            return
        peer_id = m[1]
        self.peers[peer_id] = "Ready"

    def handle_state_changed(self, line):
        m = search(
            "received stateChanged peerID *\\((\\d+)\\) oldState *\\(([^()]+)\\) newState *\\(([^()]+)\\)", line)
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
