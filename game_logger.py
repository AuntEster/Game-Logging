"""
Game session logger: tracks when the active game starts and ends,
resolving exe names to SteamGridDB game titles via seeded AppID mappings.
"""

import os
import sqlite3
import time
from datetime import datetime
from collections import defaultdict

from dotenv import load_dotenv
import psutil
import requests
import win32gui, win32process

load_dotenv()
DB_FILE = "game_session.db"
STEAMGRID_API_KEY = os.getenv("STEAMGRID_API_KEY")
HEADERS = {"Authorization": f"Bearer {STEAMGRID_API_KEY}"}

BASE_URL = "https://www.steamgriddb.com/api/v2"
STEAM_APP_IDS = {
    "warframe.x64.exe": 230410,
    "marvelrivals.exe": 658940,
    "helldivers2.exe": 553850,
}

CHECK_INTERVAL = 3  # seconds


def get_active_process() -> str | None:
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None
    _, pid = win32process.GetWindowThreadProcessId(hwnd)

    try:
        return psutil.Process(pid).name()  # Warframe.exe
    except psutil.NoSuchProcess:
        return None


def lookup_game(exe_name: str) -> str | None:
    base = exe_name.lower()
    appid = STEAM_APP_IDS.get(base)
    if not appid:
        return None

    url = f"{BASE_URL}/games/steam/{appid}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=3)
        response.raise_for_status()
        data = response.json().get("data", {})
        return data.get("name")
    except Exception as e:
        print(f"SteamGridDB lookup failed for AppID {appid}: {e}")
        return None


def get_window_title() -> str:
    """return title of active window"""
    return win32gui.GetWindowText(win32gui.GetForegroundWindow()).strip()


def create_table() -> None:
    """initialize SQLite session table if it doesn't exist"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            process_name TEXT, window_title TEXT, 
            start_time TEXT, end_time TEXT)"""
    )
    conn.commit()
    conn.close()


def log_sesh_start(proc_name: str, title: str) -> None:
    """insert new session row with a NULL end time"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """INSERT INTO sessions 
        (process_name, window_title, start_time, end_time) 
        VALUES (?,?,?, NULL) """,
        (proc_name, title, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def log_sesh_end(proc_name):
    """mark most recent session as ended"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """UPDATE sessions 
        SET end_time = ? 
        WHERE process_name = ? AND end_time IS NULL""",
        (datetime.now().isoformat(), proc_name),
    )
    conn.commit()
    conn.close()


def main() -> None:
    """main: detect start/end sessions"""
    print("Game logger started")
    create_table()

    current_game: str | None = None
    current_title: str | None = None

    while True:
        exe = get_active_process()
        title = get_window_title()
        friend = lookup_game(exe) if exe else None

        if current_game and friend != current_game:
            print(f"[END] {current_game}")
            log_sesh_end(current_game)
            current_game = None

        if friend and friend != current_game:
            print(f"[START] {friend} - {title}")
            log_sesh_start(friend, title)
            current_game = friend
            current_title = title

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
