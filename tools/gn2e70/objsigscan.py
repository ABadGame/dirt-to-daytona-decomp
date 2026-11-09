#!/usr/bin/env python3
"""Name functions in main.dol by matching them against compiled reference objects.

Point this at a folder of PowerPC ELF .o files (for example, a Dolphin SDK
decompilation built with the same Metrowerks compiler). For every function in those
objects it builds a signature: the instruction bytes, with relocated fields masked out.
It then looks for game functions of the same size whose bytes match. For each match,
the object's relocations also name the callees (bl targets) and referenced data.

Usage:
  objsigscan.py OBJ_DIR [OBJ_DIR ...] [--apply] [--min-insns N]

--apply renames only auto-generated fn_/lbl_ symbols in config/GN2E70/symbols.txt.
"""
import argparse
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOL = ROOT / "orig/GN2E70/sys/main.dol"
SYMBOLS = ROOT / "config/GN2E70/symbols.txt"
SDA_BASE = 0x8031BFA0  # r13; ProDG reaches every small-data section through it
AUTO_NAME = re.compile(r"^(fn|lbl)_[0-9A-F]{8}$")
# Names the Metrowerks linker generates itself; defining them again crashes mwldeppc.
LINKER_RESERVED = re.compile(
    r"^(_ctors|_dtors|_rom_copy_info|_bss_init_info|_eti_init_info|_stack_addr|_stack_end"
    r"|_db_stack_addr|_db_stack_end|__ArenaLo|__ArenaHi|_SDA_BASE_|_SDA2_BASE_|_f_\w+|_e_\w+)$")
SYM_RE = re.compile(r"^(\S+) = (\.[A-Za-z0-9.]+):0x([0-9A-Fa-f]+);(.*)$")

# PowerPC ELF relocation types -> mask of the instruction bits they patch
R_PPC_ADDR16_LO, R_PPC_ADDR16_HI, R_PPC_ADDR16_HA = 4, 5, 6
R_PPC_REL24, R_PPC_REL14 = 10, 11
R_PPC_EMB_SDA21 = 109
RELOC_MASK = {
    1: 0xFFFFFFFF,       # ADDR32 (data in code)
    R_PPC_ADDR16_LO: 0x0000FFFF,
    R_PPC_ADDR16_HI: 0x0000FFFF,
    R_PPC_ADDR16_HA: 0x0000FFFF,
    R_PPC_REL24: 0x03FFFFFC,
    R_PPC_REL14: 0x0000FFFC,
    R_PPC_EMB_SDA21: 0x001FFFFF,  # base register (rA) + 16-bit offset
}


def sext16(x):
    return x - 0x10000 if x & 0x8000 else x


