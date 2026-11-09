// Translation unit 0x8005B908-0x8005EA70 (ends at a GCC static-initializer stub).
// Its strings include AI skill-table warnings ("AI: Warning: ..."), so this is
// probably part of the AI driver code. Built with ProDG:
//   ngccc -O2 -fexceptions -fvtable-thunks -G 0
//
// Functions marked `// @target ADDRESS` can be checked on their own with
//   python tools/gn2e70/prodg_probe.py src/game/tu_8005B908.cpp --versions 3.5 \n//     "--flags=-O2 -fexceptions -fvtable-thunks -G 0"

#include <stdarg.h>

// Named-value table (virtual interface). Only the slots used here are known:
// with -fvtable-thunks, slot k of the vtable is at offset 8 + 4*k.
class ValueTable {
public:
    virtual ~ValueTable();                   // 0x08
    virtual int Has(const char* name);       // 0x0C
    virtual int HasEntry(const char* name);  // 0x10
    virtual void v3();                       // 0x14
    virtual void v4();                       // 0x18
    virtual void v5();                       // 0x1C
    virtual void v6();                       // 0x20
    virtual float GetFloat(const char* name);  // 0x24
    virtual float GetFloatOr(const char* name, float def);  // 0x28
    virtual int GetInt(const char* name);    // 0x2C
};

