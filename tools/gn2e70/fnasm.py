#!/usr/bin/env python3
"""Print the disassembly of one or more functions from dtk's split asm output.

Usage: fnasm.py NAME_OR_ADDR [...]     e.g. fnasm.py fn_8005E394 8005E3A0
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDR = re.compile(r"/\* ([0-9A-F]{8}) [0-9A-F]+  (?:[0-9A-F]{2} ){4}\*/\t")

def main():
    want = set()
    for a in sys.argv[1:]:
        a = a.upper().removeprefix("0X")
        want.add(a if not re.fullmatch(r"[0-9A-F]{8}", a) else f"FN_{a}")
    files = list((ROOT / "build/GN2E70/asm").rglob("*.s"))
    for path in files:
        cur = None
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\.fn (\S+),", line)
            if m:
                name = m.group(1)
                addr = re.search(r"\| (0x[0-9A-F]+) \|", prev) if 'prev' in dir() else None
                cur = name if name.upper() in want else None
                if cur:
                    print(f"\n{line}")
                continue
            if cur:
                if line.startswith(".endfn"):
                    print(line); cur = None
                else:
                    print(ADDR.sub(r"\1  ", line))
            prev = line

if __name__ == "__main__":
    main()
