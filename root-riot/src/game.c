/* ROOT RIOT / Native NES co-op platformer. All coordinates use feet/bottom
   anchors in physics. Their screen conversion is confined to the renderer. */
#include "art.h"
#include "world.h"
typedef unsigned char u8;
typedef signed char i8;
typedef unsigned int u16;
typedef signed int i16;
#define REG(a) (*(volatile u8 *)(a))
#define CTRL REG(0x2000)
#define MASK REG(0x2001)
#define STATUS REG(0x2002)
#define ADDR REG(0x2006)
#define DATA REG(0x2007)
#define A 128
#define B 64
#define SEL 32
#define START 16
#define UP 8
#define DOWN 4
#define LEFT 2
#define RIGHT 1
#define FOES 5
#define ALLY_SHOTS 8
#define SHOTS 12
#define EMPTY 255
#define YGROUND 192
extern void present(void), blank(void), on(void), readpads(void), upload(void);
extern void __fastcall__ bank(u8);
extern u8 pads[4], edges[4], stream[68], oam[256];
extern u8 menu_bytes;
#pragma zpsym("menu_bytes")
extern u8 vram_hi, vram_lo, attr_lo, sx, nt, streaming, frame;
#pragma zpsym("vram_hi")
#pragma zpsym("vram_lo")
#pragma zpsym("attr_lo")
#pragma zpsym("sx")
#pragma zpsym("nt")
#pragma zpsym("streaming")
#pragma zpsym("frame")

static const char *const names[] = {"BIRD", "MONKEY", "PANDA", "LLAMA"};
static const char *const lands[] = {"SPROUT COUNTY",   "ONION TERRACES",    "CARROT FOUNDRY",
                                    "MIDNIGHT CANOPY", "BEET REFINERY",     "PEPPER BADLANDS",
                                    "KERNEL REACTOR",  "ORBITAL GREENHOUSE"};
static const char *const kings[] = {"RADISH REX",     "ONION ORACLE",    "CAPTAIN CARROT",
                                    "BARON BROCCOLI", "BATTLE BEET",     "SERRANO CYCLONE",
                                    "KERNEL PANIC",   "EMPEROR EGGPLANT"};
static const u8 stagebank[] = {1, 1, 2, 3, 2, 1, 2, 3};
static const u8 bossart[] = {0, 1, 0, 0, 1, 2, 2, 1};
static const u8 endhp[] = {9, 12, 14, 16, 18, 20, 22, 26};
static const u8 maxlife[] = {3, 4, 6, 3};
static const u8 menupal[32] = {0x0c, 0x11, 0x27, 0x30, 0x0c, 0x15, 0x26, 0x37, 0x0c, 0x12, 0x22,
                               0x31, 0x0c, 0x19, 0x2a, 0x38, 0x0c, 0x0f, 0x16, 0x38, 0x0c, 0x0f,
                               0x17, 0x37, 0x0c, 0x0f, 0x00, 0x30, 0x0c, 0x0f, 0x24, 0x39};
static const u8 bgpal[8][16] = {{0x31, 0x21, 0x2a, 0x30, 0x31, 0x07, 0x17, 0x29, 0x31, 0x09, 0x19,
                                 0x38, 0x31, 0x0f, 0x16, 0x30},
                                {0x32, 0x22, 0x2b, 0x30, 0x32, 0x08, 0x18, 0x39, 0x32, 0x0f, 0x2a,
                                 0x30, 0x32, 0x0f, 0x16, 0x38},
                                {0x01, 0x0c, 0x21, 0x30, 0x01, 0x00, 0x10, 0x27, 0x01, 0x07, 0x16,
                                 0x38, 0x01, 0x0f, 0x16, 0x30},
                                {0x0c, 0x01, 0x21, 0x30, 0x0c, 0x08, 0x19, 0x2a, 0x0c, 0x19, 0x2a,
                                 0x38, 0x0c, 0x0f, 0x16, 0x30},
                                {0x05, 0x0f, 0x15, 0x25, 0x05, 0x06, 0x16, 0x26, 0x05, 0x0f, 0x14,
                                 0x34, 0x05, 0x0f, 0x16, 0x38},
                                {0x26, 0x16, 0x27, 0x38, 0x26, 0x07, 0x17, 0x28, 0x26, 0x08, 0x19,
                                 0x38, 0x26, 0x0f, 0x16, 0x30},
                                {0x02, 0x0f, 0x12, 0x32, 0x02, 0x00, 0x10, 0x2c, 0x02, 0x06, 0x16,
                                 0x38, 0x02, 0x0f, 0x16, 0x30},
                                {0x0f, 0x02, 0x22, 0x32, 0x0f, 0x03, 0x13, 0x34, 0x0f, 0x09, 0x29,
                                 0x38, 0x0f, 0x0f, 0x16, 0x30}};
/* These arrays stay exported so a debugger can inspect actor state. */
u8 mode, stage, count, kind[4], hp[4], py[4], grounded[4], flight[4], safe[4], down[4], face[4],
    cool[4], swing[4], grace[4], buffered[4], frac[4];
u16 px[4], camera, arena;
i8 vy[4];
u8 boss, hits, bossmax, by, bdir, btimer, baction, bpattern, bflash, checkpoint;
u16 bx;
u8 ec[FOES], ey[FOES], edir[FOES], ehp[FOES], etime[FOES], eflash[FOES];
u16 ex[FOES];
u8 fy[SHOTS], life[SHOTS], owner[SHOTS], style[SHOTS];
u16 fx[SHOTS];
i8 dx[SHOTS], dy[SHOTS];
u8 tick, stagewon, leader, paused, reviveflash, groupwipe, spawncol;
static u8 effect_life[4], effect_y[4], effect_next;
static u16 effect_x[4];
static void burst(u16 x, u8 y) {
    u8 e = effect_next;
    effect_x[e] = x;
    effect_y[e] = y;
    effect_life[e] = 10;
    effect_next = (e + 1) & 3;
}
static u8 panbank, soundtime, scorebeat, noteindex, soundtype, range_col;
static const u8 *geo;
static const u8 *feat;
static const u8 *attr;
static const u8 *sky;
static const u8 *meta;
static u16 oldcam;
static const u8 tunes[8][8] = {{0, 4, 7, 9, 7, 4, 2, 7},  {0, 3, 7, 10, 7, 5, 3, 2},
                               {0, 0, 7, 6, 3, 5, 2, 7},  {0, 5, 7, 12, 10, 7, 3, 5},
                               {0, 3, 6, 7, 3, 10, 6, 2}, {0, 4, 9, 7, 12, 9, 7, 2},
                               {0, 7, 6, 3, 0, 10, 7, 6}, {0, 3, 7, 10, 12, 10, 6, 7}};
