#!/usr/bin/env python3

###
# Generates build files for the project.
# This file also includes the project configuration,
# such as compiler flags and the object matching status.
#
# Usage:
#   python3 configure.py
#   ninja
#
# Append --help to see available options.
###

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

from tools.project import (
    Object,
    ProgressCategory,
    ProjectConfig,
    calculate_progress,
    generate_build,
    is_windows,
)

# Game versions
DEFAULT_VERSION = 0
VERSIONS = [
    "GN2E70",  # 0
]

parser = argparse.ArgumentParser()
parser.add_argument(
    "mode",
    choices=["configure", "progress"],
    default="configure",
    help="script mode (default: configure)",
    nargs="?",
)
parser.add_argument(
    "-v",
    "--version",
    choices=VERSIONS,
    type=str.upper,
    default=VERSIONS[DEFAULT_VERSION],
    help="version to build",
)
parser.add_argument(
    "--build-dir",
    metavar="DIR",
    type=Path,
    default=Path("build"),
    help="base build directory (default: build)",
)
parser.add_argument(
    "--binutils",
    metavar="BINARY",
    type=Path,
    help="path to binutils (optional)",
)
parser.add_argument(
    "--compilers",
    metavar="DIR",
    type=Path,
    help="path to compilers (optional)",
)
parser.add_argument(
    "--map",
    action="store_true",
    help="generate map file(s)",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="build with debug info (non-matching)",
)
if not is_windows():
    parser.add_argument(
        "--wrapper",
        metavar="BINARY",
        type=Path,
        help="path to wibo or wine (optional)",
    )
parser.add_argument(
    "--dtk",
    metavar="BINARY | DIR",
    type=Path,
    # GN2E70 needs a patched dtk (tools/gn2e70/dtk-prodg-eh-bctr.patch); build it from source.
    default=Path("tools/decomp-toolkit"),
    help="path to decomp-toolkit binary or source (default: tools/decomp-toolkit)",
)
parser.add_argument(
    "--objdiff",
    metavar="BINARY | DIR",
    type=Path,
    help="path to objdiff-cli binary or source (optional)",
)
parser.add_argument(
    "--sjiswrap",
    metavar="EXE",
    type=Path,
    help="path to sjiswrap.exe (optional)",
)
parser.add_argument(
    "--ninja",
    metavar="BINARY",
    type=Path,
    help="path to ninja binary (optional)",
)
parser.add_argument(
    "--verbose",
    action="store_true",
    help="print verbose output",
)
parser.add_argument(
    "--non-matching",
    dest="non_matching",
    action="store_true",
    help="builds equivalent (but non-matching) or modded objects",
)
parser.add_argument(
    "--warn",
    dest="warn",
    type=str,
    choices=["all", "off", "error"],
    help="how to handle warnings",
)
parser.add_argument(
    "--no-progress",
    dest="progress",
    action="store_false",
    help="disable progress calculation",
)
args = parser.parse_args()

config = ProjectConfig()
config.version = str(args.version)
version_num = VERSIONS.index(config.version)

# Apply arguments
config.build_dir = args.build_dir
config.dtk_path = args.dtk
config.objdiff_path = args.objdiff
config.binutils_path = args.binutils
config.compilers_path = args.compilers
config.generate_map = args.map
config.non_matching = args.non_matching
config.sjiswrap_path = args.sjiswrap
config.ninja_path = args.ninja
config.progress = args.progress
if not is_windows():
    config.wrapper = args.wrapper
# Don't build asm unless we're --non-matching
if not config.non_matching:
    config.asm_dir = None

# Tool versions
config.binutils_tag = "2.42-2"
config.compilers_tag = "20251118"
config.dtk_tag = "v1.8.3"
config.objdiff_tag = "v3.6.1"
config.sjiswrap_tag = "v1.2.2"
config.wibo_tag = "1.0.3"

# Project
config.config_path = Path("config") / config.version / "config.yml"
config.check_sha_path = Path("config") / config.version / "build.sha1"
config.asflags = [
    "-mgekko",
    "--strip-local-absolute",
    "-I include",
    f"-I build/{config.version}/include",
    f"--defsym BUILD_VERSION={version_num}",
]
config.ldflags = [
    "-fp hardware",
    "-nodefaults",
]
if args.debug:
    config.ldflags.append("-g")  # Or -gdwarf-2 for Wii linkers
