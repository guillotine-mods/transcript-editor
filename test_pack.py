"""python3 test_pack.py"""
import os, tempfile, zipfile
from pack import pack

with tempfile.TemporaryDirectory() as d:
    g = os.path.join(d, "game")
    os.makedirs(g + "/SOUNDS/A")
    os.makedirs(g + "/transcripts")
    for name, data in [("SOUNDS/A/x.AIF", "x"), ("SOUNDS/A/x.AIF.import", "no"), ("MOVIE.dir", "no"), ("transcripts/lines.backup-1.csv", "no")]:
        with open(os.path.join(g, name), "w") as fh:
            fh.write(data)
    with open(g + "/transcripts/lines.csv", "w", encoding="utf-8-sig", newline="") as fh:
        fh.write("file,text\r\nSOUNDS/A/x.AIF,שלום\r\nSOUNDS/A/gone.AIF,\r\n")
    out = os.path.join(d, "out.zip")
    assert pack(g, out) == 1
    names = set(zipfile.ZipFile(out).namelist())
    assert names == {"game/Start here.html", "game/transcripts/lines.csv", "game/SOUNDS/A/x.AIF"}, names
print("ok")
