// Translation unit 0x8005B908-0x8005EA70 (ends at a GCC static-initializer stub).
// Its strings include AI skill-table warnings ("AI: Warning: ..."), so this is
// probably part of the AI driver code. Built with ProDG:
//   ngccc -O2 -fexceptions -fvtable-thunks
//
// Functions marked `// @target ADDRESS` can be checked on their own with
//   python tools/gn2e70/prodg_probe.py src/game/tu_8005B908.cpp --versions 3.5 \n//     "--flags=-O2 -fexceptions -fvtable-thunks"

// Named-value table (virtual interface). Only the slots used here are known:
// with -fvtable-thunks, slot k of the vtable is at offset 8 + 4*k.
class ValueTable {
public:
    virtual ~ValueTable();                   // 0x08
    virtual int Has(const char* name);       // 0x0C
    virtual void v2();                       // 0x10
    virtual void v3();                       // 0x14
    virtual void v4();                       // 0x18
    virtual void v5();                       // 0x1C
    virtual void v6();                       // 0x20
    virtual float GetFloat(const char* name);  // 0x24
    virtual void v8();                       // 0x28
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
extern int lbl_80276E38[];  // 0x80276E38, right after lbl_80276A48
extern float lbl_80276A1C[];

// 0x80276F4C. Must be over 8 bytes: ProDG would otherwise have used small data.
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

extern int lbl_80251C10[];    // .data
extern float lbl_80276A08[];
extern int lbl_80276A2C[];    // limit for lbl_80276A30
extern int lbl_80276A30[];    // counter
extern char lbl_80276F2C[];

DriverState* fn_80065A74(int slot);
void fn_8006AF58(void);
void fn_800643F4(int value);
int fn_80071D70(void);
float fn_8005E7F8(void);
float fn_8005E890(void);
// Linked-list node freed by fn_8005CFE0.
struct ListNode {
    char pad[0x28];
    ListNode* next;  // 0x28
};
extern ListNode* lbl_80276F28[];
extern ValueTable* lbl_80276A20[];  // current AI tuning table, may be null
extern int lbl_80276A28[];

struct AIObject {
    char pad[0x5C];
    int ready;  // 0x5C
};

void fn_801A1F68(const char* fmt, ...);  // debug warning print (kernel.cpp)
void fn_801A3830(void* ptr);             // memory free (Mem*)
int sprintf(char* buf, const char* fmt, ...);
int fn_8002371C(void* buf, int flags, int* outA, float* outTime);
void fn_80061FC0(AIObject* obj, int arg);
void fn_8005BA48(AIObject* obj, int arg);
void fn_8005E5B0(int id, char* out);
int fn_8005E578(unsigned int slot);
float fn_80057784(int curve, float a, float b);
float fn_8005E29C(const char* name, float def);  // named tuning value with a default
CarInfo* fn_800738D8(int slot);

// @target 8005BB20
float fn_8005BB20(int x) { return (float)(x - 0x55) * 0.05f; }

// @target 8005D4CC
int fn_8005D4CC(int i) { return lbl_80276E38[i]; }

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
float fn_8005E4C0(void) { return lbl_80276A1C[0]; }

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
// Caps value at max(lo, hi).
int fn_8005B908(int lo, int hi, int value) {
    int limit = hi;
    if (limit < lo) {
        limit = lo;
    }
    return value > limit ? limit : value;
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
void fn_8005E1A4(void) { fn_800643F4(lbl_80251C10[0]); }

// @target 8005E6B8
float fn_8005E6B8(void) { return lbl_80276A08[0]; }

// @target 8005E798
char* fn_8005E798(void) { return lbl_80276F2C; }

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
    if (lbl_80276A30[0] < lbl_80276A2C[0]) {
        lbl_80276A30[0]++;
        return 1;
    }
    return 0;
}

// @target 8005E970
void fn_8005E970(void) {
    if (lbl_80276A30[0] > 0) {
        lbl_80276A30[0]--;
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
    while (lbl_80276F28[0]) {
        ListNode* node = lbl_80276F28[0];
        lbl_80276F28[0] = node->next;
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
float fn_8005E29C(const char* name, float def) {
    if (lbl_80276A20[0] && lbl_80276A20[0]->Has(name)) {
        return lbl_80276A20[0]->GetFloat(name);
    }
    return def;
}

// Named int tuning value, or def.
// @target 8005E31C
int fn_8005E31C(const char* name, int def) {
    if (lbl_80276A20[0] && lbl_80276A20[0]->Has(name)) {
        return lbl_80276A20[0]->GetInt(name);
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
int fn_8005E7B0(void) { return fn_80071D70() && lbl_80276A28[0] == 0; }

}  // extern "C"
