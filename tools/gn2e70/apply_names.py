#!/usr/bin/env python3
"""Apply tools/gn2e70/manual_names.txt to config/GN2E70/symbols.txt.

Only auto-generated names (fn_XXXXXXXX, lbl_XXXXXXXX) are replaced, so running this
again never overwrites a name someone chose by hand.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYMBOLS = ROOT / "config/GN2E70/symbols.txt"
NAMES = ROOT / "tools/gn2e70/manual_names.txt"

wanted = {}
for line in NAMES.read_text(encoding="utf-8").splitlines():
    line = line.split("#", 1)[0].strip()
    if line:
        addr, name = line.split()[:2]
        wanted[int(addr, 16)] = name

lines = SYMBOLS.read_text(encoding="utf-8").splitlines()
done = set()
for i, line in enumerate(lines):
    m = re.match(r"^((?:fn|lbl)_([0-9A-F]{8})) = (.*)$", line)
    if m and int(m.group(2), 16) in wanted and int(m.group(2), 16) not in done:
        addr = int(m.group(2), 16)
        lines[i] = f"{wanted[addr]} = {m.group(3)}"
        done.add(addr)
SYMBOLS.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
missing = sorted(set(wanted) - done)
print(f"renamed {len(done)}; not applied (already named or missing): "
      + ", ".join(f"{a:08X}" for a in missing))
