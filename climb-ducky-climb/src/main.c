#include "game.h"
uint8_t game_mode, muted, has_save;
static uint8_t seq, guide_from;
#define SLOT ((volatile uint8_t *)0xA000)
static uint8_t valid(volatile uint8_t *p) {
    return p[0] == 0xd7 && p[1] == 0x51 && p[3] < 8u && p[6] < 2u &&
           p[7] == (uint8_t)(0xa9 ^ p[2] ^ p[3] ^ p[4] ^ p[5] ^ p[6]);
}
/* Separate slots preserve old camp saves and keep the previous record during a write. */
#define RECORD (SLOT + 16)
#define HARD_RECORD (SLOT + 32)
uint32_t run_frames, best_frames, hard_best;
static uint16_t last_tick;
static uint8_t full_run, record_slot, hard_record_slot;
static uint32_t read_record(volatile uint8_t *p) {
    if (p[0] != 0xb4 || p[5] != (uint8_t)(0x63 ^ p[1] ^ p[2] ^ p[3] ^ p[4]))
        return 0;
    return (uint32_t)p[1] | ((uint32_t)p[2] << 8) | ((uint32_t)p[3] << 16) | ((uint32_t)p[4] << 24);
}
static void save_record(volatile uint8_t *p, uint32_t value) {
    ENABLE_RAM;
    p[0] = 0;
    for (uint8_t i = 0; i < 4; ++i)
        p[i + 1] = (uint8_t)(value >> (8 * i));
    p[5] = 0x63 ^ p[1] ^ p[2] ^ p[3] ^ p[4];
    p[0] = 0xb4;
    DISABLE_RAM;
}
void load_save(void) {
    volatile uint8_t *a = SLOT, *b = SLOT + 8, *p;
    uint8_t va, vb;
    ENABLE_RAM;
    va = valid(a);
    vb = valid(b);
    if (va || vb) {
        p = (!va || (vb && (int8_t)(b[2] - a[2]) > 0)) ? b : a;
        seq = p[2];
        camp = p[3];
        falls = (uint16_t)p[4] | ((uint16_t)p[5] << 8);
        muted = p[6];
        has_save = 1;
    }
    best_frames = read_record(RECORD);
    uint32_t second = read_record(RECORD + 8);
    if (second && (!best_frames || second < best_frames)) {
        best_frames = second;
        record_slot = 8;
    }
    hard_best = read_record(HARD_RECORD);
    second = read_record(HARD_RECORD + 8);
    if (second > hard_best) {
        hard_best = second;
        hard_record_slot = 8;
    }
    DISABLE_RAM;
}
void commit_save(void) {
    volatile uint8_t *p;
    ++seq;
    p = SLOT + ((seq & 1u) ? 8 : 0);
    ENABLE_RAM;
    p[0] = 0;
    p[1] = 0x51;
    p[2] = seq;
    p[3] = camp;
    p[4] = (uint8_t)falls;
    p[5] = falls >> 8;
    p[6] = muted;
    p[7] = 0xa9 ^ p[2] ^ p[3] ^ p[4] ^ p[5] ^ p[6];
    p[0] = 0xd7;
    DISABLE_RAM;
    has_save = 1;
}
void show_title(void) {
    game_mode = TITLE;
    activate_scene(SCENE_TITLE);
    panel(TITLE);
}
void finish(void) {
    if (hard_mode) {
        if (hard_height > hard_best) {
            hard_best = hard_height;
            save_record(HARD_RECORD + (hard_record_slot ^= 8), hard_best);
        }
        game_mode = WIN;
        HIDE_SPRITES;
        panel(WIN);
        sound(3);
        return;
    }
    if (full_run && run_frames && (!best_frames || run_frames < best_frames)) {
        best_frames = run_frames;
        save_record(RECORD + (record_slot ^= 8), best_frames);
    }
    game_mode = WIN;
    commit_save();
    activate_scene(SCENE_SUMMIT);
    HIDE_SPRITES;
    panel(WIN);
    sound(6);
}
static void enter(uint8_t fresh) {
    if (fresh) {
        camp = 0;
        falls = 0;
        commit_save();
    }
    run_frames = 0;
    full_run = camp == 0;
    game_mode = PLAY;
    reset_at(camp);
    activate_scene(SCENE_MOUNTAIN);
    draw_world();
    draw_status();
    SHOW_SPRITES;
    sound(5);
    last_tick = sys_time;
}
static void enter_hard(void) {
    reset_hard(sys_time ^ ((uint16_t)DIV_REG << 8));
    game_mode = PLAY;
    activate_scene(SCENE_MOUNTAIN);
    draw_world();
    draw_status();
    SHOW_SPRITES;
    last_tick = sys_time;
}
static void resume_play(void) {
    game_mode = PLAY;
    draw_world();
    draw_status();
    SHOW_SPRITES;
    last_tick = sys_time;
}
void main(void) {
    uint8_t last, held, pressed;
    cpu_fast();
    audio_init();
    load_save();
    show_title();
    last = joypad();
    for (;;) {
        vsync();
        uint16_t tick = sys_time;
        if (game_mode == PLAY && !hard_mode)
            run_frames += (uint16_t)(tick - last_tick);
        last_tick = tick;
        held = joypad();
        pressed = held & ~last;
        last = held;
        music_tick();
        switch (game_mode) {
        case TITLE:
            if (pressed & J_START)
                enter(!has_save);
            else if ((pressed & J_B) && has_save) {
                game_mode = CONFIRM;
                panel(game_mode);
            } else if (pressed & J_SELECT)
                enter_hard();
            else if (pressed & J_A) {
                guide_from = TITLE;
                game_mode = GUIDE;
                panel(game_mode);
            }
            break;
        case GUIDE:
            if (pressed & (J_A | J_B | J_START | J_SELECT)) {
                game_mode = guide_from;
                panel(game_mode);
            }
            break;
        case CONFIRM:
            if (pressed & J_A)
                enter(1);
            else if (pressed & (J_B | J_START)) {
                show_title();
            }
            break;
        case PLAY:
            if (pressed & J_START) {
                game_mode = PAUSE;
                panel(game_mode);
                break;
            }
            play_step(held, pressed);
            if (game_mode == PLAY) {
                draw_world();
                if (!(frame & 7u))
                    draw_status();
            }
            break;
        case PAUSE:
            if (pressed & (J_A | J_START))
                resume_play();
            else if ((pressed & J_SELECT) && hard_mode)
                finish();
            else if (pressed & J_SELECT) {
                reset_at(camp);
                recall_count = 49;
                resume_play();
                sound(5);
            } else if (pressed & J_B) {
                guide_from = PAUSE;
                game_mode = GUIDE;
                panel(game_mode);
            } else if (pressed & J_UP) {
                muted = !muted;
                NR51_REG = muted ? 0 : 0xff;
                commit_save();
                panel(game_mode);
            }
            break;
        case WIN:
            if (hard_mode && (pressed & J_SELECT))
                enter_hard();
            else if (pressed & (J_START | J_A))
                show_title();
            break;
        }
    }
}
