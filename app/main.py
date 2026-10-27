"""World Map desktop app.

The page is copied to %APPDATA%\\WorldMap\\www on first run. Once a year the app
re-downloads World Bank data and the latest palantir.json from GitHub and
rebuilds the map data in the background.
"""
import datetime
import json
import os
import shutil
import sys
import threading
import urllib.request

import webview

import build_data

APP_VERSION = "1.1.0"
REPO = "eyad28607-cell/world-map"
PALANTIR_URL = f"https://raw.githubusercontent.com/{REPO}/main/app/assets/palantir.json"
UPDATE_EVERY_DAYS = 365

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
BUNDLED = os.path.join(BASE, "assets")
HOME = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "WorldMap")
WWW = os.path.join(HOME, "www")
STATE = os.path.join(HOME, "state.json")


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(st):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f)


def prepare():
    """Copy the bundled page out on first run or after an app upgrade."""
    st = load_state()
    if st.get("version") != APP_VERSION or not os.path.exists(os.path.join(WWW, "index.html")):
        shutil.copytree(BUNDLED, WWW, dirs_exist_ok=True)
        with open(os.path.join(BUNDLED, "meta.json"), encoding="utf-8") as f:
            built = json.load(f)["built"]
        st = {"version": APP_VERSION, "last_update": built}
        save_state(st)
    return st


def update_if_due(window, st):
    last = datetime.date.fromisoformat(st.get("last_update", "2000-01-01"))
    if (datetime.date.today() - last).days < UPDATE_EVERY_DAYS:
        return
    try:
        rows = build_data.build_rows(*build_data.fetch_worldbank())
        try:
            with urllib.request.urlopen(PALANTIR_URL, timeout=30) as r:
                pal = json.loads(r.read().decode("utf-8"))
            with open(os.path.join(WWW, "palantir.json"), "w", encoding="utf-8") as f:
                json.dump(pal, f, ensure_ascii=False, indent=1)
        except (OSError, ValueError):
            with open(os.path.join(WWW, "palantir.json"), encoding="utf-8") as f:
                pal = json.load(f)
        build_data.write(rows, pal, WWW)
    except (OSError, ValueError, KeyError, IndexError):
        return  # offline or source changed; keep current data and try next launch
    st["last_update"] = datetime.date.today().isoformat()
    save_state(st)
    window.evaluate_js("location.reload()")


def main():
    os.makedirs(HOME, exist_ok=True)
    st = prepare()
    window = webview.create_window("World Map: Offline & Palantir", os.path.join(WWW, "index.html"),
                                   width=1280, height=820, min_size=(700, 500))
    webview.start(lambda: threading.Thread(target=update_if_due, args=(window, st), daemon=True).start(),
                  icon=os.path.join(BASE, "icon.ico"))


if __name__ == "__main__":
    main()
