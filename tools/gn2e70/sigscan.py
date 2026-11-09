#!/usr/bin/env python3
"""Scan main.dol for decomp-toolkit's SDK function signatures at *every* known function.

dtk only applies its signatures from fixed anchor points (mostly reached from a
Metrowerks-style __start), which ProDG's startup code doesn't follow. This scanner tries
each signature at every function start in symbols.txt. For each match it also follows
the signature's relocations, which names the callees (bl targets) and the data objects
the function references.

Usage:
  sigscan.py [--sigdir DIR] [--apply]

Without --apply it prints proposed names. With --apply it renames the matching
auto-generated symbols (fn_*/lbl_*) in config/GN2E70/symbols.txt, leaving
already-named symbols alone.
"""
import argparse
import base64
import glob
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DOL = ROOT / "orig/GN2E70/sys/main.dol"
SYMBOLS = ROOT / "config/GN2E70/symbols.txt"
DEFAULT_SIGDIR = ROOT / "tools/decomp-toolkit/assets/signatures"

SDA_BASE = 0x8031BFA0   # r13
SDA2_BASE = 0x8032BFA0  # r2 (unused by this game, but resolve it anyway)

SYM_RE = re.compile(r"^(\S+) = (\.[A-Za-z0-9.]+):0x([0-9A-Fa-f]+);(.*)$")
AUTO_NAME = re.compile(r"^(fn|lbl|jumptable|gap)_[0-9A-F]{8}(_\w+)?$")


def sext16(x):
    return x - 0x10000 if x & 0x8000 else x


class Dol:
    def __init__(self, path):
        self.data = path.read_bytes()
        d = self.data
        offs = struct.unpack(">18I", d[0:72])
        addrs = struct.unpack(">18I", d[72:144])
        sizes = struct.unpack(">18I", d[144:216])
        self.sections = [(addrs[i], sizes[i], offs[i]) for i in range(18) if sizes[i]]

    def read(self, addr, size):
        for a, s, o in self.sections:
            if a <= addr and addr + size <= a + s:
                return self.data[o + addr - a : o + addr - a + size]
        return None

    def word(self, addr):
        b = self.read(addr, 4)
        return struct.unpack(">I", b)[0] if b else None


def load_symbols():
    lines = SYMBOLS.read_text(encoding="utf-8").splitlines()
    by_addr = {}
    for i, line in enumerate(lines):
        m = SYM_RE.match(line)
        if m:
            name, sec, addr, attrs = m.groups()
            by_addr.setdefault(int(addr, 16), []).append((i, name, sec, attrs))
    return lines, by_addr


def load_signatures(sigdir):
    sigs = []
    for path in sorted(glob.glob(str(Path(sigdir) / "*.yml"))):
        for sig in yaml.safe_load(open(path, encoding="utf-8")) or []:
            raw = base64.b64decode(sig["signature"])
            pairs = [struct.unpack(">II", raw[i : i + 8]) for i in range(0, len(raw), 8)]
            sigs.append((Path(path).stem, sig, pairs))
    return sigs


def matches(dol, addr, pairs):
    data = dol.read(addr, len(pairs) * 4)
    if data is None:
        return False
    words = struct.unpack(f">{len(pairs)}I", data)
    return all((w & m) == (ins & m) for w, (ins, m) in zip(words, pairs))


