from dataclasses import dataclass
import re
from xmlrpc.client import DateTime
from .base import ChatCommand
from handlers.base import ChatPlayer
from os import getenv, scandir
from datetime import datetime, timezone

SAVE_DIR = getenv("SAVES")

# https://stackoverflow.com/a/1094933
def format_file_size(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def format_relative_date(time: datetime, compare: datetime):
    diff = int((compare - time).total_seconds())

    suffix = " ago"
    if diff < 0:
        suffix = " from now"
        diff = -diff

    if diff < 1:
        return "< 1s"
    
    res = [f"{diff % 60}s"]
    
    diff //= 60
    if diff > 0:
        res.append(f"{diff % 60}m")
        diff //= 60
        if diff > 0:
            res.append(f"{diff % 24}h")
            diff //= 24
            if diff > 0:
                res.append(f"{diff}d")

    return "".join(res[::-1]) + suffix

@dataclass
class SaveGameInfo():
    name: str
    mtime: datetime
    size: int

class ListSavesCommand(ChatCommand):
    def run(self, player: ChatPlayer, args: list[str]):
        savegames: list[SaveGameInfo] = []

        dirlist = scandir(SAVE_DIR)
        for dirent in dirlist:
            if dirent.name[0] == ".":
                continue
        
            if not dirent.is_file():
                continue

            stat = dirent.stat()
            savegames.append(SaveGameInfo(
                name=dirent.name,
                mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                size=stat.st_size,
            ))

        savegames.sort(key=lambda sg : sg.mtime, reverse=True)

        now_time = datetime.now(tz=timezone.utc)

        for sg in savegames:
            player.send_message(f"{sg.name} @ {format_relative_date(sg.mtime, now_time)} ({format_file_size(sg.size)})")

    def names(self) -> list[str]:
        return ["savelist"]

class LoadSaveCommand(ChatCommand):
    def run(self, player: ChatPlayer, args: list[str]):
        player.send_message("Load")

    def names(self) -> list[str]:
        return ["saveload"]