extern "C" {

// One 0x14-byte record per car slot (meaning of the fields not known yet).
struct AIEntry {
    float a;  // 0x00
    float b;  // 0x04
    float c;  // 0x08
    float d;  // 0x0C
    float e;  // 0x10
};

struct CarInfo {
    char pad[0x600];
    int id;  // 0x600
};

// Global AI data at 0x80276A48 (dtk splits it into several lbl_ symbols).
struct AIData {
    AIEntry def;        // 0x000; returned for slot 0x3FFFFFFF
    AIEntry slots[49];  // 0x014
    float scale;        // 0x3E8
    float f3EC;         // 0x3EC
};
extern AIData lbl_80276A48;
extern float lbl_80276A1C;

// 0x80276F4C
struct AISettings {
    float f0;  // 0x0
    int i4;    // 0x4
    float f8;  // 0x8
};
extern AISettings lbl_80276F4C;

// Returned by fn_80065A74; only the fields used here are known.
struct DriverState {
    int i0;          // 0x00
    bool active;     // 0x04 (bool is 4 bytes with GCC 2.95 on PowerPC)
    char pad8[0x18 - 0x08];
    char block18[0x38 - 0x18];  // 0x18
    char block38[4];            // 0x38
};

extern int lbl_80251C10;    // .data
extern int lbl_80276A2C;    // limit for lbl_80276A30
extern int lbl_80276A30;    // counter

DriverState* fn_80065A74(int slot);
void fn_8006AF58(void);
void fn_800643F4(int value);
int fn_80071D70(void);
float fn_8005E7F8(void);
float fn_8005E890(void);
// A 0x20-byte block of per-range settings (contents not known yet).
struct RangeData {
    char bytes[0x20];
};

// Linked list of settings ranges; freed by fn_8005CFE0, searched by fn_8005E6C4.
struct ListNode {
    float min;       // 0x00
    float max;       // 0x04
    RangeData data;  // 0x08
    ListNode* next;  // 0x28
};
extern ListNode* lbl_80276F28;
extern RangeData lbl_80276F2C;  // default settings when no range matches
extern ValueTable* lbl_80276A20;  // current AI tuning table, may be null
extern int lbl_80276A28;

struct AIObject {
    char pad[0x58];
    int track;  // 0x58
    int ready;  // 0x5C
};
extern AIObject* lbl_80276E38[];  // 0x80276E38: one AI object per slot (48)

// Entry compared by fn_8005C020 (e.g. for sorting).
struct RankEntry {
    int i0;     // 0x0
    int valid;  // 0x4; negative = no value
    int value;  // 0x8
};

// AI state block at 0x80276A00 (only the fields used here are known).
struct AIState {
    float f0;   // 0x00
    float f4;   // 0x04
    float f8;   // 0x08
    float fC;   // 0x0C
    float f10;  // 0x10
    int i14;    // 0x14
};
extern AIState lbl_80276A00;
extern int lbl_80276A38;
extern int lbl_80251C04;  // count of failed default.ili loads
extern int lbl_80251BF4;
extern const float lbl_802135C0;  // 4.0f, defined in another file
extern const float lbl_802135C4;  // 4.0f, defined in another file

void fn_801A1F68(const char* fmt, ...);  // debug warning print (kernel.cpp)
void fn_801A3830(void* ptr);             // memory free (Mem*)
int sprintf(char* buf, const char* fmt, ...);
char* strcpy(char* dst, const char* src);
int fn_8002371C(void* buf, int flags, int* outA, float* outTime);
void fn_80061FC0(AIObject* obj, int arg);
int fn_80062064(AIObject* obj, const char* file);  // loads an AI data file
void fn_800707D0(void);
void fn_80069FC8(void);
void fn_800696DC(void);
void fn_80064CBC(void);
void fn_8008F214(void);
float fn_800638A0(void);
float fn_8005E7A4(void);
float fn_8005E4C0(void);
float fn_8005E89C(void);
int fn_8005E7B0(void);
void fn_80062004(AIObject* obj, int flags);  // destructor (GCC 2.95 passes 2 for "don't free")
void fn_80069634(void);
void fn_80064C70(void);
void fn_80069F40(void);
void fn_8007078C(void);
extern int lbl_80276A24;
extern int lbl_80276A34;  // a ValueTable* stored as int
void fn_8005BA48(AIObject* obj, int arg);
char* fn_8005E5B0(int id, char* out);
int fn_8005E578(unsigned int slot);
// Local helper object used by fn_8005BE50 (0x90 bytes; built by fn_800620D8, torn down
// by fn_800621F4(obj, 2)). Only the fields used here are known.
struct TrackSub {
    char pad[0x10];
    int id;        // 0x10
    char pad14[0x60 - 0x14];
    int enabled;   // 0x60
};
struct TrackData {
    char pad[0x610];
    TrackSub sub;  // 0x610
};
struct TrackProbe {
    char pad[0x54];
    TrackData* track;  // 0x54
    char pad58[0x90 - 0x58];
};
struct ProbeTarget {
    char pad[0x24];
    float dist;  // 0x24
};
void fn_800620D8(TrackProbe* probe, int arg);
void fn_800621F4(TrackProbe* probe, int flags);
float fn_80070B54(void);
ProbeTarget* fn_800633F0(TrackProbe* probe, int id);

// A float range (filled in by fn_8005B970).
struct FloatRange {
    float min;  // 0x0
    float max;  // 0x4
};
struct FloatArray;  // opaque; element access via fn_801E9BB8
struct TrackInfo {
    char pad[0x60];
    const char* name;  // 0x60
};
float* fn_801E9BB8(FloatArray* arr, int index);
ValueTable* fn_8005B3DC(const char* file);  // loads a .val table
void fn_8005B884(ValueTable* table);        // releases it
int fn_80017100(void);                      // number of tracks
TrackInfo* fn_8001710C(int index);
void fn_801A2028(const char* fmt, ...);     // fatal error ("PANIC")
const char* fn_8005BBBC(int level);

float fn_80057784(int curve, float a, float b);
int vsprintf(char* buf, const char* fmt, va_list args);
void fn_80129AE0(int a, int b, char* text, int c);
void fn_80064108(int arg, int track);
void fn_8006416C(int arg, int track);
void fn_80064538(int arg);
void fn_8005DB78(void);
void fn_800707FC(void);
void fn_80069738(void);
void fn_8005D034(void);
void fn_8006A038(void);
void fn_8006AFD4(void);
int fn_80039624(void);
int fn_80039724(float t);
float fn_8005E29C(const char* name, float def);  // named tuning value with a default
CarInfo* fn_800738D8(int slot);

// Shared by fn_8005E29C and fn_8005E1D4 (fn_8005E29C is defined after fn_8005E1D4's
// address, so the compiler can't have inlined it there; this is likely a header inline).
static inline float getTuningFloat(const char* name, float def) {
    if (lbl_80276A20 && lbl_80276A20->Has(name)) {
        return lbl_80276A20->GetFloat(name);
    }
    return def;
}

// Number of values used from an array: at most 128.
static inline int fn_rangeCount(FloatArray* arr) {
    int n = *(int*)arr;
    if (n > 128) {
        n = 128;
    }
    return n;
}

// @target 8005BB20
float fn_8005BB20(int x) { return (float)(x - 0x55) * 0.05f; }

// @target 8005D4CC
AIObject* fn_8005D4CC(int i) { return lbl_80276E38[i]; }

// @target 8005DF08
void fn_8005DF08(void) {}

// @target 8005E1CC
int fn_8005E1CC(void) { return 0; }

// @target 8005E394
float fn_8005E394(void) { return 0.02f; }

// @target 8005E3A0
AIEntry* fn_8005E3A0(int slot) {
    if (slot == 0x3FFFFFFF) {
        return &lbl_80276A48.def;
    }
    return &lbl_80276A48.slots[slot];
}

// @target 8005E3D0
int fn_8005E3D0(float* out) {
    *out = lbl_80276F4C.f0;
    return lbl_80276F4C.i4;
}

// @target 8005E3E8
float fn_8005E3E8(void) { return lbl_80276F4C.f8; }

// @target 8005E3F4
float fn_8005E3F4(int slot) { return fn_8005E3A0(slot)->c; }

// @target 8005E418
float fn_8005E418(int slot) {
    AIEntry* e = fn_8005E3A0(slot);
    return e->c + e->c * fn_80057784(3, e->d, e->e);
}

// @target 8005E45C
float fn_8005E45C(int slot) {
    AIEntry* e = fn_8005E3A0(slot);
    return e->c + e->c * fn_80057784(1, e->d, e->e);
}

// @target 8005E4A0
float fn_8005E4A0(int slot) { return fn_8005E418(slot); }

// @target 8005E4C0
float fn_8005E4C0(void) { return lbl_80276A1C; }

// @target 8005E4CC
void fn_8005E4CC(int slot, float value) {
    // Unused, but the original allocates a stack frame for a local like this one
    // (probably left over from removed code); without it the function doesn't match.
    float unused[3];
    lbl_80276A48.slots[slot].b = value;
    lbl_80276A48.slots[slot].a = value;
    lbl_80276A48.slots[slot].c = lbl_80276A48.scale / value;
}

// @target 8005E504
float fn_8005E504(void) { return fn_8005E29C("pit_over", 1.525f); }

// @target 8005E534
float fn_8005E534(void) {
    const float scale = 0.8f;
    float speed = fn_8005E29C("ym_speed_f", 1.0f);
    return speed * scale;
}

// @target 8005E578
int fn_8005E578(unsigned int slot) {
    if (slot > 0x2F) {
        return -1;
    }
    return fn_800738D8(slot)->id;
}

// @target 8005B908
// Clamps value to [min, max].
int fn_8005B908(int value, int min, int max) {
    int result = min;
    if (result < value) {
        result = value;
    }
    return max > result ? result : max;
}

// @target 8005B928
char* fn_8005B928(int slot) { return fn_80065A74(slot)->block18; }

// @target 8005B94C
char* fn_8005B94C(int slot) { return fn_80065A74(slot)->block38; }

// AI difficulty name for a skill level (0-2).
// @target 8005BBBC
const char* fn_8005BBBC(int level) {
    const char* names[3] = {"AIEasy", "AIMedium", "AIHard"};
    return names[level];
}

// @target 8005DEE8
void fn_8005DEE8(void) { fn_8006AF58(); }

// @target 8005E1A4
void fn_8005E1A4(void) { fn_800643F4(lbl_80251C10); }

// @target 8005E6B8
float fn_8005E6B8(void) { return lbl_80276A00.f8; }

// @target 8005E798
RangeData* fn_8005E798(void) { return &lbl_80276F2C; }

// @target 8005E7A4
float fn_8005E7A4(void) { return 76.25f; }

// @target 8005E890
float fn_8005E890(void) { return 4.0f; }

// @target 8005E89C
float fn_8005E89C(void) {
    float result;
    if (fn_80071D70()) {
        result = fn_8005E7F8();
    } else {
        result = fn_8005E890();
    }
    return result;
}

// Takes one from a limited pool; returns false when it's used up.
// @target 8005E940
int fn_8005E940(void) {
    if (lbl_80276A30 < lbl_80276A2C) {
        lbl_80276A30++;
        return 1;
    }
    return 0;
}

// @target 8005E970
void fn_8005E970(void) {
    if (lbl_80276A30 > 0) {
        lbl_80276A30--;
    }
}

// @target 8005E98C
bool fn_8005E98C(void) { return !fn_80065A74(-1)->active; }

// @target 8005BAD8
AIObject* fn_8005BAD8(AIObject* obj, int arg) {
    fn_80061FC0(obj, arg);
    obj->ready = 1;
    fn_8005BA48(obj, arg);
    return obj;
}

// Warns when an AI table lacks an element.
// @target 8005BB60
void fn_8005BB60(ValueTable* table, const char* element, const char* tableName) {
    if (!table->Has(element)) {
        fn_801A1F68("AI: Warning: table \"%s\" has no element \"%s\"", tableName, element);
    }
}

// Reads the ghost car's time, or 60 seconds if there's no ghost.
// @target 8005BF0C
float fn_8005BF0C(void) {
    char buf[16];
    int unk;
    float time;
    float result;
    if (!fn_8002371C(buf, 0, &unk, &time)) {
        fn_801A1F68("AI: Warning: No ghost data.");
        result = 60.0f;
    } else {
        result = time;
    }
    return result;
}

// Frees every node of the list at lbl_80276F28.
// @target 8005CFE0
void fn_8005CFE0(void) {
    while (lbl_80276F28) {
        ListNode* node = lbl_80276F28;
        lbl_80276F28 = node->next;
        fn_801A3830(node);
    }
}

// Formats a signed difference ("+3", "-1"), or an empty string for 0.
// @target 8005DB2C
char* fn_8005DB2C(char* buf, int value) {
    if (value) {
        sprintf(buf, "%+d", value);
    } else {
        buf[0] = 0;
    }
    return buf;
}

// Named float tuning value, or def if there's no table or no such entry.
// @target 8005E29C
float fn_8005E29C(const char* name, float def) { return getTuningFloat(name, def); }

// Named int tuning value, or def.
// @target 8005E31C
int fn_8005E31C(const char* name, int def) {
    if (lbl_80276A20 && lbl_80276A20->Has(name)) {
        return lbl_80276A20->GetInt(name);
    }
    return def;
}

// @target 8005E668
char* fn_8005E668(int slot, char* out) {
    if (slot >= 0) {
        fn_8005E5B0(fn_8005E578(slot), out);
    } else {
        fn_8005E5B0(-40, out);
    }
    return out;
}

// @target 8005E7B0
int fn_8005E7B0(void) { return fn_80071D70() && lbl_80276A28 == 0; }

// Loads the AI data for a track: default.ili, falling back to track.ild.
// @target 8005BA48
void fn_8005BA48(AIObject* obj, int track) {
    obj->track = track;
    if (!fn_80062064(obj, "default.ili")) {
        if (++lbl_80251C04 == 1) {
            fn_801A1F68("Can't load default.ili");
        }
        if (!fn_80062064(obj, "track.ild")) {
            fn_801A1F68("Can't load track.ild");
        }
    }
}

// Compares two entries by value (clamped to 0-100); entries without one sort last.
// @target 8005C020
int fn_8005C020(const RankEntry* a, const RankEntry* b) {
    int va = a->valid >= 0 ? fn_8005B908(a->value, 0, 100) : 9999;
    int vb = b->valid >= 0 ? fn_8005B908(b->value, 0, 100) : 9999;
    return va - vb;
}

// Resets the AI state.
// @target 8005DF0C
void fn_8005DF0C(void) {
    fn_800707D0();
    fn_80069FC8();
    fn_800696DC();
    fn_80064CBC();
    lbl_80276A30 = 0;
    fn_8008F214();
    // This exact order is the only one (of all 120) the compiler schedules like the original.
    lbl_80276A00.f8 = lbl_80276A00.f0;
    lbl_80276A00.i14 = 0;
    lbl_80276A38 = 0;
    lbl_80276F4C.i4 = 0;
    lbl_80276F4C.f8 = 1.0f;
}

// @target 8005E7F8
float fn_8005E7F8(void) {
    float a = (float)fn_8005E7B0();
    float b = (float)((lbl_80251BF4 + 1) / 2);
    return 4.0f + a * lbl_802135C0 + b * lbl_802135C4;
}

// @target 8005E8D0
float fn_8005E8D0(float x) {
    float v;
    if (x >= 0.0f) {
        v = x;
    } else {
        v = fn_8005E89C();  // negative means "use the default"
    }
    float a = fn_800638A0();
    float b = fn_8005E7A4();
    float c = fn_8005E4C0();
    return (a - b) - v * c;
}

// Writes the label for a car: its number, or a tag for the pace car, ghost and wrecker.
// @target 8005E5B0
char* fn_8005E5B0(int id, char* out) {
    if (id >= 0) {
        sprintf(out, "#%3d", id);
    } else {
        switch (id) {
        case -10:
            strcpy(out, "#PCE");
            break;
        case -20:
            strcpy(out, "#GST");
            break;
        case -30:
            strcpy(out, "#WRK");
            break;
        default:
            strcpy(out, "#---");
            break;
        }
    }
    return out;
}

// Shuts the AI down: frees every slot's AI object and the AI subsystems.
// @target 8005D420
void fn_8005D420(void) {
    lbl_80276A24 = 0;
    fn_8005CFE0();
    for (int i = 0; i < 48; i++) {
        if (lbl_80276E38[i]) {
            AIObject* obj = lbl_80276E38[i];
            lbl_80251C04--;
            fn_80062004(obj, 2);
            fn_801A3830(obj);
            lbl_80276E38[i] = 0;
        }
    }
    lbl_80276A20 = 0;
    fn_80069634();
    fn_80064C70();
    fn_80069F40();
    fn_8007078C();
    fn_8005B884((ValueTable*)lbl_80276A34);
}

// Interpolates a tuning value between two skill tables (t = 0..1).
// @target 8005BF64
float fn_8005BF64(ValueTable* from, ValueTable* to, float t, const char* name, float def) {
    if (from && to) {
        float a = from->GetFloatOr(name, def);
        float b = to->GetFloatOr(name, def);
        return a + (b - a) * t;
    }
    fn_801A1F68("AI: Warning: missing skill tables, default %s is %+5.2f", name, def);
    return def;
}

static inline TrackSub* fn_trackSub(TrackProbe* probe) { return &probe->track->sub; }

// Sets lbl_80276A28 to whether the AI is far enough ahead (exact meaning unknown).
// NOT MATCHING yet: 2 instructions differ. The original sets the constructor's
// arguments in the order r4 (0), then r3 (&probe); this version does r3 first.
// @target 8005BE50
void fn_8005BE50(void) {
    TrackProbe probe;
    lbl_80276A28 = 1;
    fn_800620D8(&probe, 0);
    float x = fn_8005E8D0(fn_8005E7F8());
    x += (fn_80070B54() + 5.334f) * 2.0f;
    TrackSub* sub = fn_trackSub(&probe);
    if (sub->enabled) {
        ProbeTarget* target = fn_800633F0(&probe, sub->id);
        if (target) {
            lbl_80276A28 = x > target->dist - fn_8005E4C0() * 2.0f;
        }
    }
    fn_800621F4(&probe, 2);
}

// Formats a message and passes it on (printf-style).
// @target 8005D7D8
void fn_8005D7D8(int a, int b, int c, const char* fmt, ...) {
    char buf[256];
    va_list args;
    va_start(args, fmt);
    vsprintf(buf, fmt, args);
    fn_80129AE0(a, b, buf, c);
}

// Per-frame AI update.
// @target 8005E0D0
void fn_8005E0D0(void) {
    for (int i = 0; i < lbl_80251BF4; i++) {
        AIObject* obj = lbl_80276E38[i];
        if (obj) {
            if (obj->ready) {
                fn_80064108(lbl_80251C10, obj->track);
            } else {
                fn_8006416C(lbl_80251C10, obj->track);
            }
            obj->ready = 0;
        }
    }
    fn_80064538(lbl_80251C10);
    fn_8005DB78();
    fn_800707FC();
    fn_80069738();
    if ((++lbl_80276A38 & 7) == 0) {
        fn_8005D034();  // every 8th frame
    }
    fn_8006A038();
    fn_8006AFD4();
}

// Pit-side tuning value for a skill level; level 2 uses "pit_side_2" when present.
// @target 8005E1D4
float fn_8005E1D4(int level) {
    if (level == 0) {
        level = 1;
    }
    const char* hard = "pit_side_2";
    const char* name = "pit_side";
    if (level == 2 && lbl_80276A20 && lbl_80276A20->Has(hard)) {
        name = hard;
    }
    // Same lookup as getTuningFloat, but written out: the original loads the default
    // only on the fallback path instead of keeping it in a register.
    if (lbl_80276A20 && lbl_80276A20->Has(name)) {
        return lbl_80276A20->GetFloat(name);
    }
    return 1.0f;
}

// Settings for the range containing t, or the defaults.
// @target 8005E6C4
RangeData* fn_8005E6C4(float t) {
    int found = 0;
    bool busy = fn_80039624();
    if (!busy) {
        bool ok = fn_80039724(t);
        if (ok) {
            found = 1;
        }
    }
    if (found) {
        for (ListNode* node = lbl_80276F28; node; node = node->next) {
            bool inRange = false;
            if (!(t < node->min)) {
                inRange = t <= node->max;  // computed as a value, like the original
            }
            if (inRange) {
                return &node->data;
            }
        }
    }
    return &lbl_80276F2C;
}

// Smallest and largest of an array's first (up to 128) values; 0 for an empty array.
// NOT MATCHING yet: right size and shape; floating-point register choices differ in the
// min/max updates (the original updates v in place for the max).
// @target 8005B970
void fn_8005B970(FloatRange* out, FloatArray* arr) {
    if (fn_rangeCount(arr) != 0) {
        float first = *fn_801E9BB8(arr, 0);
        out->min = out->max = first;
        for (int i = 0; i < fn_rangeCount(arr); i++) {
            float v = *fn_801E9BB8(arr, i);
            out->min = v <= out->min ? v : out->min;
            if (!(v >= out->max)) {
                v = out->max;
            }
            out->max = v;
        }
    } else {
        out->min = out->max = 0.0f;
    }
}

// Checks that cskill.val has a "<skill>_<track>" entry for every track and skill level.
// @target 8005BBF4
void fn_8005BBF4(void) {
    ValueTable* table = fn_8005B3DC("cskill.val");
    int numTracks = fn_80017100();
    for (int i = 0; i < numTracks; i++) {
        const char* track = fn_8001710C(i)->name;
        for (int level = 0; level <= 2; level++) {
            char entry[64];
            sprintf(entry, "%s_%s", fn_8005BBBC(level), track);
            if (!table->HasEntry(entry)) {
                fn_801A2028("ai: cskill.val does not contain entry %s", entry);
            }
        }
    }
    fn_8005B884(table);
}

}  // extern "C"
