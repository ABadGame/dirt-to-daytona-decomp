#!/usr/bin/env python3
"""Work out Dolphin SDK source-file boundaries in .text from the names in symbols.txt.

Every function name in the reference SDK objects (built by tools/gn2e70/build_sdk.sh)
belongs to one source file. Walking the game's functions in address order:

  * consecutive named functions from the same file form that file's span;
  * unnamed functions *between two functions of the same file* are part of it;
  * unnamed functions between two different files are left out, so dtk puts them in
    automatic gap units instead of guessing.

Names defined in several reference files (static helpers like `cb` or `Callback`) don't
decide anything on their own; they join the surrounding file when it's unambiguous.
A file that turns up in two separate places is reported and only its larger span kept.

Usage:
  sdk_splits.py OBJ_DIR [OBJ_DIR ...]          print the proposed .text splits
  sdk_splits.py OBJ_DIR ... --write            also add them to splits.txt
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from objsigscan import Elf  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SYMBOLS = ROOT / "config/GN2E70/symbols.txt"
SPLITS = ROOT / "config/GN2E70/splits.txt"
FN_RE = re.compile(r"^(\S+) = \.text:0x([0-9A-F]+); // type:function size:0x([0-9A-F]+)")
# Only the Metrowerks (SDK) blocks; see the code map in the README.
SDK_RANGES = [(0x8003C84C, 0x80056D80), (0x801AD700, 0x801CC000), (0x801E3D00, 0x801E5600)]


def load_text_functions():
    fns = []
    for line in SYMBOLS.read_text(encoding="utf-8").splitlines():
        m = FN_RE.match(line)
        if m:
            fns.append((int(m.group(2), 16), int(m.group(3), 16), m.group(1)))
    return sorted(fns)


def name_to_files(obj_dirs):
    files = defaultdict(set)
    for obj_dir in obj_dirs:
        for path in Path(obj_dir).rglob("*.o"):
            try:
                elf = Elf(path)
            except Exception:
                continue
            unit = f"dolphin/{path.parent.name}/{path.stem}.c"
            for sym in elf.symbols():
                if sym["type"] == 2 and sym["shndx"] not in (0, 0xFFF1):  # defined STT_FUNC
                    files[sym["name"]].add(unit)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obj_dirs", nargs="+")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    owners = name_to_files(args.obj_dirs)
    fns = [f for f in load_text_functions() if any(lo <= f[0] < hi for lo, hi in SDK_RANGES)]

    # Label each function with its file when the name is unique to one file.
    label = []
    for addr, size, name in fns:
        files = owners.get(name, set())
        label.append(next(iter(files)) if len(files) == 1 else None)
    # Ambiguous names (static helpers) take the file of their neighbours if those agree.
    for i, (addr, size, name) in enumerate(fns):
        if label[i] is None and len(owners.get(name, ())) > 1:
            prev = next((label[j] for j in range(i - 1, -1, -1) if label[j]), None)
            nxt = next((label[j] for j in range(i + 1, len(fns)) if label[j]), None)
            if prev and prev == nxt and prev in owners[name]:
                label[i] = prev

    # Build spans: runs of the same file, absorbing unlabeled functions that sit between
    # two functions of that file (and nothing else).
    spans = []  # [file, first_index, last_index]
    for i, lab in enumerate(label):
        if lab is None:
            continue
        if spans and spans[-1][0] == lab and all(label[j] is None for j in range(spans[-1][2] + 1, i)):
            spans[-1][2] = i
        else:
            spans.append([lab, i, i])

    by_file = defaultdict(list)
    for s in spans:
        by_file[s[0]].append(s)
    chosen = []
    for unit, ss in by_file.items():
        best = max(ss, key=lambda s: s[2] - s[1])
        if len(ss) > 1:
            where = ", ".join(f"{fns[s[1]][0]:08X}" for s in ss)
            print(f"note: {unit} appears in {len(ss)} places ({where}); keeping the largest",
                  file=sys.stderr)
        chosen.append(best)
    chosen.sort(key=lambda s: s[1])

    total = 0
    for unit, a, b in chosen:
        start, end = fns[a][0], fns[b][0] + fns[b][1]
        total += end - start
        print(f"{start:08X}-{end:08X}  {b - a + 1:3d} fns  {unit}")
    print(f"{len(chosen)} SDK files covering {total:#x} bytes", file=sys.stderr)

    if args.write:
        text = SPLITS.read_text(encoding="utf-8").rstrip("\n")
        header, _, rest = text.partition("\n\n")
        existing = set(re.findall(r"^(\S+):", rest, re.M))
        blocks = [rest] if rest.strip() else []
        for unit, a, b in chosen:
            if unit not in existing:
                start, end = fns[a][0], fns[b][0] + fns[b][1]
                blocks.append(f"{unit}:\n\t.text       start:0x{start:08X} end:0x{end:08X}")
        SPLITS.write_text(header + "\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8",
                          newline="\n")
        print(f"added {len(chosen)} units to {SPLITS.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
