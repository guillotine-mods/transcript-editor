"""Start the transcripts of a game: write GAME_DIR/transcripts/lines.csv, which the editor opens and saves.

usage: prepare.py GAME_DIR [--lines CSV] [--rename OLD=NEW ...] [--lang he] [--model REPO] [--no-whisper]

Every sound under GAME_DIR gets a row; `file` is its path under GAME_DIR, and the row order is the order of
conversations and of lines. Rows of --lines are kept in their order; their `file` may be any path that ends
with the clip's path under GAME_DIR. Clips with no row get a Whisper transcript (cached in
transcripts/.whisper, so a stopped run resumes) and are added at the end, grouped by folder.
"""
import argparse, csv, json, os, re, sys

COLUMNS = ["file", "conversation", "speaker", "text", "status", "note"]
AUDIO = (".aif", ".aiff", ".aifc", ".wav", ".ogg", ".oga", ".opus", ".mp3", ".m4a", ".flac")


def natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def is_sound(path):
    if path.lower().endswith(AUDIO):
        return True
    if "." in os.path.basename(path):
        return False
    with open(path, "rb") as fh:  # some games' sounds have no extension
        return fh.read(4) in (b"OggS", b"FORM", b"RIFF")


def clips(root):
    for d, dirs, files in os.walk(root, followlinks=True):
        dirs[:] = [x for x in dirs if not x.startswith(".") and not (d == root and x == "transcripts")]
        for f in files:
            if not f.startswith(".") and is_sound(os.path.join(d, f)):
                yield os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")


def write(path, text):
    with open(path + ".tmp", "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(path + ".tmp", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game_dir")
    ap.add_argument("--lines", help="existing CSV with at least file and text columns")
    ap.add_argument("--rename", action="append", default=[], help="rename a CSV column, e.g. scene=conversation")
    ap.add_argument("--lang", default="he", help="Whisper language code")
    ap.add_argument("--model", default="mlx-community/whisper-large-v3-mlx")
    ap.add_argument("--no-whisper", action="store_true", help="leave text empty for clips without a row")
    a = ap.parse_args()

    out_dir = os.path.join(a.game_dir, "transcripts")
    out_csv = os.path.join(out_dir, "lines.csv")
    if os.path.exists(out_csv):  # it may hold edits; never overwrite them
        sys.exit(f"{out_csv} exists; it may hold edits, so it is left alone")

    rows, header = [], list(COLUMNS)
    if a.lines:
        ren = dict(r.split("=", 1) for r in a.rename)
        with open(a.lines, encoding="utf-8-sig", newline="") as fh:
            rd = csv.DictReader(fh)
            src_cols = [ren.get(c, c) for c in rd.fieldnames]
            for r in rd:
                rows.append({ren.get(k, k): v for k, v in r.items()})
        header += [c for c in src_cols if c not in header]
        if "file" not in src_cols or "text" not in src_cols:
            sys.exit("the lines CSV needs a file and a text column (use --rename)")

    by_suffix = {}  # every trailing part of each row's path -> rows, so a/b/c.aif matches clip b/c.aif
    for r in rows:
        parts = r["file"].replace("\\", "/").lower().split("/")
        for i in range(len(parts)):
            by_suffix.setdefault("/".join(parts[i:]), []).append(r)

    matched, new = {}, []
    game = os.path.basename(os.path.abspath(a.game_dir)).lower()
    for rel in sorted(clips(a.game_dir), key=natural):
        # a CSV of several games (piposh2/SOUNDS/X.AIF, piposh-dream/SOUNDS/X.AIF) is told apart by the folder's name
        hit = by_suffix.get(f"{game}/{rel.lower()}") or by_suffix.get(rel.lower(), [])
        if len(hit) == 1 and id(hit[0]) not in matched:
            matched[id(hit[0])] = rel
        else:
            if len(hit) > 1:
                print(f"{rel}: {len(hit)} CSV rows match it; treated as a new clip", file=sys.stderr)
            new.append(rel)

    whisper = None
    if new and not a.no_whisper:
        try:
            import mlx_whisper as whisper
        except ImportError:
            sys.exit(f"{len(new)} clips need Whisper: pip install mlx-whisper, or pass --no-whisper")

    keep, dropped = [], [r["file"] for r in rows if id(r) not in matched]
    if dropped:
        print(f"{len(dropped)} CSV rows have no clip under {a.game_dir} and were left out, e.g. {dropped[0]}", file=sys.stderr)
    for r in rows:
        rel = matched.get(id(r))
        if rel is not None:
            r["file"] = rel
            r["conversation"] = r.get("conversation") or os.path.dirname(rel) or "(top)"
            r["status"] = r.get("status") or "raw"
            keep.append(r)
    from_csv = len(keep)

    cache = os.path.join(out_dir, ".whisper")
    for i, rel in enumerate(new):
        text, silent = "", False
        if whisper:
            c = os.path.join(cache, rel + ".json")
            if not os.path.exists(c):
                try:
                    res = whisper.transcribe(os.path.join(a.game_dir, rel), path_or_hf_repo=a.model, language=a.lang,
                                             condition_on_previous_text=False, verbose=None)
                except RuntimeError:  # a damaged clip; not cached, so a repaired one is tried again
                    print(f"skip {rel}: ffmpeg can't read it", file=sys.stderr)
                    keep.append({"file": rel, "conversation": os.path.dirname(rel) or "(top)", "status": "raw",
                                 "note": "Not transcribed: the sound file is damaged. Needs doing by hand."})
                    continue
                os.makedirs(os.path.dirname(c), exist_ok=True)
                segs = res["segments"]
                # Whisper rarely returns nothing on effects and music; it hallucinates ("תודה רבה"), so trust its own scores
                silent = not segs or all(g["no_speech_prob"] > 0.6 for g in segs) or \
                    sum(g["avg_logprob"] for g in segs) / len(segs) < -1.0
                write(c, json.dumps({"text": res["text"].strip(), "no_speech": silent}, ensure_ascii=False))
            with open(c, encoding="utf-8") as fh:
                got = json.load(fh)
            text, silent = got["text"], got["no_speech"] or not got["text"]
            if i % 50 == 0:
                print(f"whisper {i + 1}/{len(new)} {rel}: {text}", flush=True)
        # a no-speech clip's text is Whisper's hallucination ("תודה."); the cache keeps it
        keep.append({"file": rel, "conversation": os.path.dirname(rel) or "(top)", "text": "" if silent else text,
                     "status": "no_speech" if silent else "raw"})

    os.makedirs(out_dir, exist_ok=True)
    write(os.path.join(out_dir, ".gdignore"), "")  # Godot would import the CSV as a translation
    write(os.path.join(out_dir, ".gitignore"), "lines.backup-*.csv\n.whisper/\n")
    # BOM so Excel reads Hebrew right
    with open(out_csv + ".tmp", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, header, extrasaction="ignore")
        w.writeheader()
        w.writerows(keep)
    os.replace(out_csv + ".tmp", out_csv)
    print(f"{len(keep)} lines ({from_csv} from CSV) -> {out_csv}")


if __name__ == "__main__":
    main()
