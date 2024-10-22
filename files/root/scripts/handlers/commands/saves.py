from dataclasses import dataclass
from .base import ChatCommand
from handlers.base import ChatPlayer
from os import getenv, lstat, scandir, stat_result, utime, rename
from datetime import datetime, timezone
from os.path import join
from shutil import copyfile
from threading import Thread

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
    path: str
    stat: stat_result


def savegame_info_from_file(name: str) -> SaveGameInfo:
    path_name = join(SAVE_DIR, name)
    stat = lstat(path_name)
    return SaveGameInfo(
        name=name,
        mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        size=stat.st_size,
        stat=stat,
        path=path_name,
    )


class ListSavesCommand(ChatCommand):
    def run(self, player: ChatPlayer, args: list[str]):
        savegames: list[SaveGameInfo] = []

        dirlist = scandir(SAVE_DIR)
        for dirent in dirlist:
            if dirent.name[0] == ".":
                continue

            if not dirent.is_file():
                continue

            savegames.append(savegame_info_from_file(dirent.name))

        savegames.sort(key=lambda sg: sg.mtime, reverse=True)

        now_time = datetime.now(tz=timezone.utc)

        for sg in savegames:
            player.send_message(
                f"{sg.name} @ {format_relative_date(sg.mtime, now_time)} ({format_file_size(sg.size)})")

    def names(self) -> list[str]:
        return ["savelist"]


class LoadSaveThread(Thread):
    def __init__(self, player: ChatPlayer, savegame: SaveGameInfo) -> None:
        super().__init__()
        self.name = "Savegame Loader Thread"
        self.player = player
        self.savegame = savegame

    def run(self):
        tmp_filename = join(
            SAVE_DIR, f"saveload_{int(datetime.now().timestamp())}.tmp")
        zip_filename = f"{tmp_filename}.zip"

        self.player.send_message(f"Copying save to {zip_filename}...")
        copyfile(self.savegame.path, tmp_filename)
        self.player.send_message(
            "Save copied! Stopping server and reloading...")

        self.player.game.stop()
        self.player.game.wait()

        rename(tmp_filename, zip_filename)
        utime(zip_filename)

        self.player.game.restart()


class LoadSaveCommand(ChatCommand):
    def run(self, player: ChatPlayer, args: list[str]):
        sg_name = args[0]
        savegame = savegame_info_from_file(sg_name)

        thread = LoadSaveThread(player, savegame)
        thread.start()

    def names(self) -> list[str]:
        return ["saveload"]
