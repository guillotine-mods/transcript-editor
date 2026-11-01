# Transcript Editor

Listen to a game's recorded lines, fix their text, and put them in order. A web page for the people
editing, at **https://guillotine-mods.github.io/transcript-editor/**, and two Python scripts for whoever
prepares the material. The lines live in the game itself, in `transcripts/lines.csv`; the page reads and
saves them in the folder on your computer and sends nothing anywhere.

## For editors

1. Have the game on your computer: the folder you were sent (unzip it first), its folder from the
   repository, or a copy of the game from the CD (a CD itself can't be saved into).
2. Go to https://guillotine-mods.github.io/transcript-editor/ in **Google Chrome** or **Microsoft Edge**.
   Safari and Firefox can only look, not save. (Without internet, `index.html` from this repository works
   the same when opened in Chrome.)
3. Click **Choose game folder** and pick the game's folder. The browser asks whether this page may edit
   files there: choose **Allow**. Next time, **Continue with …** brings you straight back. A game without
   transcripts yet gets one line for each of its sounds.
4. Pick a conversation on the left; it opens at its first line that is not checked yet. The ▶ beside a
   line plays that line; **▶ Play conversation** plays all of it, skipping sounds that aren't in the
   folder (those lines say "sound not found"). Typing pauses playback.
5. Fix the text and the speaker. When a line is right, press **✓ Next** (or Ctrl+Enter, ⌘+Enter on a Mac):
   it marks the line **Checked** and plays the next line still to check. At the end of a conversation it goes back to
   lines skipped there, then on to the next conversation with work left. The status menu also has
   **Final** (checked again by a second person) and **No speech**. The numbers on the left (`12/30`)
   and at the top count checked lines. **Use this** puts the other version into the text (Ctrl+Z undoes it).
6. Reorder by dragging ⠿, or with ↑ ↓. That works for whole conversations on the left too.

Everything saves by itself into `transcripts/lines.csv` in the game folder; the top right says
**Saved ✓**. Each day the first open also keeps a copy, `transcripts/lines.backup-<date>.csv`,
so nothing is lost for good. If `lines.csv` is changed somewhere else meanwhile (another tab, Excel), the
editor stops saving and asks you to reload, so neither overwrites the other. When done, press
**Download my edits** and send back the file it gives you (`<game>-lines.csv`), or commit
`transcripts/lines.csv` to the game's repository.

Keys: **Ctrl+Enter** ✓ Next; **Esc** plays the line you are typing in again, or stops; **Space**
(outside the text) play the conversation from the last line, or stop; **Enter** next line. The search box finds words, a
speaker or a file name; each Enter jumps to the next matching line.

## For whoever prepares a game

To start a game's transcripts from Whisper (Apple Silicon, `pip install mlx-whisper`, and ffmpeg):

```bash
python3 prepare.py GAME_DIR [--lines existing.csv] [--rename scene=conversation] [--lang he]
```

It writes `GAME_DIR/transcripts/lines.csv` with a row for every sound under `GAME_DIR`, and never
overwrites one that exists. Rows of `--lines` keep their order and text; their `file` only has to end
with the sound's path under `GAME_DIR` (a CSV of several games is told apart by the game folder's name,
as in `piposh2/SOUNDS/X.AIF`). Sounds without a row are transcribed by Whisper (`--no-whisper` leaves them
empty) and added at the end, one conversation per folder. Whisper results are cached in
`transcripts/.whisper`, so a stopped run picks up where it was. `transcripts/` gets a `.gdignore`, so Godot
doesn't import the CSV, and a `.gitignore` for the backups and the cache.

The editor plays the games' sounds as they are: Ogg files (whatever their extension), plain AIFF, WAV
and MP3. Lines find their sound ignoring case and extension, so the same `lines.csv` works in a
repository checkout and in a copy of the CD.

To send a game to someone who edits it, without the rest of the game or any setup on their side:

```bash
python3 pack.py GAME_DIR -o GAME.zip
```

The zip holds the sounds, `transcripts/lines.csv` and a `Start here.html` that opens the editor. Share it
any way that takes its size (rating is 118 MB). They unzip it, open `Start here.html` in Chrome or Edge and
choose the unzipped folder. What they send back replaces `GAME_DIR/transcripts/lines.csv`.

When several people edit, keep the `lines.csv` you sent out as the base and merge what comes back:

```bash
python3 merge.py base.csv anna.csv ben.csv -o merged.csv
```

A change one editor made is taken. Where two editors changed the same text, field or order differently,
the first file wins and the clash is printed. `python3 test_merge.py` checks the merge.

## `lines.csv`

| column | |
|---|---|
| `file` | the sound's path in the game folder; identifies the line |
| `conversation` | group name; empty means the file's folder |
| `speaker`, `text`, `note` | edited in the tool |
| `status` | `raw`, `checked`, `final`, `no_speech` |
| `alt_text` | optional; shown faded under the text with a **Use this** button (e.g. a second transcript) |

**Row order is the order**: conversations in the order they first appear, lines in row order. Any other
columns are kept as they are. The file is UTF-8 with a BOM so Excel shows Hebrew correctly.
