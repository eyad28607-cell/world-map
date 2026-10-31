"""Packages the app for the current OS into ../dist:
Windows -> WorldMap.exe, macOS -> WorldMap-macOS.zip (WorldMap.app), Linux -> WorldMap-linux.tar.gz.

    pip install pywebview pyinstaller pillow   (Linux: pip install "pywebview[qt]" pyinstaller pillow)
    python build.py
"""
import os
import shutil
import subprocess
import sys

import PyInstaller.__main__

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "..", "dist")
WORK = os.path.join(HERE, "build")
sep = os.pathsep


def main():
    p = lambda name: os.path.join(HERE, name)  # absolute, because the spec file lives in WORK
    icon = p("icon.ico" if sys.platform == "win32" else "icon.png")
    args = [p("main.py"), "--noconfirm", "--windowed", "--name", "WorldMap", "--icon", icon,
            "--add-data", f"{p('assets')}{sep}assets", "--add-data", f"{p('icon.ico')}{sep}.",
            "--add-data", f"{p('icon.png')}{sep}.", "--paths", HERE,
            "--distpath", DIST, "--workpath", WORK, "--specpath", WORK]
    if sys.platform == "darwin":
        args += ["--osx-bundle-identifier", "io.github.worldmap"]
        PyInstaller.__main__.run(args)
        # ditto, not shutil.make_archive: the bundle relies on symlinks, which zipfile turns into empty folders
        out = os.path.join(DIST, "WorldMap-macOS.zip")
        subprocess.run(["ditto", "-c", "-k", "--keepParent", os.path.join(DIST, "WorldMap.app"), out], check=True)
    elif sys.platform == "win32":
        PyInstaller.__main__.run(args + ["--onefile"])
        out = os.path.join(DIST, "WorldMap.exe")
    else:
        PyInstaller.__main__.run(args)  # one folder: Qt WebEngine does not work from a one-file bundle
        out = shutil.make_archive(os.path.join(DIST, "WorldMap-linux"), "gztar", DIST, "WorldMap")
    print("Built", os.path.abspath(out))


if __name__ == "__main__":
    main()
