# NASCAR: Dirt to Daytona — GameCube decompilation

A work-in-progress decompilation of **NASCAR: Dirt to Daytona** (GameCube, USA, `GN2E70`),
built on [decomp-toolkit](https://github.com/encounter/decomp-toolkit) via
[dtk-template](https://github.com/encounter/dtk-template).

The goal is C/C++ source that compiles back to a byte-identical `main.dol`. A native PC
port is a later, separate step: it needs replacements for the GameCube hardware layers
(GX graphics, DSP/AX audio, PAD input, card/DVD I/O).

## Status

- `ninja` splits the DOL and relinks it into a **byte-identical `main.dol`**
  (SHA-1 `729179d684034f46e5f4e562244ad1996e390a93`).
- **10,614 functions** were found automatically. **178 are named** (Dolphin SDK and the
  ProDG/GCC runtime), along with ~80 SDK data objects. None are decompiled yet.
- All code is still in one automatic unit per section (`auto_*`). Splitting into real
  source files (`dash.cpp`, `race.cpp`, …) is still to come.

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
"ProDG manual". Game code will need the ProDG compilers in `build/compilers/ProDG/`
(3.5, 3.5b140, 3.7, 3.8.1, 3.9.3) to match; the exact version is still to be found. The
Dolphin SDK portions are Metrowerks code (see the code map).

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
5. **Blocked relocations** (`block_relocations` in `config.yml`):
   - everything that targets `.sdata2`. ProDG reaches it through `r13`, but the Metrowerks
     linker would rewrite those ~310 instructions to use `r2`.
   - the `__start` loads of `_SDA2_BASE_` and of the `.sbss` end address, which the
     Metrowerks linker generates differently.

   The proper fix is to link with ProDG's `ngcld.exe` (in `build/compilers/ProDG/*`)
   instead of `mwldeppc.exe`. Then these blocks can go, and `.ctdt` can be split into
   real `.ctors`/`.dtors` input sections.
6. **Linker script template.** [config/GN2E70/ldscript.tpl](config/GN2E70/ldscript.tpl)
   reproduces ProDG's stack and arena layout (`_stack_end = 0x80315E60`,
   `_stack_addr = 0x80375E60`, `__ArenaLo = 0x80375E80`, no debugger stack). Once
   `OSInit` was named, dtk started emitting relocations to these symbols, and the
   Metrowerks default layout put them in different places.

## Naming tools

All of these live in `tools/gn2e70/` and run from the project root after a build.

- `sigscan.py [--apply]`: tries every decomp-toolkit SDK signature at every function
  start (dtk normally only tries them from fixed anchor points), then follows each match's
  relocations to name callees and data. Conflicting or tiny (< 6 instruction) matches are
  skipped. `--apply` only renames auto-generated `fn_`/`lbl_` symbols.
- `manual_names.txt` + `apply_names.py`: hand-identified names, each with its evidence.
  Add a line and rerun the script.
- `xrefs.py [--grep REGEX]`: per-function table of referenced strings and callees
  (writes `build/GN2E70/xrefs.json` with `--json`). Useful for finding functions by
  their assert/debug messages.
- `compiler_map.py [MIN_RUN]`: prints the Metrowerks/GCC regions shown in the code map.
- `sdk_libmap.py START END`: tags functions in an address range with the hardware
  registers they touch and the named functions they call, to pin down library boundaries.

## Roadmap

1. ~~**Initial analysis:** generate symbols and splits, get a matching relink.~~ Done.
2. **Identify the SDK:** *in progress.* Library regions are mapped, and the core OS, DVD,
   EXI, SI, DB, GX-init and GCC-runtime functions are named. Still to do: the rest of
   GX, CARD, PAD, AI/AR/ARQ/AX/DSP and MTX. The likely approach is building matching
   signatures from a 2002-era Dolphin SDK decompilation with the Metrowerks compilers
   already in `build/compilers/GC`.
3. **Pin down the ProDG version:** compile small test functions with each ProDG version
   and compare them with the original.
4. **ProDG link step:** switch from `mwldeppc` to `ngcld` and remove workaround 5.
5. **Split the game code:** use the leftover assert/debug strings (`dash.cpp`, `race.cpp`…)
   and the `.ctors` entries (one per C++ file with static initializers) to find source-file
   boundaries and name classes (`RaceSummaryOverlay`, …).
6. **Decompile:** add source to `src/` and register each object in `configure.py`,
   starting as `NonMatching` and switching to `Matching` once it matches.
7. **PC port (later):** build a non-matching configuration with SDK calls redirected to
   a PC backend (for example SDL with OpenGL/Vulkan).

## Docs

See `docs/` for the dtk-template guides on symbols, splits, the `.comment` section and
dependency setup.