if args.map:
    config.ldflags.append("-mapunused")
    # config.ldflags.append("-listclosure") # For Wii linkers

# Use for any additional files that should cause a re-configure when modified
config.reconfig_deps = []

# Optional numeric ID for decomp.me preset
# Can be overridden in libraries or objects
config.scratch_preset_id = None

# Base flags, common to most GC/Wii games.
# Generally leave untouched, with overrides added below.
cflags_base = [
    "-nodefaults",
    "-proc gekko",
    "-align powerpc",
    "-enum int",
    "-fp hardware",
    "-Cpp_exceptions off",
    "-O4,p",
    "-inline auto",
    '-pragma "cats off"',
    '-pragma "warn_notinlined off"',
    "-maxerrors 1",
    "-nosyspath",
    "-RTTI off",
    "-fp_contract on",
    "-str reuse",
    "-multibyte",  # For Wii compilers, replace with `-enc SJIS`
    "-i include",
    f"-i build/{config.version}/include",
    f"-DBUILD_VERSION={version_num}",
    f"-DVERSION_{config.version}",
]

# Debug flags
if args.debug:
    # Or -sym dwarf-2 for Wii compilers
    cflags_base.extend(["-sym on", "-DDEBUG=1"])
else:
    cflags_base.append("-DNDEBUG=1")

# Warning flags
if args.warn == "all":
    cflags_base.append("-W all")
elif args.warn == "off":
    cflags_base.append("-W off")
elif args.warn == "error":
    cflags_base.append("-W error")

# Metrowerks library flags
cflags_runtime = [
    *cflags_base,
    "-use_lmw_stmw on",
    "-str reuse,pool,readonly",
    "-gccinc",
    "-common off",
    "-inline auto",
]

# REL flags
cflags_rel = [
    *cflags_base,
    "-sdata 0",
    "-sdata2 0",
]

config.linker_version = "GC/1.3.2"  # still used to compile Metrowerks (SDK) objects

# GN2E70 was linked with SN Systems ProDG. ngcld resolves every small-data reference
# through r13 like the original, so no relocations need blocking. See README.
config.prodg_linker_version = "3.5"
config.prodg_ldscript = Path("config") / config.version / "ngcld.ld"


# Helper function for Dolphin libraries
# GN2E70: the SDK is Metrowerks-built (see README). Flags follow the release rules of the
# doldecomp/dolsdk2001 and dolsdk2004 decompilations; the exact compiler is not confirmed.
cflags_dolphin = [
    *cflags_base,  # already has -O4,p -inline auto -enum int
    "-char unsigned",
    "-requireprotos",
]


def DolphinLib(lib_name: str, objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": "GC/1.2.5n",
        "cflags": cflags_dolphin,
        "progress_category": "sdk",
        "objects": objects,
    }


# GN2E70 game code: SN Systems ProDG (GCC 2.95), built with `ngccc -O2 -fexceptions`.
# project.py only compiles with Metrowerks so far, so these stay NonMatching until a
# ProDG compile rule exists (see README roadmap). mw_version/cflags are placeholders.
def GameLib(lib_name: str, objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": config.linker_version,
        "cflags": cflags_base,
        "progress_category": "game",
        "objects": objects,
    }


# Helper function for REL script objects
def Rel(lib_name: str, objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": "GC/1.3.2",
        "cflags": cflags_rel,
        "progress_category": "game",
        "objects": objects,
    }


Matching = True                   # Object matches and should be linked
NonMatching = False               # Object does not match and should not be linked
Equivalent = config.non_matching  # Object should be linked when configured with --non-matching


# Object is only matching for specific versions
def MatchingFor(*versions):
    return config.version in versions