# --- minimal big-endian ELF32 reader -----------------------------------------------
class Elf:
    def __init__(self, path):
        self.path = path
        d = self.data = Path(path).read_bytes()
        if d[:4] != b"\x7fELF" or d[4] != 1 or d[5] != 2:
            raise ValueError("not a big-endian ELF32 file")
        (self.shoff,) = struct.unpack(">I", d[0x20:0x24])
        self.shentsize, self.shnum, self.shstrndx = struct.unpack(">HHH", d[0x2E:0x34])
        self.sections = []
        for i in range(self.shnum):
            o = self.shoff + i * self.shentsize
            name, typ, flags, addr, off, size, link, info, align, entsize = struct.unpack(
                ">10I", d[o : o + 40])
            self.sections.append(dict(name=name, type=typ, off=off, size=size, link=link,
                                      info=info, entsize=entsize))
        strtab = self.sections[self.shstrndx]
        for s in self.sections:
            s["name"] = self._str(strtab, s["name"])

    def _str(self, sec, off):
        start = sec["off"] + off
        return self.data[start : self.data.index(b"\0", start)].decode("latin-1")

    def section_data(self, idx):
        s = self.sections[idx]
        return self.data[s["off"] : s["off"] + s["size"]]

    def symbols(self):
        for s in self.sections:
            if s["type"] == 2:  # SHT_SYMTAB
                strtab = self.sections[s["link"]]
                for i in range(s["size"] // 16):
                    o = s["off"] + i * 16
                    name, value, size, info, other, shndx = struct.unpack(
                        ">IIIBBH", self.data[o : o + 16])
                    yield dict(index=i, name=self._str(strtab, name), value=value, size=size,
                               type=info & 0xF, bind=info >> 4, shndx=shndx)

    def relocs_for(self, target_idx):
        for s in self.sections:
            if s["type"] == 4 and s["info"] == target_idx:  # SHT_RELA
                for i in range(s["size"] // 12):
                    o = s["off"] + i * 12
                    off, info, addend = struct.unpack(">IIi", self.data[o : o + 12])
                    yield off, info >> 8, info & 0xFF, addend


def object_signatures(path):
    """Yield (name, words, masks, relocs) for each function in an object file."""
    try:
        elf = Elf(path)
    except (ValueError, struct.error):
        return
    syms = list(elf.symbols())
    by_index = {s["index"]: s for s in syms}
    for sec_idx, sec in enumerate(elf.sections):
        if not sec["name"].startswith(".text") or sec["type"] != 1:
            continue
        data = elf.section_data(sec_idx)
        relocs = sorted(elf.relocs_for(sec_idx))
        for fn in syms:
            if fn["type"] != 2 or fn["shndx"] != sec_idx or fn["size"] < 4:  # STT_FUNC
                continue
            start, end = fn["value"], fn["value"] + fn["size"]
            words = list(struct.unpack(f">{fn['size'] // 4}I", data[start:end]))
            masks = [0xFFFFFFFF] * len(words)
            fn_relocs = []
            for off, sym_idx, rtype, addend in relocs:
                if start <= off < end:
                    k = (off - start) // 4
                    masks[k] &= ~RELOC_MASK.get(rtype, 0xFFFFFFFF) & 0xFFFFFFFF
                    tgt = by_index.get(sym_idx, {})
                    fn_relocs.append((off - start, rtype, tgt.get("name", ""),
                                      tgt.get("type", 0), addend))
            yield fn["name"], words, masks, fn_relocs


# --- game side ----------------------------------------------------------------------
class Dol:
    def __init__(self, path):
        d = self.data = path.read_bytes()
        offs = struct.unpack(">18I", d[0:72])
        addrs = struct.unpack(">18I", d[72:144])
        sizes = struct.unpack(">18I", d[144:216])
        self.sections = [(addrs[i], sizes[i], offs[i]) for i in range(18) if sizes[i]]

    def words(self, addr, n):
        for a, s, o in self.sections:
            if a <= addr and addr + 4 * n <= a + s:
                return struct.unpack(f">{n}I", self.data[o + addr - a : o + addr - a + 4 * n])
        return None


def load_game_functions():
    lines = SYMBOLS.read_text(encoding="utf-8").splitlines()
    fns, by_addr = defaultdict(list), defaultdict(list)
    for i, line in enumerate(lines):
        m = SYM_RE.match(line)
        if not m:
            continue
        name, sec, addr, attrs = m.groups()
        addr = int(addr, 16)
        by_addr[addr].append((i, name, sec, attrs))
        size = re.search(r"size:0x([0-9A-Fa-f]+)", attrs)
        if "type:function" in attrs and size:
            fns[int(size.group(1), 16)].append(addr)
    return lines, by_addr, fns


def reloc_target(addr, word, rtype, ha_cache, sym):
    if rtype == R_PPC_REL24:
        li = word & 0x03FFFFFC
        if li & 0x02000000:
            li -= 0x04000000
        return addr + li
    if rtype == R_PPC_EMB_SDA21 and (word >> 16) & 0x1F == 13:
        return SDA_BASE + sext16(word & 0xFFFF)
    if rtype == R_PPC_ADDR16_HA:
        ha_cache[sym] = word & 0xFFFF
        return None
    if rtype == R_PPC_ADDR16_LO and sym in ha_cache:
        return ((ha_cache[sym] << 16) + sext16(word & 0xFFFF)) & 0xFFFFFFFF
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obj_dirs", nargs="+")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--min-insns", type=int, default=6)
    args = ap.parse_args()

    dol = Dol(DOL)
    lines, by_addr, game_fns = load_game_functions()

    support = defaultdict(lambda: defaultdict(set))  # addr -> name -> {evidence}
    kinds = {}
    seen_sigs, n_sigs, n_matches = set(), 0, 0
    for obj_dir in args.obj_dirs:
        for path in sorted(Path(obj_dir).rglob("*.o")):
            for name, words, masks, relocs in object_signatures(path):
                if len(words) < args.min_insns or name.startswith("@"):
                    continue
                key = (name, tuple(w & m for w, m in zip(words, masks)), tuple(masks))
                if key in seen_sigs:
                    continue
                seen_sigs.add(key)
                n_sigs += 1
                for addr in game_fns.get(len(words) * 4, []):
                    game = dol.words(addr, len(words))
                    if not game or any((g ^ w) & m for g, w, m in zip(game, words, masks)):
                        continue
                    n_matches += 1
                    ev = f"{Path(obj_dir).name}/{path.name}"
                    support[addr][name].add("match " + ev)
                    kinds[(addr, name)] = "Function"
                    ha = {}
                    for off, rtype, tname, ttype, addend in relocs:
                        if not tname or tname.startswith("@") or tname.startswith("."):
                            continue
                        tgt = reloc_target(addr + off, game[off // 4], rtype, ha, tname)
                        if tgt is not None:
                            tgt = (tgt - addend) & 0xFFFFFFFF
                            support[tgt][tname].add(f"reloc from {name}")
                            kinds[(tgt, tname)] = "Function" if ttype == 2 else (
                                "Object" if ttype == 1 else kinds.get((tgt, tname), "Unknown"))

    def dominant(scores):
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        if len(ranked) == 1 or ranked[0][1] >= 2 * ranked[1][1]:
            return ranked[0][0]
        return None

    accepted, conflicts = {}, {}
    for addr, names in support.items():
        best = dominant({n: len(e) for n, e in names.items()})
        (accepted if best else conflicts)[addr] = best or sorted(names)
    name_addrs = defaultdict(list)
    for addr, name in accepted.items():
        name_addrs[name].append(addr)
    for name, addrs in name_addrs.items():
        if len(addrs) > 1:
            keep = dominant({a: len(support[a][name]) for a in addrs})
            for a in addrs:
                if a != keep:
                    conflicts[a] = [name]
                    accepted.pop(a)

    print(f"{n_sigs} signatures, {n_matches} matches, {len(accepted)} names, "
          f"{len(conflicts)} conflicts", file=sys.stderr)
    for addr in sorted(accepted):
        name = accepted[addr]
        print(f"{addr:08X}\t{kinds.get((addr, name), '?')}\t{name}\t"
              f"{sorted(support[addr][name])[0]}")
    for addr in sorted(conflicts):
        print(f"{addr:08X}\tCONFLICT\t{conflicts[addr]}", file=sys.stderr)

    if args.apply:
        renamed = 0
        for addr, name in accepted.items():
            kind = kinds.get((addr, name))
            if LINKER_RESERVED.match(name):
                continue
            for i, old, sec, attrs in by_addr.get(addr, []):
                is_fn = "type:function" in attrs
                if AUTO_NAME.match(old) and (kind == "Function") == is_fn:
                    lines[i] = f"{name} = {sec}:0x{addr:08X};{attrs}"
                    renamed += 1
                    break
        SYMBOLS.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"renamed {renamed} symbols", file=sys.stderr)


if __name__ == "__main__":
    main()
