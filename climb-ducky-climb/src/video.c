#include "game.h"
#include "assets.h"
#include <string.h>
typedef struct {
    uint8_t bank;
    uint16_t tiles;
    uint8_t rows;
    const uint8_t *data, *map, *attr;
    const uint16_t *pal;
} Scene;
static const Scene scenes[] = SCENE_TABLE;
static const uint16_t obj_pals[] = {
    RGB(2, 5, 7), RGB(2, 5, 7),  RGB(30, 29, 22), RGB(31, 20, 6),  /* duck */
    RGB(2, 5, 7), RGB(30, 8, 5), RGB(29, 16, 9),  RGB(31, 28, 20), /* scarf */
    RGB(2, 5, 7), RGB(2, 6, 8),  RGB(9, 16, 17),  RGB(29, 29, 23), /* stone */
    RGB(2, 5, 7), RGB(2, 8, 13), RGB(10, 23, 27), RGB(26, 31, 31), /* ice */
    RGB(2, 5, 7), RGB(8, 5, 7),  RGB(22, 12, 9),  RGB(31, 24, 15), /* shale */
    RGB(2, 5, 7), RGB(3, 9, 12), RGB(12, 21, 18), RGB(29, 29, 15), /* glider */
    RGB(2, 5, 7), RGB(5, 7, 9),  RGB(20, 12, 7),  RGB(31, 20, 8),  /* camp */
    RGB(2, 5, 7), RGB(5, 9, 13), RGB(16, 24, 24), RGB(31, 31, 27)};
static uint8_t oam, loaded = NONE;
static uint32_t last_status = UINT32_MAX;
#define FONT_BASE 152u
#define DUCK_FLIP 0x20u
#define TITLE_DUCK_TILE 232u
#define TITLE_DUCK_TILE_COUNT 24u
static uint8_t char_tile(char c) {
    if (c >= 'A' && c <= 'Z')
        return 1 + c - 'A';
    if (c >= '0' && c <= '9')
        return 27 + c - '0';
    switch (c) {
    case '+':
        return 37;
    case '-':
        return 38;
    case '.':
        return 39;
    case '/':
        return 40;
    case '>':
        return 41;
    case '!':
        return 42;
    case ':':
        return 43;
    default:
        return 0;
    }
}
static void row_text(uint8_t *dst, const char *s, uint8_t max, uint8_t amber) {
    while (*s && max--)
        *dst++ = FONT_BASE + (amber ? FONT_COUNT : 0u) + char_tile(*s++);
}
static void win_row(uint8_t y, const char *s, uint8_t amber) {
    uint8_t row[20];
    memset(row, FONT_BASE, 20);
    row_text(row, s, 20, amber);
    set_win_tiles(0, y, 20, 1, row);
}
static void menu_action(uint8_t y, const char *button, const char *action) {
    uint8_t row[20];
    memset(row, FONT_BASE, sizeof(row));
    row_text(row + 1, button, 6, 1);
    row_text(row + 8, action, 12, 0);
    set_win_tiles(0, y, 20, 1, row);
}
static uint8_t sky_step = NONE;
static void window_attrs(uint8_t rows) {
    uint8_t attrs[20], i;
    memset(attrs, 0x87, 20);
    VBK_REG = 1;
    for (i = 0; i < rows; i++)
        set_win_tiles(0, i, 20, 1, attrs);
    VBK_REG = 0;
}
static void draw_title_duck(void);

