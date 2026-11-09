/* GN2E70 linker script for SN Systems ngcld (ProDG), GNU ld syntax.
 *
 * Sections are laid out back to back, so the build still links when code changes size.
 * With the original code this reproduces the shipped main.dol exactly:
 *
 *   .init   0x80003100   .text   0x800032C0   .ctdt  0x80212B40   .rodata 0x80212F60
 *   .data   0x8024E960   .bss    0x80261500   .sdata 0x80313FA0   .sbss   0x80314720
 *   .sdata2 0x80314CA0
 *
 * ProDG reaches .sdata, .sbss *and* .sdata2 through r13 (_SDA_BASE_). r2 is loaded with
 * _SDA2_BASE_ in __start, but nothing in the game uses it.
 *
 * The object list is supplied by tools/gn2e70/ngcld.py as an INPUT(...) block, since
 * ngcld has no response-file support.
 */
ENTRY(__start)

SECTIONS
{
    .init   0x80003100 : { *(.init) }
    .text              : { *(.text) }
    .ctdt              : { *(.ctdt) }   /* merged .ctors + .dtors (see README) */
    .rodata            : { *(.rodata) }
    .data              : { *(.data) }
    .bss               : { *(.bss) }
    .sdata             : { *(.sdata) }
    .sbss              : { *(.sbss) }
    .sdata2            : { *(.sdata2) }

    _SDA_BASE_  = ADDR(.sdata) + 0x8000;
    _SDA2_BASE_ = _SDA_BASE_ + 0x10000;

    /* Stack and arena, as in the original: 0x20 bytes after .sdata2 (probably .sbss2,
     * which isn't stored in the DOL), a 0x60000-byte stack, then the arena. */
    _stack_end     = ADDR(.sdata2) + SIZEOF(.sdata2) + 0x20;
    _stack_addr    = _stack_end + 0x60000;
    _db_stack_addr = _stack_addr;
    _db_stack_end  = _stack_addr;
    __ArenaLo      = _stack_addr + 0x20;
    __ArenaHi      = 0x81780000;
}