config.warn_missing_config = True
config.warn_missing_source = False
config.libs = [
    DolphinLib(
        "base",
        [
            Object(NonMatching, "dolphin/base/PPCArch.c"),
        ],
    ),
    DolphinLib(
        "os",
        [
            Object(NonMatching, "dolphin/os/OS.c"),
            Object(NonMatching, "dolphin/os/OSAlarm.c"),
            Object(NonMatching, "dolphin/os/OSAlloc.c"),
            Object(NonMatching, "dolphin/os/OSArena.c"),
            Object(NonMatching, "dolphin/os/OSAudioSystem.c"),
            Object(NonMatching, "dolphin/os/OSCache.c"),
            Object(NonMatching, "dolphin/os/OSContext.c"),
            Object(NonMatching, "dolphin/os/OSError.c"),
            Object(NonMatching, "dolphin/os/OSInterrupt.c"),
            Object(NonMatching, "dolphin/os/OSLink.c"),
            Object(NonMatching, "dolphin/os/OSMemory.c"),
            Object(NonMatching, "dolphin/os/OSReset.c"),
            Object(NonMatching, "dolphin/os/OSResetSW.c"),
            Object(NonMatching, "dolphin/os/OSRtc.c"),
            Object(NonMatching, "dolphin/os/OSSync.c"),
            Object(NonMatching, "dolphin/os/OSThread.c"),
            Object(NonMatching, "dolphin/os/OSTime.c"),
            Object(NonMatching, "dolphin/os/__ppc_eabi_init.c"),
            Object(NonMatching, "dolphin/os/OSMutex.c"),
            Object(NonMatching, "dolphin/os/OSReboot.c"),
            Object(NonMatching, "dolphin/os/OSFont.c"),
        ],
    ),
    DolphinLib(
        "dvd",
        [
            Object(NonMatching, "dolphin/dvd/dvdfs.c"),
            Object(NonMatching, "dolphin/dvd/dvd.c"),
            Object(NonMatching, "dolphin/dvd/dvdqueue.c"),
            Object(NonMatching, "dolphin/dvd/dvderror.c"),
            Object(NonMatching, "dolphin/dvd/fstload.c"),
            Object(NonMatching, "dolphin/dvd/dvdlow.c"),
        ],
    ),
    DolphinLib(
        "exi",
        [
            Object(NonMatching, "dolphin/exi/EXIBios.c"),
            Object(NonMatching, "dolphin/exi/EXIUart.c"),
        ],
    ),
    DolphinLib(
        "db",
        [
            Object(NonMatching, "dolphin/db/db.c"),
        ],
    ),
    DolphinLib(
        "pad",
        [
            Object(NonMatching, "dolphin/pad/Pad.c"),
        ],
    ),
    DolphinLib(
        "si",
        [
            Object(NonMatching, "dolphin/si/SIBios.c"),
            Object(NonMatching, "dolphin/si/SISamplingRate.c"),
            Object(NonMatching, "dolphin/si/SISteering.c"),
            Object(NonMatching, "dolphin/si/SISteeringXfer.c"),
            Object(NonMatching, "dolphin/si/SISteeringAuto.c"),
        ],
    ),
    DolphinLib(
        "vi",
        [
            Object(NonMatching, "dolphin/vi/vi.c"),
        ],
    ),
    DolphinLib(
        "gx",
        [
            Object(NonMatching, "dolphin/gx/GXInit.c"),
            Object(NonMatching, "dolphin/gx/GXFifo.c"),
            Object(NonMatching, "dolphin/gx/GXAttr.c"),
            Object(NonMatching, "dolphin/gx/GXMisc.c"),
            Object(NonMatching, "dolphin/gx/GXGeometry.c"),
            Object(NonMatching, "dolphin/gx/GXFrameBuf.c"),
            Object(NonMatching, "dolphin/gx/GXLight.c"),
            Object(NonMatching, "dolphin/gx/GXTexture.c"),
            Object(NonMatching, "dolphin/gx/GXBump.c"),
            Object(NonMatching, "dolphin/gx/GXTransform.c"),
            Object(NonMatching, "dolphin/gx/GXPerf.c"),
        ],
    ),
    DolphinLib(
        "mtx",
        [
            Object(NonMatching, "dolphin/mtx/mtx.c"),
            Object(NonMatching, "dolphin/mtx/mtx44.c"),
            Object(NonMatching, "dolphin/mtx/vec.c"),
        ],
    ),
    DolphinLib(
        "ai",
        [
            Object(NonMatching, "dolphin/ai/ai.c"),
        ],
    ),
    DolphinLib(
        "ar",
        [
            Object(NonMatching, "dolphin/ar/ar.c"),
            Object(NonMatching, "dolphin/ar/arq.c"),
        ],
    ),
    DolphinLib(
        "card",
        [
            Object(NonMatching, "dolphin/card/CARDBios.c"),
            Object(NonMatching, "dolphin/card/CARDRdwr.c"),
            Object(NonMatching, "dolphin/card/CARDBlock.c"),
            Object(NonMatching, "dolphin/card/CARDDir.c"),
            Object(NonMatching, "dolphin/card/CARDCheck.c"),
            Object(NonMatching, "dolphin/card/CARDMount.c"),
            Object(NonMatching, "dolphin/card/CARDFormat.c"),
            Object(NonMatching, "dolphin/card/CARDOpen.c"),
            Object(NonMatching, "dolphin/card/CARDCreate.c"),
            Object(NonMatching, "dolphin/card/CARDRead.c"),
            Object(NonMatching, "dolphin/card/CARDWrite.c"),
            Object(NonMatching, "dolphin/card/CARDDelete.c"),
            Object(NonMatching, "dolphin/card/CARDStat.c"),
            Object(NonMatching, "dolphin/card/CARDNet.c"),
            Object(NonMatching, "dolphin/card/CARDUnlock.c"),
        ],
    ),
    DolphinLib(
        "ax",
        [
            Object(NonMatching, "dolphin/ax/AXAlloc.c"),
            Object(NonMatching, "dolphin/ax/AXAux.c"),
            Object(NonMatching, "dolphin/ax/AXCL.c"),
            Object(NonMatching, "dolphin/ax/AXOut.c"),
            Object(NonMatching, "dolphin/ax/AXSPB.c"),
            Object(NonMatching, "dolphin/ax/AXVPB.c"),
            Object(NonMatching, "dolphin/ax/AXProf.c"),
        ],
    ),
    DolphinLib(
        "dtk",
        [
            Object(NonMatching, "dolphin/dtk/dtk.c"),
        ],
    ),
    DolphinLib(
        "dsp",
        [
            Object(NonMatching, "dolphin/dsp/dsp.c"),
            Object(NonMatching, "dolphin/dsp/dsp_debug.c"),
            Object(NonMatching, "dolphin/dsp/dsp_task.c"),
        ],
    ),
    GameLib(
        "game",
        [
            Object(NonMatching, "game/tu_800032C0.cpp"),
            Object(NonMatching, "game/dash.cpp"),
            Object(NonMatching, "game/race.cpp"),
            Object(NonMatching, "game/tu_80017848.cpp"),
            Object(NonMatching, "game/tu_8001BB74.cpp"),
            Object(NonMatching, "game/tu_8001FB14.cpp"),
            Object(NonMatching, "game/tu_80020794.cpp"),
            Object(NonMatching, "game/tu_80020CB4.cpp"),
            Object(NonMatching, "game/tu_80020D4C.cpp"),
            Object(NonMatching, "game/tu_80021748.cpp"),
            Object(NonMatching, "game/tu_80023FB4.cpp"),
            Object(NonMatching, "game/tu_80024154.cpp"),
            Object(NonMatching, "game/tu_800241D4.cpp"),
            Object(NonMatching, "game/tu_800243BC.cpp"),
            Object(NonMatching, "game/tu_80026860.cpp"),
            Object(NonMatching, "game/tu_8002710C.cpp"),
            Object(NonMatching, "game/tu_8002E0EC.cpp"),
            Object(NonMatching, "game/tu_8002F5F4.cpp"),
            Object(NonMatching, "game/tu_80056D78.cpp"),
            Object(NonMatching, "game/tu_80057534.cpp"),
            Object(NonMatching, "game/tu_80057604.cpp"),
            Object(NonMatching, "game/tu_80057C88.cpp"),
            Object(NonMatching, "game/tu_8005A8D0.cpp"),
            Object(NonMatching, "game/tu_8005B3BC.cpp"),
            Object(NonMatching, "game/tu_8005B908.cpp"),
            Object(NonMatching, "game/tu_8005EA70.cpp"),
            Object(NonMatching, "game/tu_80063D38.cpp"),
            Object(NonMatching, "game/tu_80064D60.cpp"),
            Object(NonMatching, "game/tu_80066B4C.cpp"),
            Object(NonMatching, "game/pit.cpp"),
            Object(NonMatching, "game/tu_80069BC0.cpp"),
            Object(NonMatching, "game/tu_8006A844.cpp"),
            Object(NonMatching, "game/tu_8006B18C.cpp"),
            Object(NonMatching, "game/tu_8006B734.cpp"),
            Object(NonMatching, "game/tu_80070C70.cpp"),
            Object(NonMatching, "game/tu_8007132C.cpp"),
            Object(NonMatching, "game/tu_80071444.cpp"),
            Object(NonMatching, "game/tu_80071758.cpp"),
            Object(NonMatching, "game/tu_80072E88.cpp"),
            Object(NonMatching, "game/tu_80075AF0.cpp"),
            Object(NonMatching, "game/tu_8007764C.cpp"),
            Object(NonMatching, "game/tu_80077FF8.cpp"),
            Object(NonMatching, "game/tu_8007AC30.cpp"),
            Object(NonMatching, "game/tu_8008A360.cpp"),
            Object(NonMatching, "game/tu_8008E310.cpp"),
            Object(NonMatching, "game/tu_80098E40.cpp"),
            Object(NonMatching, "game/tu_8009F928.cpp"),
            Object(NonMatching, "game/tu_800A0674.cpp"),
            Object(NonMatching, "game/tu_800A3550.cpp"),
            Object(NonMatching, "game/tu_800A3BD4.cpp"),
            Object(NonMatching, "game/tu_800A6FBC.cpp"),
            Object(NonMatching, "game/tu_800AA068.cpp"),
            Object(NonMatching, "game/tu_800AB314.cpp"),
            Object(NonMatching, "game/tu_800AD5BC.cpp"),
            Object(NonMatching, "game/tu_800AE158.cpp"),
            Object(NonMatching, "game/tu_800B48E4.cpp"),
            Object(NonMatching, "game/tu_800B5144.cpp"),
            Object(NonMatching, "game/tu_800B58CC.cpp"),
            Object(NonMatching, "game/tu_800BCB38.cpp"),
            Object(NonMatching, "game/tu_800BD9A4.cpp"),
            Object(NonMatching, "game/tu_800C20D8.cpp"),
            Object(NonMatching, "game/tu_800C42FC.cpp"),
            Object(NonMatching, "game/tu_800D0C10.cpp"),
            Object(NonMatching, "game/tu_800D1270.cpp"),
            Object(NonMatching, "game/tu_800D17C0.cpp"),
            Object(NonMatching, "game/tu_800D58A0.cpp"),
            Object(NonMatching, "game/tu_800D7488.cpp"),
            Object(NonMatching, "game/tu_800D7CF4.cpp"),
            Object(NonMatching, "game/tu_800D7DA8.cpp"),
            Object(NonMatching, "game/tu_800D8878.cpp"),
            Object(NonMatching, "game/tu_800DA83C.cpp"),
            Object(NonMatching, "game/tu_800DAE6C.cpp"),
            Object(NonMatching, "game/tu_800DBD6C.cpp"),
            Object(NonMatching, "game/tu_800E04C0.cpp"),
            Object(NonMatching, "game/tu_800E0B48.cpp"),
            Object(NonMatching, "game/tu_800E1538.cpp"),
            Object(NonMatching, "game/tu_800E17A4.cpp"),
            Object(NonMatching, "game/tu_800E1BEC.cpp"),
            Object(NonMatching, "game/tu_800E216C.cpp"),
            Object(NonMatching, "game/tu_800E5228.cpp"),
            Object(NonMatching, "game/event.cpp"),
            Object(NonMatching, "game/tu_800EC690.cpp"),
            Object(NonMatching, "game/tu_800ED618.cpp"),
            Object(NonMatching, "game/tu_800EE738.cpp"),
            Object(NonMatching, "game/tu_800EE850.cpp"),
            Object(NonMatching, "game/tu_800EF6D0.cpp"),
            Object(NonMatching, "game/tu_800F0BD8.cpp"),
            Object(NonMatching, "game/tu_800F0E68.cpp"),
            Object(NonMatching, "game/tu_800F14F8.cpp"),
            Object(NonMatching, "game/tu_800F1F10.cpp"),
            Object(NonMatching, "game/tu_800F2A9C.cpp"),
            Object(NonMatching, "game/tu_800F37C4.cpp"),
            Object(NonMatching, "game/tu_800F39C4.cpp"),
            Object(NonMatching, "game/tu_800F3EEC.cpp"),
            Object(NonMatching, "game/tu_800F3F88.cpp"),
            Object(NonMatching, "game/tu_800F4020.cpp"),
            Object(NonMatching, "game/tu_800F4FB4.cpp"),
            Object(NonMatching, "game/tu_800F6044.cpp"),
            Object(NonMatching, "game/soundmgr.cpp"),
            Object(NonMatching, "game/tu_800F8F74.cpp"),
            Object(NonMatching, "game/tu_800F995C.cpp"),
            Object(NonMatching, "game/tu_800FA620.cpp"),
            Object(NonMatching, "game/tu_800FAD90.cpp"),
            Object(NonMatching, "game/tu_800FB0B0.cpp"),
            Object(NonMatching, "game/tu_800FB748.cpp"),
            Object(NonMatching, "game/tu_800FB820.cpp"),
            Object(NonMatching, "game/tu_8010948C.cpp"),
            Object(NonMatching, "game/tu_8010CFB8.cpp"),
            Object(NonMatching, "game/tu_8011B590.cpp"),
            Object(NonMatching, "game/tu_8011CD10.cpp"),
            Object(NonMatching, "game/tu_801208EC.cpp"),
            Object(NonMatching, "game/tu_801211E4.cpp"),
            Object(NonMatching, "game/tu_80122B2C.cpp"),
            Object(NonMatching, "game/tu_80124394.cpp"),
            Object(NonMatching, "game/tu_80126E30.cpp"),
            Object(NonMatching, "game/tu_8012813C.cpp"),
            Object(NonMatching, "game/tu_80128DD0.cpp"),
            Object(NonMatching, "game/tu_8012901C.cpp"),
            Object(NonMatching, "game/tu_80129950.cpp"),
            Object(NonMatching, "game/tu_80129DD8.cpp"),
            Object(NonMatching, "game/tu_8012B51C.cpp"),
            Object(NonMatching, "game/tu_8012F928.cpp"),
            Object(NonMatching, "game/tu_8013008C.cpp"),
            Object(NonMatching, "game/tu_801356F8.cpp"),
            Object(NonMatching, "game/tu_801361E8.cpp"),
            Object(NonMatching, "game/tu_80136EEC.cpp"),
            Object(NonMatching, "game/tu_80137D94.cpp"),
            Object(NonMatching, "game/tu_8013863C.cpp"),
            Object(NonMatching, "game/tu_8013A9C4.cpp"),
            Object(NonMatching, "game/tu_8013C598.cpp"),
            Object(NonMatching, "game/tu_8013E470.cpp"),
            Object(NonMatching, "game/tu_8013F65C.cpp"),
            Object(NonMatching, "game/tu_801411AC.cpp"),
            Object(NonMatching, "game/tu_801424A0.cpp"),
            Object(NonMatching, "game/tu_80144A2C.cpp"),
            Object(NonMatching, "game/tu_80145434.cpp"),
            Object(NonMatching, "game/tu_80145918.cpp"),
            Object(NonMatching, "game/tu_80145DB8.cpp"),
            Object(NonMatching, "game/tu_801461F4.cpp"),
            Object(NonMatching, "game/tu_80146314.cpp"),
            Object(NonMatching, "game/tu_801466A8.cpp"),
            Object(NonMatching, "game/tu_80147320.cpp"),
            Object(NonMatching, "game/tu_8014841C.cpp"),
            Object(NonMatching, "game/tu_80149160.cpp"),
            Object(NonMatching, "game/tu_80149600.cpp"),
            Object(NonMatching, "game/tu_80149CC4.cpp"),
            Object(NonMatching, "game/tu_8014AD38.cpp"),
            Object(NonMatching, "game/tu_8014B888.cpp"),
            Object(NonMatching, "game/tu_8014D6C8.cpp"),
            Object(NonMatching, "game/tu_8014E040.cpp"),
            Object(NonMatching, "game/tu_8014E1B8.cpp"),
            Object(NonMatching, "game/tu_8014E304.cpp"),
            Object(NonMatching, "game/tu_8014EA74.cpp"),
            Object(NonMatching, "game/tu_80153994.cpp"),
            Object(NonMatching, "game/tu_80153E20.cpp"),
            Object(NonMatching, "game/tu_80153EE8.cpp"),
            Object(NonMatching, "game/tu_801552A4.cpp"),
            Object(NonMatching, "game/tu_8015690C.cpp"),
            Object(NonMatching, "game/tu_8015743C.cpp"),
            Object(NonMatching, "game/tu_80157578.cpp"),
            Object(NonMatching, "game/tu_801576E0.cpp"),
            Object(NonMatching, "game/tu_801577F4.cpp"),
            Object(NonMatching, "game/tu_80157F1C.cpp"),
            Object(NonMatching, "game/tu_8015A1F4.cpp"),
            Object(NonMatching, "game/tu_8015A95C.cpp"),
            Object(NonMatching, "game/tu_8015BEEC.cpp"),
            Object(NonMatching, "game/tu_8015E9CC.cpp"),
            Object(NonMatching, "game/tu_8015FABC.cpp"),
            Object(NonMatching, "game/tu_8016000C.cpp"),
            Object(NonMatching, "game/tu_80160914.cpp"),
            Object(NonMatching, "game/tu_80161350.cpp"),
            Object(NonMatching, "game/tu_80164700.cpp"),
            Object(NonMatching, "game/tu_801650B0.cpp"),
            Object(NonMatching, "game/tu_8016761C.cpp"),
            Object(NonMatching, "game/tu_80167D84.cpp"),
            Object(NonMatching, "game/tu_801681D4.cpp"),
            Object(NonMatching, "game/tu_80168788.cpp"),
            Object(NonMatching, "game/tu_8016A70C.cpp"),
            Object(NonMatching, "game/tu_8016CB64.cpp"),
            Object(NonMatching, "game/tu_8016D618.cpp"),
            Object(NonMatching, "game/tu_8016DAF0.cpp"),
            Object(NonMatching, "game/tu_8016E230.cpp"),
            Object(NonMatching, "game/tu_8016E5FC.cpp"),
            Object(NonMatching, "game/tu_80172D40.cpp"),
            Object(NonMatching, "game/tu_8017449C.cpp"),
            Object(NonMatching, "game/tu_801746A4.cpp"),
            Object(NonMatching, "game/tu_8017660C.cpp"),
            Object(NonMatching, "game/tu_80176FE8.cpp"),
            Object(NonMatching, "game/tu_80177BE4.cpp"),
            Object(NonMatching, "game/tu_80179D28.cpp"),
            Object(NonMatching, "game/tu_8017A180.cpp"),
            Object(NonMatching, "game/tu_8017B720.cpp"),
            Object(NonMatching, "game/Skid.cpp"),
            Object(NonMatching, "game/tu_8017FB04.cpp"),
            Object(NonMatching, "game/tu_8018086C.cpp"),
            Object(NonMatching, "game/tu_801823E8.cpp"),
            Object(NonMatching, "game/tu_80182AB8.cpp"),
            Object(NonMatching, "game/tu_80183D5C.cpp"),
            Object(NonMatching, "game/tu_80183F44.cpp"),
            Object(NonMatching, "game/tu_80184E80.cpp"),
            Object(NonMatching, "game/tu_8018778C.cpp"),
            Object(NonMatching, "game/tu_801879F0.cpp"),
            Object(NonMatching, "game/tu_80188234.cpp"),
            Object(NonMatching, "game/tu_80188560.cpp"),
            Object(NonMatching, "game/tu_8018FCC0.cpp"),
            Object(NonMatching, "game/tu_80190B00.cpp"),
            Object(NonMatching, "game/tu_80190F54.cpp"),
            Object(NonMatching, "game/tu_80192C2C.cpp"),
            Object(NonMatching, "game/tu_801957EC.cpp"),
            Object(NonMatching, "game/tu_80195F3C.cpp"),
            Object(NonMatching, "game/tu_80198568.cpp"),
            Object(NonMatching, "game/tu_8019868C.cpp"),
            Object(NonMatching, "game/tu_80198724.cpp"),
            Object(NonMatching, "game/tu_80198FF8.cpp"),
            Object(NonMatching, "game/tu_801A082C.cpp"),
            Object(NonMatching, "game/tu_801A0A6C.cpp"),
            Object(NonMatching, "game/kernel.cpp"),
            Object(NonMatching, "game/tu_801A1EA8.cpp"),
            Object(NonMatching, "game/file.cpp"),
            Object(NonMatching, "game/tu_801A307C.cpp"),
            Object(NonMatching, "game/tu_801A3BB4.cpp"),
            Object(NonMatching, "game/tu_801A3C4C.cpp"),
            Object(NonMatching, "game/tu_801A3E84.cpp"),
            Object(NonMatching, "game/tu_801A407C.cpp"),
            Object(NonMatching, "game/tu_801A41B8.cpp"),
            Object(NonMatching, "game/tu_801A5938.cpp"),
            Object(NonMatching, "game/tu_801A5E2C.cpp"),
            Object(NonMatching, "game/tu_801A60E4.cpp"),
            Object(NonMatching, "game/tu_801A7E60.cpp"),
            Object(NonMatching, "game/tu_801A9EF8.cpp"),
            Object(NonMatching, "game/tu_801AA258.cpp"),
            Object(NonMatching, "game/tu_801AAA04.cpp"),
            Object(NonMatching, "game/tu_801AB040.cpp"),
            Object(NonMatching, "game/tu_801CBFCC.cpp"),
            Object(NonMatching, "game/tu_801CE7B0.cpp"),
            Object(NonMatching, "game/tu_801D3078.cpp"),
            Object(NonMatching, "game/tu_801D34C4.cpp"),
            Object(NonMatching, "game/tu_801D3AF8.cpp"),
            Object(NonMatching, "game/tu_801D41F4.cpp"),
            Object(NonMatching, "game/tu_801D44B8.cpp"),
            Object(NonMatching, "game/tu_801D4744.cpp"),
            Object(NonMatching, "game/tu_801D4868.cpp"),
            Object(NonMatching, "game/tu_801D4EA4.cpp"),
            Object(NonMatching, "game/tu_801D5F54.cpp"),
            Object(NonMatching, "game/tu_801D74EC.cpp"),
            Object(NonMatching, "game/tu_801D905C.cpp"),
            Object(NonMatching, "game/tu_801DB7D0.cpp"),
            Object(NonMatching, "game/tu_801DDE24.cpp"),
            Object(NonMatching, "game/tu_801DEEEC.cpp"),
            Object(NonMatching, "game/tu_801DFD20.cpp"),
            Object(NonMatching, "game/tu_801E10A4.cpp"),
            Object(NonMatching, "game/tu_801E16C8.cpp"),
        ],
    ),
]