void activate_scene(uint8_t n) {
    if (loaded == n)
        return;
    const Scene *scene = &scenes[n];
    const uint8_t map_row = n == SCENE_MOUNTAIN ? 2 : 0;
    DISPLAY_OFF;
    HIDE_SPRITES;
    HIDE_WIN;
    LCDC_REG = (LCDC_REG & (uint8_t)~LCDCF_BG9C00) | LCDCF_BG8000 | LCDCF_WIN9C00;
    SWITCH_ROM(scene->bank);
    VBK_REG = 1;
    set_sprite_data(0, (uint8_t)scene->tiles, scene->data);
    set_bkg_tiles(0, map_row, 20, scene->rows, scene->attr);
    VBK_REG = 0;
    set_bkg_tiles(0, map_row, 20, scene->rows, scene->map);
    if (loaded == NONE) {
        SWITCH_ROM(11);
        set_sprite_data(0, SPRITE_COUNT, sprite_tiles);
        set_sprite_data(FONT_BASE, FONT_COUNT * 2, font_tiles);
        VBK_REG = 1;
        set_sprite_data(TITLE_DUCK_TILE, TITLE_DUCK_TILE_COUNT, title_duck_tiles);
        VBK_REG = 0;
        set_sprite_palette(0, 8, obj_pals);
        SPRITES_8x16;
        SWITCH_ROM(scene->bank);
    }
    set_bkg_palette(0, 8, scene->pal);
    loaded = n;
    move_bkg(0, 0);
    SHOW_BKG;
    window_attrs(18);
    if (n == SCENE_MOUNTAIN) {
        sky_step = NONE;
        last_status = UINT32_MAX;
        draw_world();
        draw_status();
        SHOW_SPRITES;
    } else {
        for (uint8_t i = 0; i < 40; ++i)
            hide_sprite(i);
        if (n == SCENE_TITLE) {
            draw_title_duck();
            SHOW_SPRITES;
        }
    }
    DISPLAY_ON;
}
static void obj(int16_t x, int16_t y, uint8_t tile, uint8_t attr) {
    if (oam >= 40 || x <= -8 || x >= 160 || y <= -16 || y >= 144)
        return;
    set_sprite_tile(oam, tile);
    set_sprite_prop(oam, attr);
    move_sprite(oam, (uint8_t)(x + 8), (uint8_t)(y + 16));
    ++oam;
}
static void draw_title_duck(void) {
    oam = 0;
    for (uint8_t row = 0; row < 2; ++row) {
        /* Lower OAM indices put the scarf in front of the body. */
        for (uint8_t column = 0; column < 2; ++column)
            obj(16 + column * 8, 82 + row * 16,
                TITLE_DUCK_TILE + 16 + row * 4 + column * 2, 0x08u | 1u);
    }
    for (uint8_t row = 0; row < 2; ++row) {
        for (uint8_t column = 0; column < 4; ++column)
            obj(8 + column * 8, 82 + row * 16,
                TITLE_DUCK_TILE + row * 8 + column * 2, 0x08u);
    }
}

static void draw_sky(void) {
    /* One cycle per 16384 elapsed frames in Timed, or 16384 meters in Hard. */
    const uint16_t clock = hard_mode ? hard_camera_height() : (uint16_t)run_frames;
    const uint16_t phase = (clock >> 2) & 4095u;
    const uint8_t step = phase >> 5;
    if (step != sky_step) {
        uint8_t previous_bank = CURRENT_BANK;
        SWITCH_ROM(12);
        set_bkg_palette(0, 8, sky_palettes + (uint16_t)step * 32u);
        SWITCH_ROM(previous_bank);
        sky_step = step;
    }
    const uint8_t moon = phase >= 3072u;
    /* Let each disc travel a full arc and pass beyond the screen edges. */
    const uint16_t distance = moon ? phase - 3072u : phase;
    const int16_t x = moon ? ((distance * 11u) >> 6) - 16
                           : ((distance * 11u) / 192u) - 16;
    const uint8_t tile = moon ? TILE_moon : TILE_sun;
    const int16_t y = 5 + ((x < 72 ? 72 - x : x - 72) >> 2);
    obj(x, y, tile, 0);
    obj(x + 8, y, tile + 2, 0);
}

