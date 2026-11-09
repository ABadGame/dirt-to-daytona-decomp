#!/usr/bin/env python3
"""Tag functions in the Metrowerks (SDK) blocks with evidence of which Dolphin library
they belong to:

  * hardware register blocks touched (lis rX,0xCC00 + displacement), and
  * prefixes of already-named functions they call (OS, EXI, SI, DSP, GX, ...).

Usage: sdk_libmap.py START END   (hex addresses)
"""
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HW = [(0x0000, "CP"), (0x1000, "PE"), (0x2000, "VI"), (0x3000, "PI"), (0x4000, "MI"),
      (0x5000, "DSP"), (0x6000, "DI"), (0x6400, "SI"), (0x6800, "EXI"), (0x6C00, "AI")]

d = (ROOT / "orig/GN2E70/sys/main.dol").read_bytes()
offs = struct.unpack(">7I", d[0:28]); addrs = struct.unpack(">7I", d[72:100])
base, off = addrs[1], offs[1]
w = lambda a: struct.unpack(">I", d[off + a - base: off + a - base + 4])[0]
sext = lambda x: x - 0x10000 if x & 0x8000 else x

def hw_blocks(a, size):
    hits, regs = set(), {}
    for i in range(0, size, 4):
        ins = w(a + i)
        op, rd, ra, imm = ins >> 26, (ins >> 21) & 31, (ins >> 16) & 31, ins & 0xFFFF
        if op == 15 and ra == 0 and imm == 0xCC00:          # lis rD,0xCC00
            regs[rd] = True
            continue
        if ra in regs and op in (14, 24, 32, 34, 36, 38, 40, 44, 48, 52):  # addi/ori/loads/stores
            disp = sext(imm) & 0xFFFF if op != 24 else imm
            hits.add(max(n for o, n in HW if o <= disp))
    return hits

def prefix(name):
    if name.startswith("fn_"):
        return None
    m = re.match(r"_*([A-Z]{2,4})", name)
    return m.group(1) if m else None

table = json.load(open(ROOT / "build/GN2E70/xrefs.json"))
lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
for f in sorted((f for f in table.values() if f["addr"] and lo <= f["addr"] < hi),
                key=lambda f: f["addr"]):
    hw = sorted(hw_blocks(f["addr"], f["size"]))
    calls = Counter(p for p in map(prefix, f["calls"]) if p)
    if hw or calls or not f["name"].startswith("fn_"):
        tag = " ".join(f"{k}x{v}" for k, v in calls.most_common(3))
        print(f"0x{f['addr']:08X} {f['size']:#6x} {f['name'][:28]:28s} hw={','.join(hw):10s} calls={tag}")