# Optional callback to adjust link order. This can be used to add, remove, or reorder objects.
# This is called once per module, with the module ID and the current link order.
#
# For example, this adds "dummy.c" to the end of the DOL link order if configured with --non-matching.
# "dummy.c" *must* be configured as a Matching (or Equivalent) object in order to be linked.
def link_order_callback(module_id: int, objects: List[str]) -> List[str]:
    # Don't modify the link order for matching builds
    if not config.non_matching:
        return objects
    if module_id == 0:  # DOL
        return objects + ["dummy.c"]
    return objects


# Uncomment to enable the link order callback.
# config.link_order_callback = link_order_callback


# Optional extra categories for progress tracking
# Adjust as desired for your project
config.progress_categories = [
    ProgressCategory("game", "Game Code"),
    ProgressCategory("sdk", "SDK Code"),
]
config.progress_each_module = args.verbose
# Optional extra arguments to `objdiff-cli report generate`
config.progress_report_args = [
    # Marks relocations as mismatching if the target value is different
    # Default is "functionRelocDiffs=none", which is most lenient
    # "--config functionRelocDiffs=data_value",
]

if args.mode == "configure":
    # Write build.ninja and objdiff.json
    generate_build(config)
elif args.mode == "progress":
    # Print progress information
    calculate_progress(config)
else:
    sys.exit("Unknown mode: " + args.mode)
