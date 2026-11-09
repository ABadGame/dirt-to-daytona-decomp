#!/usr/bin/env python3
"""Find which ProDG compiler version and flags reproduce the game's code.

Compiles a probe source file (C or C++) with every ProDG version in
build/compilers/ProDG and each set of flags, then compares each compiled function
with the game function it's meant to reproduce. Relocated fields (addresses) are
masked out of the comparison.

Each probe function names its target with a marker comment on the line before it:

    // @target 8005BB20
    float probe_8005BB20(int x) { return (float)(x - 0x55) * K; }

Usage:
  prodg_probe.py PROBE.c [--flags "-O2" --flags "-O3" ...] [--versions 3.5,3.7] [--show]

--show prints a side-by-side diff for each non-matching function (first flags set).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from objsigscan import Dol, object_signatures, DOL, load_game_functions  # noqa: E402

# Game function sizes from symbols.txt, so a shorter compiled function can't "match".
GAME_SIZES = {a: size for size, addrs in load_game_functions()[2].items() for a in addrs}

ROOT = Path(__file__).resolve().parents[2]
PRODG = ROOT / "build/compilers/ProDG"
OBJDUMP = ROOT / "build/binutils/powerpc-eabi-objdump.exe"


def targets(src):
    out, pending = {}, None
    for line in Path(src).read_text(encoding="utf-8").splitlines():
        m = re.search(r"@target\s+([0-9A-Fa-f]{8})", line)
        if m:
            pending = int(m.group(1), 16)
            continue
        m = re.match(r"^[^/#]*?\b(\w+)\s*\(", line)
        if pending is not None and m:
            out[m.group(1)] = pending
            pending = None
    return out


def compile_probe(version, src, flags, out):
    cc = PRODG / version
    env = dict(os.environ, SN_NGC_PATH=str(cc))
    cmd = [str(cc / "ngccc.exe"), "-c", *flags.split(), str(src), "-o", str(out)]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    return r.returncode == 0 and out.exists(), (r.stdout + r.stderr).strip()


def disasm(words, base):
    return [f"{base + 4 * i:08X}  {w:08X}" for i, w in enumerate(words)]


def compare(dol, obj, want):
    """Return {func: (status, detail)} for every probe function in the object."""
    results = {}
    for name, words, masks, _ in object_signatures(obj):
        if name not in want:
            continue
        addr = want[name]
        game = dol.words(addr, len(words))
        # Game function size: compare only as many words as the compiled one.
        if game is None:
            results[name] = ("no-target", "")
            continue
        diffs = [i for i, (g, w, m) in enumerate(zip(game, words, masks)) if (g ^ w) & m]
        game_size = GAME_SIZES.get(addr)
        if game_size is not None and game_size != 4 * len(words):
            status = f"size {4 * len(words):#x}!={game_size:#x}"
        else:
            status = "MATCH" if not diffs else f"{len(diffs)} diff"
        results[name] = (status, (game, words, masks, diffs))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("probe")
    ap.add_argument("--flags", action="append")
    ap.add_argument("--versions")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    flag_sets = args.flags or ["-O2"]
    versions = args.versions.split(",") if args.versions else sorted(
        p.name for p in PRODG.iterdir() if (p / "ngccc.exe").exists())
    want = targets(args.probe)
    if not want:
        sys.exit("no '// @target ADDRESS' markers found in probe")
    dol = Dol(DOL)

    with tempfile.TemporaryDirectory() as tmp:
        for flags in flag_sets:
            print(f"== flags: {flags}")
            header = f"{'function':28s}" + "".join(f"{v:>10s}" for v in versions)
            print(header)
            table, details = {}, {}
            for v in versions:
                obj = Path(tmp) / f"probe_{v}_{abs(hash(flags))}.o"
                ok, log = compile_probe(v, Path(args.probe).resolve(), flags, obj)
                if not ok:
                    print(f"  {v}: compile failed: {log[:300]}")
                    continue
                for name, (status, det) in compare(dol, obj, want).items():
                    table.setdefault(name, {})[v] = status
                    details[(name, v)] = det
            for name in want:
                row = table.get(name, {})
                print(f"{name:28s}" + "".join(f"{row.get(v, '-'):>10s}" for v in versions))
            if args.show:
                for name in want:
                    for v in versions:
                        det = details.get((name, v))
                        if det and det[3]:
                            game, words, masks, diffs = det
                            print(f"-- {name} [{v}] game vs compiled (masked words marked *)")
                            for i, (g, w, m) in enumerate(zip(game, words, masks)):
                                mark = "!!" if i in diffs else ("* " if m != 0xFFFFFFFF else "  ")
                                print(f"   {mark} {want[name] + 4 * i:08X}  {g:08X}  {w:08X}")
                            break


if __name__ == "__main__":
    main()
