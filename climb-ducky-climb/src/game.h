#ifndef LITTLE_WINGS_H
#define LITTLE_WINGS_H
#include <gb/gb.h>
#include <gb/cgb.h>
#include <stdint.h>

#define LAST 112u
#define SECTION 14u
#define NONE 255u
enum { ROCK, ICE, FRAGILE, GLIDER, CAMP };
enum { TITLE, GUIDE, PLAY, PAUSE, WIN, CONFIRM };
typedef struct {
    int16_t h;
    uint8_t x, width, kind, phase, spike;
} Ledge;
extern const Ledge *route;
extern uint8_t route_limit, hard_mode, hard_tier;
extern uint32_t hard_height, hard_best;
void reset_hard(uint16_t seed);
uint16_t hard_camera_height(void);
void draw_status(void);
extern const int16_t camp_alt[];
extern const char *const zone_names[];
extern uint8_t game_mode, zone, ground, nearby, wing, tumble, settled, facing, frame, camp, muted,
    has_save;
extern uint8_t grace, crumble[LAST + 1], recall_count, boost_anim, notice, spin;
extern int16_t h, cam, x16;
extern int8_t vx, vy, wind;
extern uint16_t falls;
void play_step(uint8_t held, uint8_t pressed);
void reset_at(uint8_t mark);
void commit_save(void);
void load_save(void);
uint8_t ledge_x(uint8_t i);
int16_t shard_h(uint8_t i);
uint8_t shard_x(uint8_t i);
enum { SCENE_MOUNTAIN, SCENE_TITLE, SCENE_SUMMIT };
void activate_scene(uint8_t n);
void draw_world(void);
extern uint32_t run_frames, best_frames;
void panel(uint8_t kind);
void sound(uint8_t id);
void music_tick(void);
void audio_init(void);
void show_title(void);
void finish(void);
#endif
