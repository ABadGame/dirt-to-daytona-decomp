#!/usr/bin/env python3
"""Run SN Systems ngccc (the ProDG GameCube C/C++ compiler driver) from ninja.

ngccc needs SN_NGC_PATH pointing at its folder. It's also asked for a dependency file
(-MMD); ngccc writes it next to the output but names the target "<stem>.obj", so this
wrapper rewrites the target to the real output path for ninja.

Usage:
  ngccc.py --prodg DIR [--wrapper CMD] -o OUT.o -d OUT.d SOURCE -- [compiler flags...]
"""
import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path


def main():
    argv = sys.argv[1:]
    flags = []
    if "--" in argv:
        i = argv.index("--")
        argv, flags = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--prodg", required=True)
    ap.add_argument("--wrapper", default="")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("-d", "--depfile", required=True)
    ap.add_argument("source")
    args = ap.parse_args(argv)

    prodg = Path(args.prodg).resolve()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [*shlex.split(args.wrapper), str(prodg / "ngccc.exe"), "-c", *flags, "-MMD",
           args.source, "-o", str(out)]
    env = dict(os.environ, SN_NGC_PATH=str(prodg))
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    sys.stderr.write(result.stdout + result.stderr)
    if result.returncode != 0 or not out.exists():
        out.unlink(missing_ok=True)
        sys.exit(result.returncode or 1)

    # ngccc writes <output dir>/<stem>.d with the target named <stem>.obj.
    written = out.with_suffix(".d")
    dep = Path(args.depfile)
    if written.exists():
        text = written.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"^[^:\n]+:", f"{out.as_posix()}:", text, count=1)
        text = text.replace("\\\n", "\x00").replace("\\", "/").replace("\x00", "\\\n")
        if written != dep:
            written.unlink()
        dep.write_text(text, encoding="utf-8")
    else:
        dep.write_text(f"{out.as_posix()}: {Path(args.source).as_posix()}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
