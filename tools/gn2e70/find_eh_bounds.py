#!/usr/bin/env python3
"""Seed symbols.txt with function starts that decomp-toolkit's analyzer misses.

The game was built with GCC (SN Systems ProDG) using setjmp/longjmp exception handling.
Two patterns make dtk's analyzer run past the end of one function into the next:

  * a function that ends with an indirect `bctr` (the sjlj-EH unwind/return), and
  * a function that ends with a `bl` to a noreturn function (`__throw`, `terminate`...).

In both cases the next instruction is a new function's prologue (`stwu r1,-X(r1)`).
Marking that address as a known function makes dtk stop there. (The `bctr` case also
needs tools/gn2e70/dtk-prodg-eh-bctr.patch.)

Usage: find_eh_bounds.py <main.dol> [existing symbols.txt]
Prints symbols.txt lines for any function starts not already listed.
"""
import re
import struct
import sys

BCTR = 0x4E800420


def is_stwu_r1(x: int) -> bool:
    # stwu r1, -d(r1)
    return (x & 0xFFFF0000) == 0x94210000 and bool(x & 0x8000)


def is_bl(x: int) -> bool:
    # b with LK=1, AA=0
    return (x >> 26) == 18 and (x & 3) == 1


def main() -> None:
    d = open(sys.argv[1], "rb").read()
    offs = struct.unpack(">7I", d[0:28])
    addrs = struct.unpack(">7I", d[72:100])
    sizes = struct.unpack(">7I", d[144:172])

    known = set()
    if len(sys.argv) > 2:
        for line in open(sys.argv[2], encoding="utf-8"):
            m = re.search(r"=\s*\.text:(0x[0-9A-Fa-f]+);", line)
            if m:
                known.add(int(m.group(1), 16))

    starts = set()
    for i in range(7):
        if not sizes[i]:
            continue
        base, text = addrs[i], d[offs[i] : offs[i] + sizes[i]]
        words = struct.unpack(f">{len(text) // 4}I", text)
        for n in range(len(words) - 1):
            if (words[n] == BCTR or is_bl(words[n])) and is_stwu_r1(words[n + 1]):
                starts.add(base + (n + 1) * 4)

    for s in sorted(starts - known):
        print(f"fn_{s:08X} = .text:0x{s:08X}; // type:function")


if __name__ == "__main__":
    main()
