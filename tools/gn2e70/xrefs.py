#!/usr/bin/env python3
"""Build a function cross-reference table from dtk's disassembly.

For every function in build/GN2E70/asm/*.s, record:
  * strings it references (resolved from the DOL using symbols.txt string symbols)
  * functions it calls (bl targets)

Usage:
  xrefs.py [--json out.json] [--grep REGEX]

--grep prints functions that reference a string matching REGEX.
"""
import argparse
import glob
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOL = ROOT / "orig/GN2E70/sys/main.dol"
SYMBOLS = ROOT / "config/GN2E70/symbols.txt"
ASM_GLOB = str(ROOT / "build/GN2E70/asm/*.s")

SYM_RE = re.compile(r"^(\S+) = (\.[A-Za-z0-9.]+):0x([0-9A-Fa-f]+);\s*//(.*)$")
FN_RE = re.compile(r"^\.fn (\S+),")
REF_RE = re.compile(r"\b([A-Za-z_][\w$@.]*)@(?:ha|h|l|sda21)\b")
BL_RE = re.compile(r"\tbl (\S+)$")


class Dol:
    def __init__(self, path: Path):
        self.data = path.read_bytes()
        d = self.data
        offs = struct.unpack(">18I", d[0:72])
        addrs = struct.unpack(">18I", d[72:144])
        sizes = struct.unpack(">18I", d[144:216])
        self.sections = [(addrs[i], sizes[i], offs[i]) for i in range(18) if sizes[i]]

    def read(self, addr: int, size: int) -> bytes:
        for a, s, o in self.sections:
            if a <= addr < a + s:
                return self.data[o + addr - a : o + addr - a + size]
        return b""


def load_symbols():
    syms = {}
    for line in SYMBOLS.read_text(encoding="utf-8").splitlines():
        m = SYM_RE.match(line)
        if m:
            name, sec, addr, attrs = m.groups()
            size = re.search(r"size:0x([0-9A-Fa-f]+)", attrs)
            syms[name] = {
                "addr": int(addr, 16),
                "section": sec,
                "size": int(size.group(1), 16) if size else 0,
                "string": "data:string" in attrs,
                "function": "type:function" in attrs,
            }
    return syms


def build():
    dol = Dol(DOL)
    syms = load_symbols()
    table = {}
    for path in sorted(glob.glob(ASM_GLOB)):
        cur = None
        for line in open(path, encoding="utf-8"):
            m = FN_RE.match(line)
            if m:
                cur = {"name": m.group(1), "strings": [], "calls": []}
                info = syms.get(cur["name"])
                cur["addr"] = info["addr"] if info else None
                cur["size"] = info["size"] if info else 0
                table[cur["name"]] = cur
                continue
            if line.startswith(".endfn"):
                cur = None
                continue
            if cur is None:
                continue
            m = BL_RE.search(line.rstrip("\n"))
            if m and m.group(1) not in cur["calls"]:
                cur["calls"].append(m.group(1))
            for ref in REF_RE.findall(line):
                s = syms.get(ref)
                if s and s["string"]:
                    text = dol.read(s["addr"], s["size"]).split(b"\0")[0].decode("latin-1")
                    if text not in cur["strings"]:
                        cur["strings"].append(text)
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--grep")
    args = ap.parse_args()
    table = build()
    if args.json:
        Path(args.json).write_text(json.dumps(table, indent=1), encoding="utf-8")
    if args.grep:
        rx = re.compile(args.grep)
        for fn in sorted(table.values(), key=lambda f: f["addr"] or 0):
            hits = [s for s in fn["strings"] if rx.search(s)]
            if hits:
                print(f"{fn['name']}\t{hits[:3]}")
    if not args.json and not args.grep:
        with_str = sum(1 for f in table.values() if f["strings"])
        print(f"{len(table)} functions, {with_str} reference strings")


if __name__ == "__main__":
    main()
