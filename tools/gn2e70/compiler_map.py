#!/usr/bin/env python3
"""Classify functions by prologue style to tell Metrowerks code from ProDG/GCC code.

  Metrowerks (CodeWarrior 1.x):  mflr r0 ; stw r0,4(r1) ; stwu r1,-N(r1)
  GCC (ProDG):                   stwu r1,-N(r1) ; mflr r0 ; ... stw r0,N+4(r1)

Leaf functions (no stack frame) don't count. Prints runs of consecutive functions with
the same style (ignoring leaves), which roughly follow library/object boundaries.
"""
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
d = (ROOT / "orig/GN2E70/sys/main.dol").read_bytes()
offs = struct.unpack(">7I", d[0:28]); addrs = struct.unpack(">7I", d[72:100])
base, off = addrs[1], offs[1]
w = lambda a: struct.unpack(">I", d[off + a - base: off + a - base + 4])[0]

fns = []
for line in (ROOT / "config/GN2E70/symbols.txt").read_text().splitlines():
    m = re.match(r"(\S+) = \.text:0x([0-9A-F]+); // type:function size:0x([0-9A-F]+)", line)
    if m:
        fns.append((int(m.group(2), 16), int(m.group(3), 16), m.group(1)))
fns.sort()

def style(a, size):
    if size < 12:
        return None
    i0, i1, i2 = w(a), w(a + 4), w(a + 8)
    if i0 == 0x7C0802A6 and i1 == 0x90010004 and (i2 >> 16) == 0x9421:
        return "MW"
    if (i0 >> 16) == 0x9421 and i1 == 0x7C0802A6:
        return "GCC"
    return None

runs = []
for a, size, name in fns:
    s = style(a, size)
    if s is None:
        continue
    if runs and runs[-1][0] == s:
        runs[-1][2] = a; runs[-1][3] += 1
    else:
        runs.append([s, a, a, 1])
min_run = int(sys.argv[1]) if len(sys.argv) > 1 else 1
for s, start, end, n in runs:
    if n >= min_run:
        print(f"{s:4s} 0x{start:08X}-0x{end:08X}  {n:5d} fns")
tot = {k: sum(r[3] for r in runs if r[0] == k) for k in ("MW", "GCC")}
print(tot, file=sys.stderr)
