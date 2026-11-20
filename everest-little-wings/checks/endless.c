/* Exercise endless generation, collision, scrolling and rebasing together. */
#include <assert.h>
#include <stdio.h>
#include "../src/physics.c"

uint8_t game_mode,muted,has_save;
void sound(uint8_t id) { (void)id; }
void commit_save(void) {}
void finish(void) { game_mode=WIN; }

int main(void) {
    for (uint16_t seed=1; seed<=64; ++seed) {
        reset_hard(seed*941u);
        game_mode=PLAY;
        uint32_t camera=0;
        for (unsigned jump=0; jump<260; ++jump) {
            unsigned source=ground;
            assert(source!=NONE);
            unsigned target=source+1;
            uint32_t goal=height_base+route[target].h;
            uint8_t boost=route[target].h-h>40;
            for (unsigned tick=0; tick<100; ++tick) {
                int center=ledge_x(target)+route[target].width*4u;
                int error=center*16-x16-2*vx;
                uint8_t direction=error>18?J_RIGHT:(error< -18?J_LEFT:0);
                uint8_t pressed=!tick?J_A:(tick==20 && boost?J_B:0);
                play_step(direction|pressed,pressed);
                assert(game_mode==PLAY);
                assert(height_base+cam>=camera);
                camera=height_base+cam;
                if (height_base+route[target].h!=goal)target-=RECYCLE;
                if (hard_height>=goal)break;
            }
            if(hard_height<goal){
                fprintf(stderr,"Seed %u jump %u at %lu, target %lu, reached %lu\n",seed,jump,(unsigned long)(height_base+h),(unsigned long)goal,(unsigned long)hard_height);
                return 1;
            }
        }
        assert(hard_tier==7 && height_base>0);
        /* Idle at the high ledge until the camera passes the player. */
        for (unsigned tick=0; tick<1000 && game_mode==PLAY; ++tick)play_step(0,0);
        assert(game_mode==WIN);
    }
    puts("Passed 16,640 generated jumps through maximum difficulty and 64 scroll losses.");
    return 0;
}