static const u16 pitches[] = {427, 403, 380, 359, 339, 320, 302, 285, 269, 254, 239, 226, 213,
                              201, 190, 179, 169, 160, 151, 142, 134, 127, 120, 113, 106};
static const u8 bounce[] = {0,  6,  12, 17, 22, 26, 30, 33, 36, 38, 40, 42, 43, 44, 45, 45,
                            45, 45, 44, 43, 42, 40, 38, 36, 33, 30, 26, 22, 17, 12, 6,  0};
static void sfx(u8 s) {
    soundtype = s;
    soundtime = s == 5 ? 14 : 7;
}
static void music(void) {
    u8 n, k;
    u16 p;
    if (!scorebeat) {
        scorebeat = boss == 1 ? 7 : 11;
        k = stage & 7;
        n = tunes[k][noteindex & 7];
        if ((noteindex & 15) > 7)
            n += 5;
        p = pitches[n];
        REG(0x4000) = boss == 1 ? 0x96 : 0x56;
        REG(0x4001) = 8;
        REG(0x4002) = (u8)p;
        REG(0x4003) = (u8)(p >> 8);
        if (!(noteindex & 1)) {
            p = pitches[tunes[k][(noteindex >> 2) & 7]] * 2;
            REG(0x4008) = 0x88;
            REG(0x400a) = (u8)p;
            REG(0x400b) = (u8)(p >> 8);
        }
        REG(0x400c) = (noteindex & 3) == 2 ? 0x16 : 0x13;
        REG(0x400e) = (noteindex & 3) == 2 ? 6 : 2;
        REG(0x400f) = 0;
        ++noteindex;
    } else {
        --scorebeat;
        if (scorebeat == 2) {
            REG(0x4000) = 0x30;
            REG(0x400c) = 0x30;
        }
    }
    if (soundtime) {
        --soundtime;
        REG(0x4004) = soundtype == 4 ? 0x98 : 0x57;
        REG(0x4005) = 8;
        p = soundtype == 1   ? 130 + soundtime * 14
            : soundtype == 2 ? 90 + soundtime * 8
            : soundtype == 3 ? 260 - soundtime * 14
            : soundtype == 4 ? 90 + soundtime * 28
                             : 180 + soundtime * 8;
        REG(0x4006) = (u8)p;
        REG(0x4007) = (u8)(p >> 8);
    } else
        REG(0x4004) = 0x30;
}
static void silence(void) {
    REG(0x4000) = REG(0x4004) = REG(0x400c) = 0x30;
    REG(0x4008) = 0x80;
    REG(0x400b) = 0;
}
static void addr(u16 a) {
    (void)STATUS;
    ADDR = (u8)(a >> 8);
    ADDR = (u8)a;
}
static void palette(const u8 *p, u8 n) {
    u8 i;
    addr(0x3f00);
    for (i = 0; i < n; ++i)
        DATA = p[i];
}
static void clear_nt(void) {
    u16 i;
    addr(0x2000);
    for (i = 0; i < 1024; ++i)
        DATA = 0;
}
static u8 glyph(char c) {
    if (c >= 'A' && c <= 'Z')
        return c - 'A' + 1;
    if (c >= '0' && c <= '9')
        return c - '0' + 27;
    switch (c) {
    case '-':
        return 37;
    case '/':
        return 38;
    case '!':
        return 39;
    case '+':
        return 40;
    case '.':
        return 41;
    case ':':
        return 42;
    case '>':
        return 43;
    case '<':
        return 44;
    case '?':
        return 45;
    }
    return 0;
}
static u8 font_base;
static void textat(u8 x, u8 y, const char *s) {
    addr(0x2000 + ((u16)y << 5) + x);
    while (*s)
        DATA = font_base + glyph(*s++);
}
static void center(u8 y, const char *s) {
    u8 n = 0;
    while (s[n])
        ++n;
    textat((32 - n) >> 1, y, s);
}
static void digit(u8 x, u8 y, u8 n) {
    addr(0x2000 + ((u16)y << 5) + x);
    DATA = font_base + 27 + n;
}
extern void hide(void);
extern void __fastcall__ piece(u8 x, u8 y, u8 tile, u8 pal);
extern void __fastcall__ figure(u8 x, u8 y, u8 tile, u8 pal, u8 flip);
/* Screen maps include their attribute tables. Each block is a run or a literal. */
static const u8 ui_palette[32] = {0x0c, 0x07, 0x27, 0x37, 0x0c, 0x01, 0x16, 0x37, 0x0c, 0x01, 0x11,
                                  0x31, 0x0c, 0x09, 0x19, 0x39, 0x0c, 0x06, 0x16, 0x37, 0x0c, 0x0f,
                                  0x17, 0x37, 0x0c, 0x0f, 0x10, 0x30, 0x0c, 0x0f, 0x24, 0x39};
