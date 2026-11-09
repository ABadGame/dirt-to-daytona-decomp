#!/usr/bin/env python3
"""Split the game's (ProDG/GCC) .text into translation units using the constructor table.

GCC 2.95 gives every C++ file that has static initializers a `_GLOBAL_.I.<file>`
function, placed at the very end of that file's code and listed in .ctors. In this game
all 252 .ctors entries point at such a stub (a 44-byte function that calls
`__static_initialization_and_destruction_0(1, 0xFFFF)`, the function right before it),
so each entry marks where a source file ends. If a .dtors stub (`_GLOBAL_.D.<file>`)
directly follows, the file ends after that instead.

A unit runs from the previous boundary (or the start of a GCC region) to the next
boundary. Code after a region's last constructor is left to dtk's automatic units,
since nothing pins down where it ends. Files without static initializers have no stub,
so one unit can hold several real source files.

Units are named after the single `.cpp` file their own strings mention (e.g. "dash.cpp:
..." asserts); otherwise `game/tu_XXXXXXXX.cpp` after their start address.

Usage:
  game_splits.py            print the proposed units
  game_splits.py --write    also add them to splits.txt (marked comment:0, not mwcc)
"""
import argparse
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOL = ROOT / "orig/GN2E70/sys/main.dol"
SYMBOLS = ROOT / "config/GN2E70/symbols.txt"
SPLITS = ROOT / "config/GN2E70/splits.txt"
XREFS = ROOT / "build/GN2E70/xrefs.json"
CTOR_LIST, DTOR_LIST = 0x80212B40, 0x80212F40
# First function of each ProDG/GCC game region (see compiler_map.py / README code map).
GAME_REGIONS = [(0x800032C0, 0x8002FAA0), (0x80056D78, 0x801AD73C),
                (0x801CBFCC, 0x801E354C), (0x801E54E8, 0x80212AB0)]
FN_RE = re.compile(r"^(\S+) = \.text:0x([0-9A-F]+); // type:function size:0x([0-9A-F]+)")


def read_word(d, addr):
    offs = struct.unpack(">18I", d[0:72])
    addrs = struct.unpack(">18I", d[72:144])
    sizes = struct.unpack(">18I", d[144:216])
    for i in range(18):
        if sizes[i] and addrs[i] <= addr < addrs[i] + sizes[i]:
            o = offs[i] + addr - addrs[i]
            return struct.unpack(">I", d[o:o + 4])[0]
    return None


def read_list(d, head):
    out, addr = [], head + 4  # skip the -1 header
    while (w := read_word(d, addr)):
        out.append(w)
        addr += 4
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    d = DOL.read_bytes()
    ctors, dtors = read_list(d, CTOR_LIST), set(read_list(d, DTOR_LIST))
    fns = {}
    for line in SYMBOLS.read_text(encoding="utf-8").splitlines():
        m = FN_RE.match(line)
        if m:
            fns[int(m.group(2), 16)] = int(m.group(3), 16)
    order = sorted(fns)
    nxt = {a: order[i + 1] for i, a in enumerate(order[:-1])}
    xrefs = json.loads(XREFS.read_text(encoding="utf-8")) if XREFS.exists() else {}
    strings_at = {f["addr"]: f["strings"] for f in xrefs.values() if f.get("addr")}

    units = []
    for lo, hi in GAME_REGIONS:
        start = lo
        for c in (c for c in ctors if lo <= c <= hi):
            end = c + fns[c]
            if end in dtors:                      # a destructor stub right after it
                end += fns[end]
            names = Counter()
            for a in order:
                if start <= a < end:
                    for s in strings_at.get(a, []):
                        for n in re.findall(r"\b(\w+)\.cpp\b", s):
                            names[n] += 1
            units.append((start, end, names))
            start = end

    used, out = Counter(), []
    for start, end, names in units:
        name = f"game/{next(iter(names))}.cpp" if len(names) == 1 else None
        if name is None or used[name]:
            name = f"game/tu_{start:08X}.cpp"
        used[name] += 1
        out.append((name, start, end, names))

    for name, start, end, names in out:
        hint = "" if len(names) <= 1 else "  mentions " + ", ".join(names)
        print(f"{start:08X}-{end:08X}  {name}{hint}")
    named = sum(1 for n, *_ in out if not n.startswith("game/tu_"))
    print(f"{len(out)} game units ({named} named from strings), "
          f"{sum(e - s for _, s, e, _ in out):#x} bytes", file=sys.stderr)

    if args.write:
        text = SPLITS.read_text(encoding="utf-8").rstrip("\n")
        existing = set(re.findall(r"^(\S+):", text, re.M))
        blocks = [f"{name}: comment:0\n\t.text       start:0x{start:08X} end:0x{end:08X}"
                  for name, start, end, _ in out if name not in existing]
        SPLITS.write_text(text + "\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8",
                          newline="\n")
        print(f"added {len(blocks)} units to {SPLITS.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
