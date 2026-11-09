MEMORY
{
    text : origin = $ORIGIN
}

SECTIONS
{
    GROUP:
    {
        $SECTIONS
        .stack ALIGN(0x100):{}
    } > text

    /* GN2E70 (ProDG) memory layout, taken from the original main.dol:
     *   _stack_end  = 0x80315E60  (0x20 past the end of .sdata2; probably .sbss2,
     *                              which isn't stored in the DOL)
     *   _stack_addr = 0x80375E60  (_stack_end + 0x60000)
     *   __ArenaLo   = 0x80375E80  (_stack_addr + 0x20; no separate debugger stack)
     */
    _stack_end = $LAST_SECTION_SYMBOL + SIZEOF($LAST_SECTION_NAME) + 0x20;
    _stack_addr = _stack_end + $STACKSIZE;
    _db_stack_addr = _stack_addr;
    _db_stack_end = _stack_addr;
    __ArenaLo = _stack_addr + 0x20;
    __ArenaHi = $ARENAHI;
}

FORCEACTIVE
{
    $FORCEACTIVE
}