def reloc_targets(dol, addr, sig):
    """Yield (target_addr, symbol) for each relocation in a matched signature."""
    syms = sig["symbols"]
    ha = {}
    for r in sig.get("relocations") or []:
        sym = syms[r["symbol"]]
        at = addr + r["offset"]
        ins = dol.word(at)
        kind = r["kind"]
        if kind == "PpcRel24":
            li = ins & 0x03FFFFFC
            if li & 0x02000000:
                li -= 0x04000000
            yield at + li - r["addend"], sym
        elif kind == "PpcEmbSda21":
            ra = (ins >> 16) & 0x1F
            base = {13: SDA_BASE, 2: SDA2_BASE, 0: 0}.get(ra)
            if base is not None:
                yield base + sext16(ins & 0xFFFF) - r["addend"], sym
        elif kind in ("PpcAddr16Ha", "PpcAddr16Hi"):
            ha[r["symbol"]] = (ins & 0xFFFF, kind)
        elif kind == "PpcAddr16Lo" and r["symbol"] in ha:
            hi, hk = ha[r["symbol"]]
            lo = ins & 0xFFFF
            target = (hi << 16) + (sext16(lo) if hk == "PpcAddr16Ha" else lo)
            yield (target & 0xFFFFFFFF) - r["addend"], sym


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sigdir", default=str(DEFAULT_SIGDIR))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--min-insns", type=int, default=6,
                    help="ignore signatures shorter than this (tiny stubs match everywhere)")
    args = ap.parse_args()

    dol = Dol(DOL)
    lines, by_addr = load_symbols()
    fn_starts = sorted(
        a for a, entries in by_addr.items() if any("type:function" in e[3] for e in entries)
    )
    sigs = load_signatures(args.sigdir)

    proposals = defaultdict(set)  # addr -> {(name, kind, evidence)}
    matched = []
    for stem, sig, pairs in sigs:
        if len(pairs) < args.min_insns:
            continue
        main_sym = sig["symbols"][sig["symbol"]]
        for addr in fn_starts:
            if not matches(dol, addr, pairs):
                continue
            matched.append((addr, main_sym["name"], stem))
            proposals[addr].add((main_sym["name"], "Function", f"signature {stem}"))
            for target, sym in reloc_targets(dol, addr, sig):
                if sym["name"].startswith("@") or sym["kind"] == "Unknown":
                    continue
                proposals[target].add((sym["name"], sym["kind"], f"reloc from {main_sym['name']}"))

    # Resolve. Support = number of independent pieces of evidence for (addr, name).
    support = defaultdict(int)
    for addr, cands in proposals.items():
        for name, _, _ in cands:
            support[(addr, name)] += 1

    def dominant(scores):
        """Return the key whose score is at least twice every other score, else None."""
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        if len(ranked) == 1 or ranked[0][1] >= 2 * ranked[1][1]:
            return ranked[0][0]
        return None

    accepted, conflicts = {}, {}
    for addr, cands in sorted(proposals.items()):
        best = dominant({n: support[(addr, n)] for n in {c[0] for c in cands}})
        if best is None:
            conflicts[addr] = cands
        else:
            accepted[addr] = next(c for c in cands if c[0] == best)
    # The same name proposed at several addresses: keep only a dominant address.
    name_addrs = defaultdict(list)
    for addr, (name, _, _) in accepted.items():
        name_addrs[name].append(addr)
    for name, addrs in name_addrs.items():
        if len(addrs) > 1:
            keep = dominant({a: support[(a, name)] for a in addrs})
            for a in addrs:
                if a != keep:
                    conflicts[a] = proposals[a]
                    accepted.pop(a, None)

    print(f"{len(matched)} signature matches; {len(accepted)} names; {len(conflicts)} conflicts",
          file=sys.stderr)
    for addr, (name, kind, ev) in sorted(accepted.items()):
        print(f"{addr:08X}\t{kind}\t{name}\t{ev}")
    for addr, cands in sorted(conflicts.items()):
        print(f"{addr:08X}\tCONFLICT\t{sorted(c[0] for c in cands)}", file=sys.stderr)

    if args.apply:
        renamed = 0
        reserved = re.compile(  # generated by the Metrowerks linker; redefining crashes it
            r"^(_ctors|_dtors|_rom_copy_info|_bss_init_info|_eti_init_info|_stack_addr"
            r"|_stack_end|_db_stack_addr|_db_stack_end|__ArenaLo|__ArenaHi|_SDA_BASE_"
            r"|_SDA2_BASE_|_f_\w+|_e_\w+)$")
        for addr, (name, kind, _) in accepted.items():
            if reserved.match(name):
                continue
            for i, old, sec, attrs in by_addr.get(addr, []):
                want_fn = kind == "Function"
                is_fn = "type:function" in attrs
                if AUTO_NAME.match(old) and want_fn == is_fn:
                    lines[i] = f"{name} = {sec}:0x{addr:08X};{attrs}"
                    renamed += 1
                    break
        SYMBOLS.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"renamed {renamed} symbols", file=sys.stderr)


if __name__ == "__main__":
    main()
