"""Merge the lines.csv files editors send back into one, against the copy they were all given.

usage: merge.py BASE.csv EDITED.csv [EDITED.csv ...] -o OUT.csv

Lines are matched by `file`. For every field, and for the order of conversations and of the lines in each
conversation, a change one editor made is taken. When editors made different changes to the same thing,
the first file's change is kept and the clash is listed, so you can settle it by hand.
"""
import argparse, csv, sys


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        rows = list(rd)
        return rd.fieldnames, rows


def orders(rows):
    convs = {}
    for r in rows:
        convs.setdefault(r.get("conversation", ""), []).append(r["file"])
    return list(convs), convs


def pick(what, base, edits, clashes):
    """edits: [(editor, value or None)]; the one change made, or base."""
    seen = {}
    for who, v in edits:
        if v is not None and v != base:
            seen.setdefault(_key(v), (who, v))
    if len(seen) > 1:
        clashes.append(f"{what}: different edits in {', '.join(w for w, _ in seen.values())}; kept {next(iter(seen.values()))[0]}")
    return next(iter(seen.values()))[1] if seen else base


def _key(v):
    return tuple(v) if isinstance(v, list) else v


def merge(base_path, edited_paths):
    header, base = read(base_path)
    eds = []
    for p in edited_paths:
        h, rows = read(p)
        header += [c for c in h if c not in header]
        eds.append((p, rows))
    clashes = []
    by_file = [{r["file"]: r for r in rows} for _, rows in eds]
    base_files = {r["file"] for r in base}
    for (p, rows) in eds:
        extra = {r["file"] for r in rows} - base_files
        if extra:
            clashes.append(f"{p}: {len(extra)} lines not in the base were ignored, e.g. {sorted(extra)[0]}")

    merged = {}
    for b in base:
        f, out = b["file"], {}
        for col in header:
            out[col] = pick(f"{f} {col}", b.get(col, ""), [(p, m.get(f, {}).get(col)) for (p, _), m in zip(eds, by_file)
                                                         if f in m], clashes)
        merged[f] = out

    base_convs, base_lines = orders(base)
    ed_orders = [(p, orders(rows)) for p, rows in eds]
    conv_order = pick("conversation order", base_convs, [(p, o[0]) for p, o in ed_orders], clashes)
    for c in {r["conversation"] for r in merged.values()} - set(conv_order):  # renamed or new conversation
        conv_order.append(c)

    out, placed = [], set()
    for c in conv_order:
        want = pick(f"line order of {c}", base_lines.get(c, []), [(p, o[1].get(c)) for p, o in ed_orders], clashes)
        mine = [f for f, r in merged.items() if r["conversation"] == c]
        for f in [f for f in want if f in mine] + mine:  # lines moved in from elsewhere go last
            if f not in placed and merged[f]["conversation"] == c:
                placed.add(f)
                out.append(merged[f])
    return header, out, clashes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("edited", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    header, rows, clashes = merge(a.base, a.edited)
    with open(a.out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, header)
        w.writeheader()
        w.writerows(rows)
    for c in clashes:
        print("CLASH " + c, file=sys.stderr)
    print(f"{len(rows)} lines -> {a.out}, {len(clashes)} clashes")


if __name__ == "__main__":
    main()
