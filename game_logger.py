import psutil
import win32gui
import sqlite3
import time
import requests
from datetime import datetime
from collections import defaultdict

DB_FILE = "game_session.db"
STEAMGRID_API_KEY = "c991fa1b67b225a1dd12f28a4dced45c"
HEADERS = {"Authorization": f"Bearer {STEAMGRID_API_KEY}"}
CHECK_INTERVAL = 3  # seconds

known_sessions = {}
last_seen = defaultdict(lambda: time.time())
lookup_cache = {}
# WATCHED_GAMES = ["warframe.x64.exe"]


def lookup_game(exe_name):
    base = exe_name.lower().replace(".exe", "")
    if base in lookup_cache:
        return lookup_cache[base]

    url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{base}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=3)
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])

            for result in results:
                name = result["name"]
                if any(
                    word in name.lower()
                    for word in [
                        "chrome",
                        "discord",
                        "notepad",
                        "service",
                        "helper",
                        "driver",
                        "settings",
                        "studio",
                        "node",
                        "bar",
                        "explorer",
                        "python",
                        "chatgpt",
                    ]
                ):
                    continue  # Filter generic matches for now
                if base in name.lower().replace(" ", ""):
                    lookup_cache[base] = name
                    return name  # Valid match
            return None  # No match with SteamDB
    except Exception as e:
        print(f"Lookup error: {e}")

    lookup_cache[base] = None
    return None


def get_window_title():
    return win32gui.GetWindowText(win32gui.GetForegroundWindow()).strip()


def create_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, process_name TEXT, window_title TEXT, start_time TEXT, end_time TEXT)"""
    )
    conn.commit()
    conn.close()


def log_sesh_start(proc_name, title):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """INSERT INTO sessions (process_name, window_title, start_time, end_time) VALUES (?,?,?, NULL) """,
        (proc_name, title, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def log_sesh_end(proc_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """UPDATE sessions SET end_time = ? WHERE process_name = ? AND end_time IS NULL""",
        (datetime.now().isoformat(), proc_name),
    )
    conn.commit()
    conn.close()


def main():
    print("Game logger started")
    create_table()

    while True:
        active_procs = {
            p.info["pid"]: p.info for p in psutil.process_iter(["pid", "name"])
        }
        current_title = get_window_title()
        active_names = {p["name"].lower() for p in active_procs.values() if p["name"]}

        # Update last seen times
        for name in active_names:
            last_seen[name] = time.time()

        # Start new session if not already known
        for name in active_names:
            if name not in known_sessions:
                game_title = lookup_game(name)
                if game_title:
                    print(f"[START] {game_title} - {current_title}")
                    log_sesh_start(game_title, current_title)
                    known_sessions[name] = current_title

        # End session if not seen for 10+ seconds ---> Edge case for games that have their own launcher (warframe)
        now = time.time()
        for name in list(known_sessions):
            if name not in active_names and now - last_seen[name] > 30:
                search_name = lookup_game(name)
                print(f"[END] {search_name}")
                log_sesh_end(search_name)
                del known_sessions[name]

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
