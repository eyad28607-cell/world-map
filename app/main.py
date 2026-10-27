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

APP_VERSION = "1.5.0"
REPO = "eyad28607-cell/world-map"
PALANTIR_URL = f"https://raw.githubusercontent.com/{REPO}/main/app/assets/palantir.json"
TOPICS_URL = f"https://raw.githubusercontent.com/{REPO}/main/app/assets/topics.js"
UPDATE_EVERY_DAYS = 365

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
BUNDLED = os.path.join(BASE, "assets")
if sys.platform == "win32":
    HOME = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "WorldMap")
elif sys.platform == "darwin":
    HOME = os.path.expanduser("~/Library/Application Support/WorldMap")
else:
    HOME = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "WorldMap")
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
        countries, net, pop = build_data.fetch_worldbank()
        rows = build_data.build_rows(countries, net, pop)
        try:
            with urllib.request.urlopen(PALANTIR_URL, timeout=30) as r:
                pal = json.loads(r.read().decode("utf-8"))
            with open(os.path.join(WWW, "palantir.json"), "w", encoding="utf-8") as f:
                json.dump(pal, f, ensure_ascii=False, indent=1)
        except (OSError, ValueError):
            with open(os.path.join(WWW, "palantir.json"), encoding="utf-8") as f:
                pal = json.load(f)
        try:  # hand-written topic pages (e.g. Israel and Palestine), as edited on GitHub
            with urllib.request.urlopen(TOPICS_URL, timeout=30) as r:
                topics = r.read()
            if topics.startswith(b"// Hand-written topic pages"):
                with open(os.path.join(WWW, "topics.js"), "wb") as f:
                    f.write(topics)
        except OSError:
            pass
        build_data.write(rows, pal, WWW)
        build_data.refresh_extra(countries, WWW, log=lambda m: None)
    except (OSError, ValueError, KeyError, IndexError):
        return  # offline or source changed; keep current data and try next launch
    st["last_update"] = datetime.date.today().isoformat()
    save_state(st)
    window.evaluate_js("location.reload()")


# Checks run by the self-test: (name, JavaScript that returns true when that part works)
SELF_TEST = [
    ("map draws countries", "document.querySelectorAll('#map path.choroplethlocation').length > 150"),
    ("guide opens", "document.getElementById('bg').click(); !reader.hidden && document.querySelectorAll('#rbody .gitem').length > 50"),
    ("country page", "closeReader(); country(byIso['FRA']); openCountry('FRA'); RB.innerText.includes('France')"),
    ("weapons page", "openEquip('USA','Aircraft & drones'); document.querySelectorAll('#rbody .card').length > 20"),
    ("weapon detail", "document.querySelector('#rbody .card').click(); !!document.querySelector('#rbody .detail')"),
    ("world catalogue", "openCatalog(); document.querySelectorAll('#rbody .tile').length > 5"),
    ("world units", "openWorldUnits('Special forces'); document.querySelectorAll('#rbody .card').length > 20"),
    ("conflicts page", "openConflicts('UKR'); document.querySelectorAll('#rbody .ccard').length > 0"),
    ("Israel-Palestine page", "openTopic('israel-palestine'); document.querySelectorAll('#rbody .tl').length > 10"),
    ("photos load offline", "[...document.querySelectorAll('#rbody img')].some(i => i.complete && i.naturalWidth > 0)"),
]


def self_test(window, out_path):
    """Opens every main page in the real app window, writes the results to out_path and closes the app."""
    import time
    time.sleep(8)
    results = {}
    for name, js in SELF_TEST:
        *steps, check = js.split(";")  # run the steps, then return the final check
        try:
            results[name] = bool(window.evaluate_js(
                f"(() => {{ try {{ {';'.join(steps)}; return !!({check}); }} catch (e) {{ return false; }} }})()"))
        except Exception:
            results[name] = False
        time.sleep(1)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    window.destroy()


def main():
    os.makedirs(HOME, exist_ok=True)
    st = prepare()
    window = webview.create_window("World Map", os.path.join(WWW, "index.html"),
                                   width=1280, height=820, min_size=(700, 500))
    test_out = os.environ.get("WORLDMAP_SELFTEST")
    task = (lambda: threading.Thread(target=self_test, args=(window, test_out), daemon=True).start()) if test_out else \
        (lambda: threading.Thread(target=update_if_due, args=(window, st), daemon=True).start())
    webview.start(task, icon=os.path.join(BASE, "icon.png" if sys.platform != "win32" else "icon.ico"))


if __name__ == "__main__":
    main()
