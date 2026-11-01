"""python3 test_merge.py"""
import csv, os, tempfile
from merge import merge

H = ["file", "conversation", "speaker", "text", "status"]


def write(d, name, rows):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(H)
        w.writerows(rows)
    return p


with tempfile.TemporaryDirectory() as d:
    base = write(d, "base.csv", [["a1", "A", "", "שלום", "raw"], ["a2", "A", "", "x", "raw"],
                                 ["b1", "B", "", "y", "raw"], ["b2", "B", "", "z", "raw"]])
    # ann fixes a1 and swaps conversations; ben fixes a2, reorders B, and also edits a1 differently
    ann = write(d, "ann.csv", [["b1", "B", "", "y", "raw"], ["b2", "B", "", "z", "raw"],
                               ["a1", "A", "", "שלום!", "checked"], ["a2", "A", "", "x", "raw"]])
    ben = write(d, "ben.csv", [["a1", "A", "", "שלום?", "raw"], ["a2", "A", "Hezi", "xx", "raw"],
                               ["b2", "B", "", "z", "raw"], ["b1", "B", "", "y", "final"]])
    header, rows, clashes = merge(base, [ann, ben])
    got = [(r["file"], r["text"], r["status"], r["speaker"]) for r in rows]
    assert got == [("b2", "z", "raw", ""), ("b1", "y", "final", ""),
                   ("a1", "שלום!", "checked", ""), ("a2", "xx", "raw", "Hezi")], got
    assert len(clashes) == 1 and "a1 text" in clashes[0], clashes
print("ok")