static void menu(const u8 *map) {
    u8 n, v;
    blank();
    bank(0);
    CTRL = 0x80;
    palette(ui_palette, 32);
    hide();
    sx = nt = font_base = 0;
    addr(0x2000);
    while ((n = *map++) != 0) {
        if (n & 128) {
            n &= 127;
            v = *map++;
            while (n--)
                DATA = v;
        } else {
            while (n--)
                DATA = *map++;
        }
    }
}
static void stamp_sprite(u8 x, u8 y, u8 first, u8 width, u8 rows, u8 pal) {
    u8 r, c;
    for (r = 0; r < rows; ++r)
        for (c = 0; c < width; ++c)
            piece(x + (c << 3), y + (r << 4), first++, pal);
}
static void head(u8 x, u8 y, u8 animal) { stamp_sprite(x, y, 32 + (animal << 3), 4, 2, animal); }
/* Patch visible menus during vblank. Keep each transfer inside the DMA budget. */
static void span(u16 address, u8 length) {
    if (menu_bytes + length + 3 > sizeof(stream))
        present();
    stream[menu_bytes++] = (u8)(address >> 8);
    stream[menu_bytes++] = (u8)address;
    stream[menu_bytes++] = length;
}
static void field(u8 x, u8 y, u8 width, const char *label, u8 centered) {
    u8 n = 0, i, left;
    while (label[n])
        ++n;
    left = centered ? (width - n) >> 1 : 0;
    span(0x2000 + ((u16)y << 5) + x, width);
    for (i = 0; i < width; ++i)
        stream[menu_bytes++] = (i >= left && i < left + n) ? glyph(label[i - left]) : 0;
}
static void guide(void) {
    static const char *const move_a[] = {"A  JUMP / FLAP", "UP/DOWN  CLIMB", "A  JUMP", "A  JUMP"};
    static const char *const move_b[] = {"B  DROP POOP", "B  MELEE", "B  HEAVY PUNCH",
                                         "B  SPIT / RUN"};
    u8 animal = 0;
    menu(guide_screen);
    on();
    for (;;) {
        hide();
        head(112, 72, animal);
        field(12, 15, 8, names[animal], 1);
        field(7, 20, 18, move_a[animal], 1);
        field(7, 22, 18, move_b[animal], 1);
        do {
            present();
            music();
            readpads();
        } while (!(edges[0] & (A | B | START | SEL | LEFT | RIGHT)));
        if (edges[0] & (A | B | START | SEL))
            return;
        animal = (animal + ((edges[0] & RIGHT) ? 1 : 3)) & 3;
    }
}
static void title(void) {
    u8 i, bob;
    mode = 0;
    for (;;) {
        menu(title_screen);
        on();
        do {
            hide();
            bob = (frame >> 4) & 3;
            if (bob == 3)
                bob = 1;
            stamp_sprite(160, 64 + bob, 72, 8, 3, 0);
            for (i = 0; i < 4; ++i)
                figure(70 + i * 33, 143, i * 8 + ((frame >> 3) & 2), i, 0);
            music();
            present();
            readpads();
        } while (!(edges[0] & (START | SEL)));
        if (edges[0] & START)
            break;
        guide();
    }
    sfx(2);
}
static void roster_draw(u8 previous_count, u8 previous_kind[4], u8 previous_stage) {
    u8 i, x, y;
    const u8 *ink;
    hide();
    for (i = 0; i < 4; ++i) {
        x = 2 + (i & 1) * 14;
        y = 6 + (i >> 1) * 8;
        if (i < count)
            head((x + 1) * 8 + 4, (y + 1) * 8 + 4, kind[i]);
        else
            piece((x + 3) * 8, y * 8 + 20, 96, 2);
        if (previous_count == 0 || ((i < previous_count) != (i < count)) ||
            previous_kind[i] != kind[i])
            field(x + 7, y + 4, 6, i < count ? names[kind[i]] : (const char *)"", 0);
        previous_kind[i] = kind[i];
    }
    if (count != previous_count) {
        ink = crew_ink + ((u16)(count - 1) << 6) + 8;
        span(0x23c8, 40);
        for (i = 0; i < 40; ++i)
            stream[menu_bytes++] = ink[i];
        span(0x207a, 1);
        stream[menu_bytes++] = 27 + count;
    }
    if (previous_stage != stage) {
        span(0x232b, 1);
        stream[menu_bytes++] = 28 + stage;
    }
}
static void roster(void) {
    u8 i, j, k, dirty = 1, previous_count = 0, previous_stage = 255, previous_kind[4];
    menu(crew_screen);
    on();
    mode = 1;
    for (;;) {
        if (dirty) {
            roster_draw(previous_count, previous_kind, previous_stage);
            previous_count = count;
            previous_stage = stage;
            dirty = 0;
        }
        present();
        readpads();
        music();
        if (edges[0] & START)
            break;
        if (edges[0] & SEL) {
            count = count % 4 + 1;
            dirty = 1;
        }
        if (edges[0] & (UP | DOWN)) {
            stage = (stage + ((edges[0] & UP) ? 1 : 7)) & 7;
            dirty = 1;
        }
        for (i = 0; i < 4; ++i) {
            if (i >= count) {
                if (edges[i] & START) {
                    count = i + 1;
                    dirty = 1;
                } else
                    continue;
            }
            if (edges[i] & (LEFT | RIGHT)) {
                k = (kind[i] + ((edges[i] & RIGHT) ? 1 : 3)) & 3;
                for (j = 0; j < 4; ++j)
                    if (kind[j] == k) {
                        kind[j] = kind[i];
                        break;
                    }
                kind[i] = k;
                dirty = 1;
            }
        }
        if (dirty)
            sfx(2);
    }
}
static void interval(u8 frames) {
    u8 i;
    for (i = 0; i < frames; ++i) {
        present();
        music();
        readpads();
        if (i > 12 && (edges[0] & (A | START)))
            return;
    }
}
static void stage_card(void) {
    static const u8 skyline_row[8] = {9, 9, 10, 6, 9, 5, 10, 6};
    static const u8 tones[8][3] = {{0x11, 0x2a, 0x30}, {0x12, 0x2b, 0x37}, {0x00, 0x21, 0x27},
                                   {0x11, 0x2b, 0x31}, {0x06, 0x15, 0x26}, {0x16, 0x27, 0x38},
                                   {0x01, 0x1c, 0x3c}, {0x02, 0x22, 0x32}};
    u8 i, x, y, pal;
    const u8 *strip;
    mode = 2;
    blank();
    bank(stagebank[stage]);
    CTRL = 0x80;
    clear_nt();
    palette(ui_palette, 32);
    hide();
    sx = nt = 0;
    font_base = STAGE_FONT;
    addr(0x3f05);
    for (i = 0; i < 3; ++i)
        DATA = tones[stage][i];
    textat(3, 3, "STAGE");
    digit(9, 3, stage + 1);
    addr(0x2075);
    for (i = 0; i < 8; ++i)
        DATA = ROUTE_PIP + (i <= stage);
    center(7, lands[stage]);
    /* Crop the real stage panorama to a window in the card. */
    for (y = 0; y < 12; ++y) {
        addr(0x2000 + ((u16)(y + 9) << 5) + 2);
        for (x = 2; x < 30; ++x) {
            strip = skydata + (u16)skymaps[stage][x] * 26;
            DATA = strip[y + skyline_row[stage]];
        }
    }
    for (y = 2; y < 5; ++y) {
        addr(0x23c0 + y * 8);
        for (x = 0; x < 8; ++x)
            DATA = 0x55;
    }
    addr(0x23e8);
    for (x = 0; x < 8; ++x)
        DATA = 0x05;
    pal = (stage == 3 || stage == 7) ? 3 : (stage == 1 || stage == 4) ? 2 : stage == 2 ? 1 : 0;
    stamp_sprite(26, 170, 64 + bossart[stage] * 8, 4, 2, pal);
    textat(9, 22, "VS");
    textat(9, 24, kings[stage]);
    on();
    interval(95);
}
static void ending(void) {
    u8 i;
    menu(ending_screen);
    mode = 6;
    addr(0x3f09);
    DATA = 0x01;
    DATA = 0x21;
    DATA = 0x2a;
    for (i = 0; i < count; ++i)
        figure(120 - (count - 1) * 14 + i * 28, 167, kind[i] * 8, kind[i], 0);
    on();
    do {
        present();
        music();
        readpads();
    } while (!(edges[0] & START));
}
static void column(u8 c) {
    u8 row, left, right, t, g, f, fl, pl, low, r, idx, pos = 0;
    const u8 *at;
    const u8 *sk;
    const u8 *sr;
    range_col = c;
    if (c > arena_cols[stage] + 17)
        range_col = arena_cols[stage] + 17;
    g = geo[range_col];
    f = feat[range_col] & 15;
    fl = g >> 4;
    pl = g & 15;
    idx = (c & 15) << 1;
    sk = skydata + (u16)sky[idx] * 26;
    sr = skydata + (u16)sky[idx + 1] * 26;
    for (row = 0; row < 15; ++row) {
        t = 0;
        if (fl < 15 && row >= fl)
            t = row == fl ? 1 : ((row + c) & 3 ? 2 : 3);
        else if (row == pl)
            t = (stagebank[stage] == 2) ? 5 : 4;
        else if (f == 1 && row >= 5 && row < fl)
            t = 6;
        else if (row + 1 == fl) {
            if (f == 2)
                t = 7;
            else if (f == 3)
                t = 8;
            else if (f == 4)
                t = 9;
        }
        if (t) {
            idx = t << 2;
            left = meta[idx];
            right = meta[idx + 1];
            low = meta[idx + 2];
            r = meta[idx + 3];
        } else if (row < 13) {
            left = sk[pos];
            right = sr[pos];
            low = sk[pos + 1];
            r = sr[pos + 1];
        } else {
            left = right = low = r = 0;
        }
        stream[pos] = left;
        stream[pos + 1] = low;
        stream[pos + 30] = right;
        stream[pos + 31] = r;
        pos += 2;
    }
    at = attributes + ((u16)attr[range_col >> 1] << 3);
    for (row = 0; row < 8; ++row)
        stream[60 + row] = at[row];
    vram_hi = 0x20 + ((c & 16) >> 2);
    vram_lo = (c & 15) << 1;
    attr_lo = (c & 15) >> 1;
}
static void scrollpos(void) {
    sx = (u8)camera;
    nt = (u8)(camera >> 8) & 1;
}
static void loadscreen(void) {
    u8 i, base = (u8)(camera >> 4) & 0xfe;
    blank();
    bank(panbank);
    CTRL = 0x80;
    palette(menupal, 32);
    palette(bgpal[stage], 16);
    hide();
    for (i = 0; i < 32; ++i) {
        column(base + i);
        upload();
    }
    scrollpos();
    on();
}
static u8 abs8(u8 a, u8 b) { return a > b ? a - b : b - a; }
static u8 closex(u16 a, u16 b, u8 d) { return (a >= b ? a - b : b - a) < d; }
static u8 floorat(u8 col) { return geo[col] & 0xf0; }
static u8 groundat(u8 col) {
    u8 h = floorat(col);
    return h == 240 ? 250 : h;
}
static void resetplayer(u8 i, u16 x, u8 protect) {
    px[i] = x;
    py[i] = groundat((u8)(x >> 4));
    vy[i] = frac[i] = 0;
    grounded[i] = 1;
    grace[i] = 4;
    buffered[i] = 0;
    flight[i] = 3;
    face[i] = 1;
    hp[i] = maxlife[kind[i]];
    down[i] = 0;
    safe[i] = protect;
    cool[i] = swing[i] = 0;
}
static void newroom(void) {
    u8 i;
    u16 x;
    boss = 0;
    stagewon = paused = reviveflash = groupwipe = 0;
    camera = (u16)checkpoint << 4;
    if (camera > arena)
        camera = arena;
    x = camera + 12;
    spawncol = checkpoint;
    for (i = 0; i < count; ++i) {
        resetplayer(i, x, 75);
        x += 20;
    }
    for (i = 0; i < 4; ++i)
        effect_life[i] = 0;
    for (i = 0; i < FOES; ++i)
        ec[i] = EMPTY;
    for (i = 0; i < SHOTS; ++i)
        life[i] = 0;
    loadscreen();
    mode = 3;
}
static void damage(register u8 i) {
    if (safe[i] || down[i])
        return;
    burst(px[i], py[i] - 10);
    if (--hp[i]) {
        safe[i] = 68;
        vy[i] = -10;
        grounded[i] = 0;
        sfx(4);
    } else {
        down[i] = 90;
        sfx(5);
    }
}
static void hitfoe(u8 e, u8 power) {
    if (eflash[e] || ec[e] == EMPTY)
        return;
    burst(ex[e], ey[e] - 10);
    if (ehp[e] <= power) {
        ec[e] = EMPTY;
        sfx(3);
    } else {
        ehp[e] -= power;
        eflash[e] = 7;
        sfx(2);
    }
}
static void hitboss(u8 power) {
    if (boss != 1 || bflash)
        return;
    burst(bx, by - 18);
    if (hits <= power) {
        hits = 0;
        boss = 2;
        btimer = 75;
        sfx(5);
    } else {
        hits -= power;
        bflash = 6;
        sfx(3);
    }
}
static void projectile(u8 who, u8 type, u16 x, u8 y, i8 vx, i8 vely, u8 duration) {
    u8 i;
    /* Keep a separate pool for each side. Four players can always fire together. */
    if (who == EMPTY) {
        for (i = ALLY_SHOTS; i < SHOTS && life[i]; ++i)
            ;
        if (i == SHOTS)
            return;
    } else {
        i = who;
        if (life[i])
            i += 4;
        if (life[i])
            return;
    }
    fx[i] = x;
    fy[i] = y;
    dx[i] = vx;
    dy[i] = vely;
    owner[i] = who;
    style[i] = type;
    life[i] = duration;
}
static void attack(register u8 i) {
    u8 a = kind[i];
    i8 dir = face[i] ? 1 : -1;
    swing[i] = a == 2 ? 13 : 9;
    cool[i] = a == 2 ? 26 : a == 3 ? 16 : 19;
    sfx(2);
    if (a == 0)
        projectile(i, 0, px[i], py[i] - 5, dir, 3, 35);
    if (a == 3)
        projectile(i, 1, px[i] + dir * 6, py[i] - 10, dir * 4, 0, 43);
}
static void recall(register u8 i) {
    u8 c = (u8)((camera + 32) >> 4), j;
    for (j = 0; j < 12; ++j, ++c)
        if (floorat(c) != 240 && (feat[c] & 15) != 2) {
            resetplayer(i, ((u16)c << 4) + 8, 90);
            return;
        }
    resetplayer(i, px[leader], 90);
    py[i] = py[leader];
    grounded[i] = 0;
}
static void player(register u8 i) {
    u8 a = kind[i], p = pads[i], col, g, fl, pl, oldy, step, edge;
    u16 nx;
    i16 shift;
    i8 speed;
    if (down[i]) {
        if (--down[i] == 0)
            recall(i);
        return;
    }
    if (safe[i])
        --safe[i];
    if (cool[i])
        --cool[i];
    if (swing[i])
        --swing[i];
    col = (u8)(px[i] >> 4);
    g = geo[col];
    fl = g & 0xf0;
    pl = (g & 15) << 4;
    if (grounded[i]) {
        grace[i] = 5;
        flight[i] = 3;
    } else if (grace[i])
        --grace[i];
    if (edges[i] & A)
        buffered[i] = 5;
    else if (buffered[i])
        --buffered[i];
    speed = 2;
    if (a == 3 && ((p & B) || (tick & 1)))
        speed = 3;
    nx = px[i];
    if (p & RIGHT) {
        nx += speed;
        face[i] = 1;
    } else if (p & LEFT) {
        face[i] = 0;
        if (nx >= speed)
            nx -= speed;
        else
            nx = 0;
    }
    if (px[i] + 7 < camera) {
        recall(i);
        return;
    }
    if (nx < camera + 6)
        nx = camera + 6;
    if (nx > arena + 248)
        nx = arena + 248;
    edge = (u8)((nx + (face[i] ? 4 : -4)) >> 4);
    step = floorat(edge);
    if (nx == px[i] || step == 240 || py[i] <= step + 2 || py[i] > 230 ||
        ((px[i] >> 4) == (nx >> 4) && py[i] > fl + 2))
        px[i] = nx;
    col = (u8)(px[i] >> 4);
    g = geo[col];
    fl = g & 0xf0;
    pl = (g & 15) << 4;
    if (buffered[i] && grace[i]) {
        vy[i] = -24;
        grounded[i] = 0;
        grace[i] = buffered[i] = 0;
        sfx(1);
    } else if (a == 0 && (edges[i] & A) && flight[i]) {
        --flight[i];
        vy[i] = -18;
        grounded[i] = buffered[i] = 0;
        sfx(1);
    }
    if (!cool[i] && (p & B))
        attack(i);
    oldy = py[i];
    if (a == 1 && (feat[col] & 15) == 1 && (p & (UP | DOWN)) && py[i] >= 80 && py[i] <= fl) {
        vy[i] = 0;
        grounded[i] = 0;
        grace[i] = 5;
        frac[i] = 0;
        if (p & UP) {
            if (py[i] > 80)
                py[i] -= 2;
        } else if (py[i] + 2 <= fl)
            py[i] += 2;
        return;
    }
    if (vy[i] < 22)
        ++vy[i];
    shift = (i16)frac[i] + vy[i];
    frac[i] = (u8)shift & 3;
    shift = oldy + (shift >> 2);
    if (shift < 20) {
        shift = 20;
        vy[i] = 0;
    }
    py[i] = (u8)shift;
    grounded[i] = 0;
    if (vy[i] >= 0) {
        if (pl < 240 && oldy <= pl && py[i] >= pl) {
            py[i] = pl;
            grounded[i] = 1;
        } else if (fl < 240 && oldy <= fl && py[i] >= fl) {
            py[i] = fl;
            grounded[i] = 1;
        }
        if (grounded[i]) {
            vy[i] = frac[i] = 0;
            if ((feat[col] & 15) == 2 && py[i] == fl)
                damage(i);
        }
    }
    if (py[i] >= 235) {
        hp[i] = 0;
        down[i] = 65;
        sfx(4);
    }
}
static void spawn(u8 c) {
    u8 e, k = feat[c] >> 4;
    if (!k)
        return;
    for (e = 0; e < FOES && ec[e] != EMPTY; ++e)
        ;
    if (e == FOES)
        return;
    --k;
    ec[e] = k;
    ex[e] = ((u16)c << 4) + 8;
    ey[e] = groundat(c);
    if (ey[e] >= 235)
        ey[e] = 176;
    ehp[e] = (k == 4 || k == 7) ? 3 : (k == 3 || k == 6) ? 2 : 1;
    edir[e] = 0;
    eflash[e] = 0;
    etime[e] = (c << 1) & 63;
}
static void beginboss(void) {
    u8 e;
    boss = 1;
    bx = arena + 208;
    by = YGROUND;
    bdir = 0;
    btimer = 59;
    baction = bpattern = bflash = 0;
    hits = bossmax = endhp[stage] + (count - 1) * (4 + (stage >> 1));
    checkpoint = arena_cols[stage];
    for (e = 0; e < FOES; ++e)
        ec[e] = EMPTY;
    for (e = ALLY_SHOTS; e < SHOTS; ++e)
        life[e] = 0;
    sfx(5);
}
static void advance(void) {
    u8 i, c, target;
    u16 front = 0, newcam;
    for (i = 0; i < count; ++i)
        if (!down[i] && px[i] >= front) {
            front = px[i];
            leader = i;
        }
    if (!front) {
        if (boss != 2)
            groupwipe = 1;
        return;
    }
    oldcam = camera;
    newcam = front > 128 ? front - 128 : 0;
    if (newcam > arena)
        newcam = arena;
    if (newcam > camera) {
        if (newcam > camera + 4)
            camera += 4;
        else
            camera = newcam;
    }
    if ((camera >> 4) != (oldcam >> 4)) {
        c = (u8)(camera >> 4);
        column(c + 16);
        streaming = 1;
    }
    scrollpos();
    if (boss == 0) {
        c = (u8)(front >> 4);
        if ((feat[c] & 15) == 3 && c > checkpoint) {
            checkpoint = c;
            reviveflash = 70;
            sfx(5);
            for (i = 0; i < count; ++i) {
                if (down[i])
                    recall(i);
                hp[i] = maxlife[kind[i]];
            }
        }
        target = (u8)((camera + 250) >> 4);
        while (spawncol <= target && spawncol < arena_cols[stage]) {
            spawn(spawncol);
            ++spawncol;
        }
        if (camera == arena)
            beginboss();
    }
    for (i = 0; i < count; ++i)
        if (!down[i] && px[i] + 8 < camera)
            recall(i);
}
static void enemy_step(register u8 e) {
    u8 k = ec[e], t, walk = 0, g, h, dir;
    u16 nx;
    i8 speed;
    if (k == EMPTY)
        return;
    if (ex[e] + 22 < camera) {
        ec[e] = EMPTY;
        return;
    }
    if (ex[e] > camera + 253)
        return;
    if (eflash[e])
        --eflash[e];
    t = ++etime[e];
    dir = edir[e];
    speed = 1;
    switch (k) {
    case 0:
        walk = t & 1;
        break;
    case 1:
        walk = 1;
        break;
    case 2:
        if ((t & 63) == 40)
            edir[e] = dir = (px[leader] > ex[e]);
        walk = (t & 63) >= 40;
        speed = 2;
        break;
    case 3:
        if ((t & 63) == 0) {
            projectile(EMPTY, 4, ex[e], ey[e] - 9, px[leader] > ex[e] ? 2 : -2, 0, 100);
        }
        break;
    case 4:
        walk = (t & 3) != 0;
        break;
    case 5:
        walk = 1;
        break;
    case 6:
        if ((t & 63) == 0)
            projectile(EMPTY, 5, ex[e], ey[e] - 9, px[leader] > ex[e] ? 2 : -2, -3, 85);
        walk = (t & 3) == 2;
        break;
    case 7:
        walk = (t & 3) != 0;
        if (!(t & 63))
            edir[e] = dir = (px[leader] > ex[e]);
        break;
    }
    if (walk) {
        nx = dir ? ex[e] + speed : ex[e] - speed;
        g = groundat((u8)(ex[e] >> 4));
        h = groundat((u8)(nx >> 4));
        if (nx < 8 || nx > arena + 245 || (k != 5 && (h > 225 || h + 17 < g)))
            edir[e] ^= 1;
        else
            ex[e] = nx;
    }
    g = groundat((u8)(ex[e] >> 4));
    if (g > 225)
        g = 190;
    if (k == 1 || k == 7) {
        ey[e] = g - (bounce[(t >> 1) & 31] >> (k == 1 ? 1 : 0));
    } else if (k == 5)
        ey[e] = g - 18 - (bounce[(t >> 1) & 31] >> 1);
    else
        ey[e] = g;
}
static void interactions(void) {
    register u8 i, e;
    u8 k, reach;
    u16 fist;
    for (i = 0; i < count; ++i) {
        if (down[i])
            continue;
        k = kind[i];
        reach = k == 2 ? 26 : 19;
        fist = face[i] ? px[i] + 12 : (px[i] >= 12 ? px[i] - 12 : 0);
        for (e = 0; e < FOES; ++e) {
            if (ec[e] == EMPTY || !closex(px[i], ex[e], 42))
                continue;
            if ((k == 1 || k == 2) && swing[i] && closex(fist, ex[e], reach) &&
                abs8(py[i], ey[e]) < 22) {
                hitfoe(e, k == 2 ? 3 : 2);
                continue;
            }
            if (closex(px[i], ex[e], 13)) {
                if (vy[i] > 0 && py[i] + 3 >= ey[e] - 14 && py[i] <= ey[e] - 5) {
                    hitfoe(e, 2);
                    vy[i] = -17;
                    grounded[i] = 0;
                } else if (abs8(py[i], ey[e]) < 14)
                    damage(i);
            }
        }
        if (boss != 1)
            continue;
        if ((k == 1 || k == 2) && swing[i] && closex(fist, bx, reach + 8) && abs8(py[i], by) < 33)
            hitboss(k == 2 ? 4 : 2);
        if (closex(px[i], bx, 21)) {
            if (vy[i] > 0 && py[i] + 5 >= by - 29 && py[i] <= by - 17) {
                hitboss(2);
                vy[i] = -20;
                grounded[i] = 0;
            } else if (py[i] > by - 24 && py[i] < by + 12)
                damage(i);
        }
    }
}
static void boss_move(i8 speed) {
    if (bdir) {
        bx += speed;
        if (bx >= arena + 232) {
            bx = arena + 232;
            bdir = 0;
        }
    } else {
        if (bx < arena + 24 + speed) {
            bx = arena + 24;
            bdir = 1;
        } else
            bx -= speed;
    }
}
static void volley(u8 high, u8 lob) {
    i8 v = px[leader] > bx ? 2 : -2;
    projectile(EMPTY, lob ? 5 : 4, bx, by - (high ? 28 : 9), v, lob ? -3 : 0, 120);
}
/* Each boss has a four-move script. All attacks include a recovery window.
   H=hop, D=dash, V=seed volley, L=lob, S=swoop, P=ground pound. */
