/* <stdarg.h> for SN Systems ProDG (GCC 2.95) on PowerPC EABI.
 *
 * ProDG's compiler package ships no system headers, so this follows GCC 2.95's
 * va-ppc.h layout: va_start copies the register-save block returned by
 * __builtin_saveregs() into the va_list (a 12-byte struct copy, as seen in the game).
 * va_arg isn't defined yet; add it from va-ppc.h when a function needs it.
 */
#ifndef _STDARG_H
#define _STDARG_H

typedef struct __va_list_tag {
    unsigned char gpr;        /* next general-purpose register (0-8) */
    unsigned char fpr;        /* next floating-point register (0-8) */
    char* overflow_arg_area;  /* arguments passed on the stack */
    char* reg_save_area;      /* saved r3-r10 and f1-f8 */
} __va_list_tag;

typedef __va_list_tag va_list[1];

#define va_start(ap, last) \
    (__builtin_next_arg(last), *(ap) = *(__va_list_tag*)__builtin_saveregs())
#define va_end(ap) ((void)0)

#endif