void draw_world(void) {
    int16_t px = x16 >> 4, py = 120 + cam - h, sy;
    uint8_t pose, flip, left, right, i, first, last, base, pal, k;
    if (loaded != SCENE_MOUNTAIN) {
        activate_scene(SCENE_MOUNTAIN);
        return;
    }
    oam = 0;
    flip = facing ? 0u : DUCK_FLIP;
    pose = tumble ? (5u + spin)
                  : (ground == NONE ? (boost_anim ? 4u : 3u)
                                    : ((vx > 4 || vx < -4) ? 1u + ((frame >> 3) & 1u) : 0u));
    left = pose * 6u;
    right = left + 2;
    if (flip) {
        uint8_t t = left;
        left = right;
        right = t;
    }
    /* Draw the scarf first so it has priority over the body. */
    obj(px - 4, py - 16, pose * 6u + 4u, 1 | flip);
    obj(px - 8, py - 16, left, flip);
    obj(px, py - 16, right, flip);
    first = nearby > 4 ? nearby - 4 : 1;
    if (first < 1)
        first = 1;
    last = (nearby + 6 < route_limit) ? nearby + 6 : route_limit;
    for (i = first; i <= last; i++) {
        int16_t lx;
        uint8_t kind;
        sy = 120 + cam - route[i].h;
        if (sy < -15 || sy > 193)
            continue;
        lx = ledge_x(i);
        kind = route[i].kind;
        if (kind == CAMP)
            obj(lx + 3, sy - 12, TILE_flag, 6);
        if (route[i].spike) {
            uint8_t tick = (frame + route[i].phase) & 127u;
            if (tick < 65u && (tick >= 30u || (tick & 4u)))
                obj(shard_x(i) - 4, 120 + cam - shard_h(i) - 8, tick < 30 ? TILE_warn : TILE_icicle,
                    7);
        }
        if (sy >= 144)
            continue;
        base = (kind == ROCK)
                   ? TILE_rockl
                   : ((kind == ICE)
                          ? TILE_icel
                          : ((kind == FRAGILE) ? TILE_crackl
                                               : ((kind == GLIDER) ? TILE_movel : TILE_campl)));
        pal = (kind == ROCK)
                  ? 2u
                  : ((kind == ICE) ? 3u : ((kind == FRAGILE) ? 4u : ((kind == GLIDER) ? 5u : 6u)));
        if (crumble[i] && (crumble[i] <= 125u || (crumble[i] < 150u && (frame & 4u))))
            base = TILE_gonel;
        for (k = 0; k < route[i].width; k++)
            obj(lx + k * 8u, sy,
                base + (k == 0 ? 0u : (k + 1u == route[i].width ? 4u : ((k + i) & 1u ? 2u : 6u))),
                pal);
    }
    if (wind) {
        for (i = 0; i < 3; i++) {
            uint8_t gx = frame * (2u + i) + (i * 59u), gy = (i * 37u + 10u) + ((frame >> 4) & 3u);
            obj(wind < 0 ? 160 - gx : gx, gy, TILE_gust, 7 | (wind < 0 ? DUCK_FLIP : 0u));
        }
    }
    draw_sky();
    for (i = oam; i < 40; i++)
        hide_sprite(i);
    /* Let the campsite scroll away at takeoff, then keep the same mountain fixed. */
    move_bkg(0, cam < 32 && (!hard_mode || hard_height < 160u) ? 48 - cam : 16);
}
static void time_row(uint8_t row, const char *label, uint32_t seconds) {
    uint32_t minutes = seconds / 60u;
    uint8_t remainder = seconds % 60u;
    char time[12] = "00000000:00";
    uint8_t i = 8;
    do {
        time[--i] = '0' + minutes % 10u;
        minutes /= 10u;
    } while (minutes);
    if (i == 7)
        --i;
    time[9] = '0' + remainder / 10u;
    time[10] = '0' + remainder % 10u;
    menu_action(row, label, time + i);
}
static void height_row(uint8_t row, const char *label, uint32_t height) {
    char value[12];
    uint8_t i = 10;
    value[11] = '\0';
    value[10] = 'M';
    do {
        value[--i] = '0' + height % 10u;
        height /= 10u;
    } while (height);
    menu_action(row, label, value + i);
}
void draw_status(void) {
    uint32_t value = hard_mode ? hard_height : run_frames / 60u;
    if (value == last_status)
        return;
    last_status = value;
    move_win(7, 136);
    if (hard_mode)
        height_row(0, "HEIGHT", value);
    else
        time_row(0, "TIME", value);
    SHOW_WIN;
}
void panel(uint8_t kind) {
    last_status = UINT32_MAX;
    switch (kind) {
    case TITLE:
        move_win(7, 120);
        menu_action(0, "START", has_save && camp ? "CONTINUE" : "TIMED");
        menu_action(1, "SELECT", "HARD");
        if (has_save)
            menu_action(2, "B", "NEW TIMED");
        else
            menu_action(2, "A", "GUIDE");
        break;
    case WIN:
        move_win(7, 120);
        if (hard_mode) {
            height_row(0, "HEIGHT", hard_height);
            height_row(1, "BEST", hard_best);
            win_row(2, " START MENU SEL TRY", 1);
        } else {
            time_row(0, "TIME", run_frames / 60u);
            if (best_frames)
                time_row(1, "BEST", best_frames / 60u);
            else
                menu_action(1, "BEST", "--:--");
            win_row(2, "    START  TITLE", 1);
        }
        break;
    case GUIDE:
        move_win(7, 80);
        win_row(0, "", 0);
        menu_action(1, "D-PAD", "MOVE");
        menu_action(2, "A", "JUMP");
        menu_action(3, "B", "ONE AIR FLAP");
        win_row(4, hard_mode ? " STAY ABOVE SCROLL" : " HOLD SELECT  CAMP", 0);
        win_row(5, "", 0);
        menu_action(6, "B", "BACK");
        win_row(7, "", 0);
        break;
    case PAUSE:
        move_win(7, 96);
        win_row(0, "", 0);
        menu_action(1, "A", "RESUME");
        menu_action(2, "B", "GUIDE");
        menu_action(3, "SELECT", hard_mode ? "END RUN" : "RECALL CAMP");
        menu_action(4, "UP", muted ? "SOUND OFF" : "SOUND ON");
        win_row(5, "", 0);
        break;
    case CONFIRM:
        move_win(7, 112);
        win_row(0, "", 0);
        win_row(1, " REPLACE SAVED CAMP", 0);
        win_row(2, " A  YES     B  KEEP", 1);
        win_row(3, "", 0);
        break;
    }
    SHOW_WIN;
}
