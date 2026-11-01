"""Pack a game's sounds and transcripts into one zip to send to whoever edits them.

usage: pack.py GAME_DIR [-o OUT.zip]

Only what editing needs goes in: the sounds lines.csv names, lines.csv, and a "Start here" page that opens the
editor. The rest of the game stays out. Unzipped, the folder is what the editor's "Choose game folder" expects.
"""
import argparse, csv, os, sys, zipfile

EDITOR = "https://guillotine-mods.github.io/transcript-editor/"
START = f"""<!doctype html>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0;url={EDITOR}">
<title>Transcript Editor</title>
<a href="{EDITOR}">Open the Transcript Editor</a>
"""


def pack(game_dir, out):
    lines = os.path.join(game_dir, "transcripts", "lines.csv")
    with open(lines, encoding="utf-8-sig", newline="") as fh:
        files = [r["file"] for r in csv.DictReader(fh)]
    root = os.path.basename(os.path.abspath(game_dir))
    missing = 0
    with zipfile.ZipFile(out + ".tmp", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{root}/Start here.html", START)
        z.write(lines, f"{root}/transcripts/lines.csv")
        for f in files:
            src = os.path.join(game_dir, f)
            if os.path.exists(src):
                z.write(src, f"{root}/{f}")
            else:
                missing += 1
                print(f"not packed, no such sound: {f}", file=sys.stderr)
    os.replace(out + ".tmp", out)
    return len(files) - missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game_dir")
    ap.add_argument("-o", "--out", help="default: GAME.zip here")
    a = ap.parse_args()
    out = a.out or os.path.basename(os.path.abspath(a.game_dir)) + ".zip"
    n = pack(a.game_dir, out)
    print(f"{n} sounds -> {out}, {os.path.getsize(out) / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
