#!/bin/bash
# Build release objects from a Dolphin SDK decompilation, for tools/gn2e70/objsigscan.py.
#
# usage: build_sdk.sh REPO_DIR COMPILER_DIR OUT_DIR [extra cflags...]
#
#   git clone --depth 1 https://github.com/doldecomp/dolsdk2001.git
#   git clone --depth 1 https://github.com/doldecomp/dolsdk2004.git
#   tools/gn2e70/build_sdk.sh dolsdk2001 build/compilers/GC/1.2.5  build/sdkobj/2001
#   for r in 0 1 2; do
#     tools/gn2e70/build_sdk.sh dolsdk2004 build/compilers/GC/1.2.5n build/sdkobj/2004r$r -DSDK_REVISION=$r
#   done
#   python tools/gn2e70/objsigscan.py build/sdkobj/* --apply
#
# Flags mirror the release rules in those repos' Makefiles; their build scripts are not run.
REPO=$1; CC=$(cd "$2" && pwd)/mwcceppc.exe; OUT=$(mkdir -p "$3" && cd "$3" && pwd); shift 3
LIBS="ai ar ax axfx base card db dsp dtk dvd exi gx mtx os pad si vi"
cd "$REPO" || exit 1
ok=0; fail=0
for lib in $LIBS; do
  [ -d src/$lib ] || continue
  for c in src/$lib/*.c; do
    [ -f "$c" ] || continue
    o="$OUT/$lib/$(basename "${c%.c}").o"; mkdir -p "$OUT/$lib"
    cs="-char unsigned"
    case "$c" in src/dvd/*|src/mtx/*|src/card/CARDRename.c|src/card/CARDOpen.c) cs="-char signed";; esac
    opt="-O4,p"; [ "$c" = src/exi/EXIBios.c ] && opt="-O3,p"
    if "$CC" -c $opt -inline auto -sym on $cs -nodefaults -proc gekko -fp hard -Cpp_exceptions off -enum int -warn off -requireprotos -pragma "cats off" -D__GEKKO__ "$@" -I- -Iinclude -Iinclude/libc -ir src -DRELEASE "$c" -o "$o" >"$o.log" 2>&1; then ok=$((ok+1)); rm -f "$o.log"; else fail=$((fail+1)); fi
  done
done
echo "$(basename $REPO) $*: $ok ok, $fail failed"
