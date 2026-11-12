# NASCAR: Dirt to Daytona — GameCube decompilation

A work-in-progress decompilation of **NASCAR: Dirt to Daytona** (GameCube, USA, `GN2E70`),
built on [decomp-toolkit](https://github.com/encounter/decomp-toolkit) via
[dtk-template](https://github.com/encounter/dtk-template).

The goal is C/C++ source that compiles back to a byte-identical `main.dol`. A native PC
port is a later, separate step: it needs replacements for the GameCube hardware layers
(GX graphics, DSP/AX audio, PAD input, card/DVD I/O).

## Status

- `ninja` splits the DOL and relinks it with ProDG's own linker (`ngcld`) into a
  **byte-identical `main.dol`** (SHA-1 `729179d684034f46e5f4e562244ad1996e390a93`).
  No relocations are blocked, so every address reference is a real symbol reference.
- **10,614 functions** were found automatically. **888 are named**: the Dolphin SDK
  (about 75%, 62% and 86% of the bytes in its three blocks) and the ProDG/GCC runtime,
  along with ~300 SDK data objects.
- **Decompiled:** 54 of 70 functions in
  [src/game/tu_8005B908.cpp](src/game/tu_8005B908.cpp) (the AI driver's settings code) match 100% in objdiff, on every ProDG version.
- `.text` is split into **333 source files**: 81 Dolphin SDK files (`dolphin/os/OS.c`,
  `dolphin/gx/GXTexture.c`, …) and 252 game units (`game/dash.cpp`, `game/race.cpp`,
  `game/tu_XXXXXXXX.cpp`, …). Everything else, including all data sections, the ProDG
  runtime and the last game region, is still in dtk's automatic units. objdiff tracks
  progress per file.

## Code map

Prologue style splits the binary into Metrowerks-compiled and GCC-compiled regions
(`python tools/gn2e70/compiler_map.py 3`). CodeWarrior 1.x saves LR before allocating the
frame (`mflr r0; stw r0,4(r1); stwu r1,-N(r1)`); GCC allocates first
(`stwu r1,-N(r1); mflr r0`).

| Range (`.text`) | Compiler | Contents |
|---|---|---|
| `0x800032E0`–`0x8002FAA0` | GCC | Game code |
| `0x8002FD08`–`0x80030E5C` | MW | Debugger (MetroTRK) stubs: `EnableMetroTRKInterrupts`, SN file-server stubs |
| `0x80030FE0`–`0x8003C7E0` | GCC | ProDG C library (`memcpy`, `memset`, printf…), `libsn`, GCC runtime (`__builtin_new`, `__terminate`, `__sjthrow`…) |
| `0x8003C84C`–`0x80056D2C` | MW | **Dolphin SDK, part 1:** PPC arch, OS (`OSInit` @ `0x8003DA7C`, alarm, cache, context, interrupts, memory, reset, SRAM, threads, time), `__init_cpp`, DVD, EXI, DB, PAD, SI, VI |
| `0x80056D78`–`0x801AD73C` | GCC | Game code (bulk): resources, profiler, AI driver, race logic, renderer (`gx*`/`dr*`), models, textures, kernel, file, memory, input, memory-card wrapper, sound (`Spu`) |
| `0x801AD80C`–`0x801CBD90` | MW | **Dolphin SDK, part 2:** GX (`GXInit` @ `0x801AEC68` …`0x801B8xxx`), then the memory-card library (CARD, ~`0x801BFCB8`–`0x801CA000`; nearly every function calls `EXILock`/`EXISelect`/`EXIDma`) |
| `0x801CBFCC`–`0x801E354C` | GCC | Game code: memory pools, state save/load, menus, season/career |
| `0x801E3DD8`–`0x801E4FCC` | MW | **Dolphin SDK, part 3:** DSP (`__DSP_add_task` string at `0x801E5398`) |
| `0x801E54E8`–`0x80212AB0` | GCC | Game code: physics, track objects, … |

So the Nintendo SDK libraries are Metrowerks-built (like the dtk signatures) and linked
into a ProDG/GCC game. Other build stamps: the OS kernel was built **Jun 5 2002 02:09:12**
(`Dolphin OS $Revision: 54 $`). No `<< Dolphin SDK >>` version strings exist, which fits an
SDK from mid-2002 or earlier.

## Target

| | |
|---|---|
| Game ID | `GN2E70` (rev 0) |
| `main.dol` SHA-1 | `729179d684034f46e5f4e562244ad1996e390a93` |
| `.init` | `0x80003100`, size `0x1C0` (entry `__start`) |
| `.text` | `0x800032C0`, size `0x20F880` (~2.1 MB) |
| `.ctdt` | `0x80212B40`, size `0x420` (merged `.ctors` + `.dtors`, see below) |
| `.rodata` | `0x80212F60`, size `0x3BA00` |
| `.data` | `0x8024E960`, size `0x12BA0` |
| `.bss` | `0x80261500`–`0x80313FA0` |
| `.sdata` / `.sbss` | `0x80313FA0` / `0x80314720`–`0x80314C9C` |
| `.sdata2` | `0x80314CA0`, size `0x11A0` |
| `r13` (`_SDA_BASE_`) | `0x8031BFA0`; covers `.sdata`, `.sbss` **and** `.sdata2` |
| `r2` (`_SDA2_BASE_`) | `0x8032BFA0` (points at nothing; unused) |
| Symbols | None shipped (no `.map`) |
| SDK | Dolphin OS (`$Revision: 54 $`) |

Leftover source names in the binary: `dash.cpp`, `race.cpp`, `default.cpp`.

## Setup

Requirements: Python 3, [Ninja](https://ninja-build.org), Git, and
[Rust](https://rustup.rs) (to build the patched decomp-toolkit). On Windows you also need
the MSVC C++ build tools (Visual Studio).

1. Put the disc image in `orig/GN2E70/`. ISO, CISO, RVZ, GCZ and WIA all work.
   It is git-ignored, and you can delete it after the first build.
2. Configure and build:

   ```sh
   python configure.py
   ninja
   ```

   The first run builds the patched decomp-toolkit in `tools/decomp-toolkit` with Cargo.
   It also downloads objdiff, binutils and the compilers (Metrowerks *and* ProDG) into
   `build/`. It then splits the DOL, relinks it, and checks the result against
   `config/GN2E70/build.sha1`.
3. Open the project in [objdiff](https://github.com/encounter/objdiff) to compare your code
   with the original, function by function.

Disassembly is written to `build/GN2E70/asm/`.

## Compiler: SN Systems ProDG (GCC 2.95), not Metrowerks

The game code has GCC traits: GCC-order prologues (`stwu` before `mflr`) and
setjmp/longjmp ("sjlj") C++ exception handling. Functions with `try` blocks also use an
`r31` frame pointer (`mr r31,r1`) and save every non-volatile register (`mfcr`,
`stmw r14`). The memory layout is ProDG's too: `r13` covers all the small-data sections,
`.ctors`/`.dtors` are `-1`-headed GCC lists, and `libsn` runtime messages point to the
"ProDG manual". The Dolphin SDK portions are Metrowerks code (see the code map).

**Game compiler settings** (from probes, see below): `ngccc -O2 -fexceptions`
- **Optimization:** `-O2` and `-O3` match; `-O1` and `-Os` don't.
- **Exceptions:** `-fexceptions` is required, because ProDG turns exception handling off
  by default and the game uses `try`/`catch`.
- **Data placement:** the defaults match the game. Small globals go through `r13`
  (`sda21`), and float constants are loaded from `.rodata` with `lis`/`lfs`.

**Version:** not distinguishable yet. ProDG 3.5, 3.5b140, 3.7, 3.8.1 and 3.9.3 all
produce identical machine code for every probe so far: the three matched game functions
plus 16 test constructs (switch tables, loops, struct copies, constant division, 64-bit
math, virtual calls, constructors/destructors, `new`/`delete`, `try`/`catch`). The only
difference found is that 3.5–3.7 emit empty placeholder sections, which never reach the
DOL. The project tentatively uses **3.5**. Every probe runs against all five versions,
so the first game function that matches only some of them will settle it.

## Project-specific workarounds

These let the template (built around Metrowerks) handle a ProDG binary.

1. **Patched dtk.** [tools/gn2e70/dtk-prodg-eh-bctr.patch](tools/gn2e70/dtk-prodg-eh-bctr.patch)
   is already applied in `tools/decomp-toolkit` (v1.8.3). sjlj-EH functions end in a
   `bctr` after restoring `r1` with `lwz r1,12(r11)`. dtk doesn't recognize that as an
   epilogue, treats the `bctr` as a jump table and walks into the next function.
   With the patch it stops at a known function end or a known function start.
2. **Seeded function starts.** Functions that end in a `bl` to a noreturn function
   (`__throw`, `terminate`) or in that `bctr` are followed directly by the next function's
   prologue. [tools/gn2e70/find_eh_bounds.py](tools/gn2e70/find_eh_bounds.py) finds them and
   writes `symbols.txt` entries
   (`python tools/gn2e70/find_eh_bounds.py orig/GN2E70/sys/main.dol config/GN2E70/symbols.txt`).
3. **OS exception handler.** `fn_80030EF8` (size `0x18`) tail-branches into the shared
   body of `fn_80030F10` (size `0xD0`). Both are pinned in `symbols.txt`.
4. **`.ctdt` section.** ProDG linked `.ctors` (`__CTOR_LIST__`, `0x80212B40`) and `.dtors`
   (`__DTOR_LIST__`, `0x80212F40`) into one DOL section. dtk ties every `.ctors` entry to
   its function's source file. The `.dtors` entries point back to low addresses, which
   makes the link order impossible to resolve. The section is named `.ctdt` so dtk
   leaves it as one unit for now.
5. **Unique names for per-file statics.** Some SDK files each have a static with the same
   name (`ResetFunctionInfo`, `BootInfo`). With every function still in one object,
   identical local names make dtk split the data sections, which broke the link.
   They're temporarily named `ResetFunctionInfo_OSMemory`, `ResetFunctionInfo_SISteering`,
   `BootInfo_OS` and `BootInfo_DVDFs`, and can go back to the original names once the code
   is split into real files.

## Linking with ngcld

The main DOL is linked with SN Systems `ngcld` (the ProDG linker, version 1.0.10.887 in
ProDG 3.5), not Metrowerks `mwldeppc`. The Metrowerks linker reaches `.sdata2` through
`r2`, so matching with it meant blocking ~310 relocations plus the `__start` references to
`_SDA2_BASE_` and the stack and arena symbols. ngcld reaches `.sdata`, `.sbss` and
`.sdata2` through `r13` like the original, so those blocks are gone.

- [config/GN2E70/ngcld.ld](config/GN2E70/ngcld.ld): GNU `ld`-style script. Sections are
  laid out back to back from `0x80003100`, so the build still links when code changes
  size. `_SDA_BASE_` (`.sdata` + `0x8000`), `_SDA2_BASE_` (`_SDA_BASE_` + `0x10000`) and
  the stack and arena symbols (`_stack_end = 0x80315E60`, `_stack_addr = 0x80375E60`,
  `__ArenaLo = 0x80375E80`) are computed from the layout, matching the original.
- [tools/gn2e70/ngcld.py](tools/gn2e70/ngcld.py): ninja wrapper. It sets `SN_NGC_PATH`,
  and because ngcld can't read response files, it writes the object list into an
  `INPUT(...)` block at the top of a generated script. (`GROUP(...)` doesn't work here:
  ngcld treats grouped files like libraries and only pulls in referenced objects.)
- `configure.py` sets `config.prodg_linker_version = "3.5"` and `config.prodg_ldscript`.
  `tools/project.py` then links the main DOL with a `link_ngcld` rule instead of mwld.
  Metrowerks compilers are still used for any SDK objects that get compiled.
- Map files aren't produced on this path yet: `--print-map` printed nothing in testing.

## Naming tools

All of these live in `tools/gn2e70/` and run from the project root after a build.

- `sigscan.py [--apply]`: tries every decomp-toolkit SDK signature at every function
  start (dtk normally only tries them from fixed anchor points), then follows each match's
  relocations to name callees and data. Conflicting or tiny (< 6 instruction) matches are
  skipped. `--apply` only renames auto-generated `fn_`/`lbl_` symbols.
- `build_sdk.sh` + `objsigscan.py OBJ_DIR... [--apply]`: the main SDK naming pass.
  `build_sdk.sh` compiles a Dolphin SDK decompilation
  ([dolsdk2001](https://github.com/doldecomp/dolsdk2001) with CodeWarrior 1.2.5, and
  [dolsdk2004](https://github.com/doldecomp/dolsdk2004) with 1.2.5n at
  `SDK_REVISION` 0, 1 and 2) using the release flags from their Makefiles. Usage is in
  the script header. `objsigscan.py` then matches every compiled function against
  same-size game functions, with relocated fields masked out, and follows the matches'
  relocations to name callees and data. On the first run it matched 1,306 functions and
  contradicted none of the 105 names we already had. It never applies names the
  Metrowerks linker reserves (`_ctors`, `_dtors`, `__ArenaLo`…).
- `prodg_probe.py PROBE.c [--flags=-O2 ...] [--show]`: compiles a probe file with every
  ProDG version and flag set, and compares each function marked `// @target ADDRESS`
  against the game (addresses masked). `--show` prints the instruction diff.
  [probes/conv.c](tools/gn2e70/probes/conv.c) reproduces three game functions exactly
  (`0x8005BB20`, `0x800A0694`, `0x80020650`).
- `manual_names.txt` + `apply_names.py`: hand-identified names, each with its evidence.
  The file also records corrections, for example `0x800471E8` is `__fini_cpp`, which dtk's
  own signature had mislabeled as `__init_cpp`.
  Add a line and rerun the script.
- `xrefs.py [--grep REGEX]`: per-function table of referenced strings and callees
  (writes `build/GN2E70/xrefs.json` with `--json`). Useful for finding functions by
  their assert/debug messages.
- `compiler_map.py [MIN_RUN]`: prints the Metrowerks/GCC regions shown in the code map.
- `sdk_libmap.py START END`: tags functions in an address range with the hardware
  registers they touch and the named functions they call, to pin down library boundaries.

## Roadmap

1. ~~**Initial analysis:** generate symbols and splits, get a matching relink.~~ Done.
2. **Identify the SDK:** *mostly done.* 888 functions are named across OS, DVD, EXI,
   SI/PAD, DB, VI, GX, CARD, AI, AR/ARQ, AX, DTK, DSP and MTX. What's left is functions
   where this June 2002 SDK differs from both the 2001 and 2004 decomps. The largest gap
   is 30 GX functions at `0x801B75B8`–`0x801B8884`. Those need fuzzy matching or
   identification by hand.
3. **Pin down the ProDG version:** *flags found, version open.* `-O2 -fexceptions`
   reproduces game code. The five ProDG versions can't be told apart yet, so 3.5 is a
   tentative choice. Keep adding `prodg_probe.py` probes as game functions get
   decompiled. The next step that depends on this is building game code with ProDG
   inside `configure.py`.
4. ~~**ProDG link step:** switch from `mwldeppc` to `ngcld` and drop the blocked
   relocations.~~ Done. A possible follow-up is splitting `.ctdt` back into real
   `.ctors`/`.dtors`, though that's limited by how dtk assigns constructor entries to
   source files, not by the linker.
5. **Split into source files:** *`.text` done; data still to do.*
   - **SDK:** [sdk_splits.py](tools/gn2e70/sdk_splits.py) maps each named SDK
     function to the reference source file that defines it, giving 81 files. Unnamed
     functions *between* two files are left in automatic units rather than guessed.
   - **Game:** [game_splits.py](tools/gn2e70/game_splits.py) uses the constructor
     table. All 252 `.ctors` entries point at GCC 2.95's `_GLOBAL_.I.<file>` stub (a
     44-byte call to `__static_initialization_and_destruction_0(1, 0xFFFF)`), which sits
     at the end of its source file. That gives 252 units ending at exact boundaries.
     Eight are named from their own debug messages (`dash`, `race`, `pit`, `event`,
     `soundmgr`, `Skid`, `kernel`, `file`); the rest are `game/tu_<start>.cpp`.
   - **Caveats:** files without static initializers have no stub, so a unit can hold
     several real source files. The last game region (`0x801E54E8`–`0x80212AB0`) has no
     constructors and is unsplit.
   - **Next:** assign `.data`/`.rodata`/`.bss` to these units, split the units that hold
     several files, and give the units real names as classes get identified.
6. **Decompile:** *started.* Game units already compile with ProDG.
   - **Workflow:** create `src/<unit>.cpp` for a unit listed in `splits.txt` (for
     example `src/game/tu_8005B908.cpp`), run `ninja`, and compare in objdiff. Mark the
     object `Matching` in `configure.py` once the whole unit matches; until then the
     original object stays linked, so the DOL still matches.
   - **Compiling:** `GameLib` objects set `prodg_version`, so `tools/project.py`
     compiles them with a `prodg_cc` rule (`ngccc -O2 -fexceptions`) through
     [tools/gn2e70/ngccc.py](tools/gn2e70/ngccc.py). The wrapper sets `SN_NGC_PATH` and
     fixes ngccc's dependency file (it names the target `<stem>.obj`), so header changes
     trigger rebuilds.
   - **Names:** use `extern "C"` for functions that don't have real names yet, so the
     symbol matches the original's `fn_XXXXXXXX`. C++ would mangle it otherwise
     (`fn_8005BB20__Fi`).
7. **PC port (later):** build a non-matching configuration with SDK calls redirected to
   a PC backend (for example SDL with OpenGL/Vulkan).

## Docs

See `docs/` for the dtk-template guides on symbols, splits, the `.comment` section and
dependency setup.
