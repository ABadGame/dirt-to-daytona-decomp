// Translation unit 0x8005B908-0x8005EA70 (ends at a GCC static-initializer stub).
// Its strings include AI skill-table warnings ("AI: Warning: ..."), so this is
// probably part of the AI driver code. Built with ProDG: ngccc -O2 -fexceptions.

extern "C" {

static const float lbl_80219A30 = 0.25f;  // TODO: real value/name (masked by objdiff)

// Converts a 1-based value offset by 0x55 to a scaled float.
float fn_8005BB20(int x) { return (float)(x - 0x55) * lbl_80219A30; }

}  // extern "C"