static const u8 scripts[8][4] = {{0, 0, 1, 0}, {3, 0, 3, 2}, {1, 1, 0, 2}, {5, 3, 5, 0},
                                 {2, 1, 2, 3}, {4, 1, 4, 2}, {3, 2, 1, 3}, {1, 4, 5, 3}};
static void boss_step(void) {
    u8 move, elapsed, span;
    if (boss == 2) {
        if (btimer) {
            --btimer;
            if (!(btimer & 7)) {
                burst(bx - 12 + ((btimer * 3) & 31), by - 26 + (btimer & 15));
                sfx(3);
            }
        } else
            stagewon = 1;
        return;
    }
    if (boss != 1)
        return;
    if (bflash)
        --bflash;
    move = scripts[stage][bpattern & 3];
    if (baction == 0) {
        if (btimer) {
            --btimer;
            return;
        }
        baction = 1;
        btimer = stage < 3 ? 25 : 20;
        bdir = px[leader] > bx;
        return;
    }
    if (baction == 1) {
        if (--btimer)
            return;
        baction = 2;
        btimer = 0;
    }
    if (baction == 2) {
        elapsed = btimer++;
        span = move == 4 ? 64 : move == 5 ? 52 : move == 3 ? 56 : move == 2 ? 48 : 40;
        if (move == 0) {
            by = YGROUND - bounce[elapsed < 32 ? elapsed : 31];
            if (elapsed < 32)
                boss_move(2);
        } else if (move == 1) {
            if (elapsed < 32)
                boss_move(stage < 5 ? 3 : 4);
        } else if (move == 2) {
            if (elapsed == 1 || elapsed == 21 || (stage >= 6 && elapsed == 36))
                volley(elapsed == 21, 0);
        } else if (move == 3) {
            if (elapsed == 1 || elapsed == 20 || elapsed == 42)
                volley(1, 1);
        } else if (move == 4) {
            by = YGROUND - bounce[elapsed >> 1];
            boss_move(2);
            if (elapsed == 25)
                volley(0, 1);
        } else {
            if (elapsed < 20) {
                by = YGROUND - (elapsed * 3);
                boss_move(2);
            } else if (elapsed < 30)
                by = YGROUND - 57;
            else if (elapsed < 37)
                by = YGROUND - ((37 - elapsed) * 8);
            else {
                by = YGROUND;
                if (elapsed == 38) {
                    projectile(EMPTY, 4, bx, by - 7, -2, 0, 100);
                    projectile(EMPTY, 4, bx, by - 7, 2, 0, 100);
                }
            }
        }
        if (btimer >= span) {
            by = YGROUND;
            baction = 0;
            btimer = 35 - stage * 2;
            if (hits < bossmax / 2 && stage >= 3)
                btimer -= 5;
            ++bpattern;
        }
    }
}
static void shots_step(void) {
    register u8 s;
    u8 i, e;
    i16 yy;
    for (s = 0; s < SHOTS; ++s) {
        if (!life[s])
            continue;
        if (!--life[s])
            continue;
        fx[s] += dx[s];
        yy = (i16)fy[s] + dy[s];
        if (yy < 8 || yy > 233 || fx[s] < camera || fx[s] > camera + 254) {
            life[s] = 0;
            continue;
        }
        fy[s] = (u8)yy;
        if (style[s] == 5 && !(life[s] & 7) && dy[s] < 4)
            ++dy[s];
        if (owner[s] == EMPTY) {
            for (i = 0; i < count; ++i)
                if (!down[i] && closex(fx[s], px[i], 9) && abs8(fy[s], py[i] - 8) < 10) {
                    damage(i);
                    life[s] = 0;
                    break;
                }
        } else {
            for (e = 0; e < FOES; ++e)
                if (ec[e] != EMPTY && closex(fx[s], ex[e], 11) && abs8(fy[s], ey[e] - 8) < 13) {
                    hitfoe(e, style[s] == 0 ? 3 : 1);
                    life[s] = 0;
                    break;
                }
            if (life[s] && boss == 1 && closex(fx[s], bx, 19) && abs8(fy[s], by - 16) < 20) {
                hitboss(style[s] == 0 ? 3 : 2);
                life[s] = 0;
            }
        }
        if (style[s] == 0 && fy[s] > groundat((u8)(fx[s] >> 4)) + 4)
            life[s] = 0;
    }
}
static void drawplayer(register u8 i) {
    u8 a, x, y, pose = 0;
    u16 rel;
    if (down[i] || (safe[i] && ((tick & 7) == 7)))
        return;
    if (px[i] < camera + 7 || px[i] > camera + 249)
        return;
    rel = px[i] - camera;
    x = (u8)rel - 7;
    y = py[i] - 16;
    a = kind[i];
    if (swing[i])
        pose = 3;
    else if (!grounded[i])
        pose = 2;
    else if (pads[i] & (LEFT | RIGHT))
        pose = (tick >> 3) & 1;
    figure(x, y, a * 8 + pose * 2, a, !face[i]);
    if ((a == 1 || a == 2) && swing[i] && x > 12 && x < 226) {
        piece(face[i] ? x + 16 : x - 8, y + 2, 90 + (a == 2), a);
        if (a == 2)
            piece(face[i] ? x + 22 : x - 12, y + 2, 91, a);
    }
}
static void drawfoe(register u8 e) {
    u8 x, code, pal;
    u16 rel;
    if (ec[e] == EMPTY || ex[e] < camera + 7 || ex[e] > camera + 248 || (eflash[e] && (tick & 2)))
        return;
    rel = ex[e] - camera;
    x = (u8)rel - 7;
    code = 32 + ec[e] * 4 + ((etime[e] >> 3) & 2);
    pal = (ec[e] == 3 || ec[e] == 7) ? 3 : ec[e] == 1 ? 2 : ec[e] == 2 || ec[e] == 6 ? 1 : 0;
    figure(x, ey[e] - 16, code, pal, !edir[e]);
}
static void drawboss(void) {
    u8 x, y, i, art, pal;
    if (!boss)
        return;
    if ((boss == 2 && (btimer & 4)) || (bflash && (tick & 2)))
        return;
    x = (u8)(bx - camera) - 16;
    y = by - 32;
    art = 64 + bossart[stage] * 8;
    pal = (stage == 3 || stage == 7) ? 3 : (stage == 1 || stage == 4) ? 2 : stage == 2 ? 1 : 0;
    for (i = 0; i < 8; ++i) {
        piece(x + ((i & 3) << 3), y + ((i & 4) << 2), art + i, pal);
    }
    if (baction == 1)
        piece(x + 12, y - 15, 94, 0);
}
static void render(void) {
    u8 i, e, first, units, part, x;
    u16 rel;
    hide();
    for (i = 0; i < count; ++i) {
        x = 12 + (i << 5);
        piece(x, 8, 98 + i, kind[i]);
        piece(x + 8, 8, 102 + hp[i], kind[i]);
    }
    if (boss) {
        units = (u8)(((u16)hits << 6) / bossmax);
        for (i = 0; i < 8; ++i) {
            part = units > 8 ? 8 : units;
            piece(92 + (i << 3), 22, 109 + part, 0);
            units -= part;
        }
    }
    if (paused) {
        for (i = 0; i < 3; ++i)
            piece(113 + (i << 3), 87, 97, 2);
    }
    if (reviveflash) {
        --reviveflash;
        piece(229, 8, 96, 3);
    }
    first = tick & 3;
    if (first >= count)
        first -= count;
    if (first >= count)
        first = 0;
    /* Rotate priority each tick so a crowded scanline shares sprite time. */
    if (tick & 1)
        drawboss();
    if (tick & 2) {
        e = (tick >> 2) & 3;
        for (i = 0; i < FOES; ++i) {
            drawfoe(e);
            if (++e == FOES)
                e = 0;
        }
    }
    for (i = 0; i < count; ++i) {
        drawplayer(first);
        if (++first == count)
            first = 0;
    }
    if (!(tick & 1))
        drawboss();
    if (!(tick & 2)) {
        e = (tick >> 2) & 3;
        for (i = 0; i < FOES; ++i) {
            drawfoe(e);
            if (++e == FOES)
                e = 0;
        }
    }
    for (i = 0; i < SHOTS; ++i)
        if (life[i] && fx[i] >= camera + 3 && fx[i] <= camera + 250) {
            rel = fx[i] - camera;
            piece((u8)rel - 3, fy[i] - 7, 88 + style[i], owner[i] == EMPTY ? 0 : kind[owner[i]]);
        }
    for (i = 0; i < 4; ++i)
        if (effect_life[i]) {
            if (!paused)
                --effect_life[i];
            if (effect_x[i] >= camera + 7 && effect_x[i] < camera + 245)
                piece((u8)(effect_x[i] - camera) - 3, effect_y[i] - 10 + (effect_life[i] >> 1), 95,
                      1);
        }
}
static void playstage(void) {
    u8 i;
    panbank = stagebank[stage];
    sky = skymaps[stage];
    meta = metamaps[stage];
    geo = geo_list[stage];
    feat = feat_list[stage];
    attr = att_list[stage];
    arena = (u16)arena_cols[stage] << 4;
    checkpoint = 0;
    tick = scorebeat = noteindex = 0;
    newroom();
    while (!stagewon) {
        readpads();
        if (edges[0] & START) {
            paused ^= 1;
            if (paused)
                silence();
        }
        if (!paused) {
            ++tick;
            for (i = 0; i < count; ++i)
                player(i);
            advance();
            if (groupwipe) {
                newroom();
                continue;
            }
            for (i = 0; i < FOES; ++i)
                enemy_step(i);
            boss_step();
            interactions();
            shots_step();
            music();
        }
        render();
        present();
    }
}
void main(void) {
    u8 i;
    count = 1;
    stage = boss = 0;
    for (i = 0; i < 4; ++i)
        kind[i] = i;
    title();
    for (;;) {
        roster();
        for (;;) {
            boss = 0;
            stage_card();
            playstage();
            if (stage == 7)
                break;
            ++stage;
        }
        boss = 0;
        ending();
        stage = 0;
    }
}
