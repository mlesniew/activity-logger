#!/usr/bin/env python3
import argparse
import dataclasses
import datetime
import re
import subprocess
import time

PATTERN = re.compile("0x([0-9a-f]+) +(-?[0-9]+) (.*?)  +([^ ]+) (.*)", re.I)


@dataclasses.dataclass(frozen=True)
class Window:
    window_id: int
    desktop: int
    cls: str
    hostname: str
    title: str


def iter_windows():
    for line in subprocess.check_output(
        ["wmctrl", "-x", "-l"], encoding="utf-8"
    ).splitlines():
        match = PATTERN.match(line)
        if not match:
            continue
        wid, desktop, cls, hostname, title = match.groups()
        yield Window(int(wid, 16), int(desktop), cls, hostname, title)


def get_active_window_id():
    return int(subprocess.check_output(["xdotool", "getwindowfocus"]))


def log():
    timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
    active_window_id = get_active_window_id()
    windows = {win.window_id: win for win in iter_windows()}
    for window in iter_windows():
        active = int(window.window_id == active_window_id)
        print(f"{timestamp}\t{active}\t{window.cls}\t{window.title}")


def main():
    while True:
        log()
        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit
