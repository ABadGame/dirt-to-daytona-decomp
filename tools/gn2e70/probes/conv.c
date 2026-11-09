/* ProDG version probes: int<->float conversions. */
extern float fn_80024FA0(float);
static const float K1 = 0.25f;
static const float K2 = 0.75f;
static const float K3 = 3.0f;

// @target 8005BB20
float probe_8005BB20(int x) { return (float)(x - 0x55) * K1; }

// @target 800A0694
float probe_800A0694(int a, int b) { return (float)(a - b) * K2; }

// @target 80020650
int probe_80020650(void) { return (int)fn_80024FA0(K3); }
