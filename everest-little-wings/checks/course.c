/* Run the cartridge's actual movement and collision code across the course clock. */
#include <stdio.h>
#include <stdlib.h>
#include "../src/physics.c"

uint8_t game_mode,muted,has_save;
void sound(uint8_t id) { (void)id; }
void commit_save(void) {}
void finish(void) { game_mode=WIN; }

static int safe_center(unsigned ledge) {
    int width=route[ledge].width*8;
    int left=ledge_x(ledge);
    if(!ledge)return 24; /* Actual base-camp spawn. */
    if(route[ledge].spike){
        int room=width/2-4;
        int bias=room<8?room:8;
        return left+width/2+(route[ledge].phase&1?bias:-bias);
    }
    return left+width/2;
}

static void stand_on(unsigned source,unsigned clock,int offset) {
    game_mode=PLAY;
    camp=source/SECTION;
    reset_at(camp);
    frame=clock;
    h=takeoff=route[source].h;
    nearby=ground=source;
    x16=16*(safe_center(source)+offset);
    immunity=0;
    if(route[source].kind==FRAGILE){crumble[source]=174;breaking=1;}
}

/* A from rest, steering towards the safe part of the landing. Use B only for the designated high ledges.
   Require three pixels inside the target and four stable frames after arrival. */
static int jump(unsigned target,unsigned clock,int offset,unsigned wait){
    unsigned source=target-1,landed=0;
    int needs_flap=route[target].h-route[source].h>42;
    stand_on(source,clock,offset);
    for(unsigned tick=0;tick<wait;tick++){
        play_step(0,0);
        if(tumble || ground!=source)return 0;
    }
    for(unsigned tick=0;tick<64;tick++){
        int error=16*safe_center(target)-x16-2*vx;
        uint8_t steer=error>18?J_RIGHT:(error< -18?J_LEFT:0);
        uint8_t pressed=tick==0?J_A:(tick==20 && needs_flap?J_B:0);
        play_step(steer|pressed,pressed);
        if(tumble)return 0;
        if(ground==target){
            int in=(x16>>4)-ledge_x(target);
            if(!landed && (in<3 || in>route[target].width*8-4))return 0;
            if(++landed==4 || game_mode==WIN)return 1;
        }else if(ground!=NONE || landed)return 0;
    }
    return 0;
}

#define CLOCK 256
#define RESPONSE 32
#define WINDOW 5
int main(void){
    unsigned failures=0,ok=0,worst=0,max_height=0,boosts=0;
    int apex=0;
    stand_on(0,0,0);
    for(unsigned tick=0;tick<60;tick++){
        play_step(tick==0?J_A:0,tick==0?J_A:0);
        if(h>apex)apex=h;
    }
    const int offsets[]={-3,0,3};
    for(unsigned target=1;target<=LAST;target++){
        unsigned rise=route[target].h-route[target-1].h;
        boosts+=rise>(unsigned)apex;
        if(rise>max_height)max_height=rise;
        for(unsigned o=0;o<sizeof(offsets)/sizeof(offsets[0]);o++){
            int offset=offsets[o];
            uint8_t now[CLOCK];
            unsigned missing=0,successful=0,longest=0;
            for(unsigned p=0;p<CLOCK;p++){
                now[p]=jump(target,p,offset,0);
                successful+=now[p];
            }
            for(unsigned p=0;p<CLOCK;p++){
                unsigned delay;
                for(delay=0;delay<=RESPONSE;delay++){
                    unsigned n=0;
                    while(n<WINDOW && now[(p+delay+n)&255u])n++;
                    if(n==WINDOW){
                        /* Also simulate the wait on the actual source surface. */
                        for(n=0;n<WINDOW;n++)if(!jump(target,p,offset,delay+n))break;
                        if(n==WINDOW)break;
                    }
                }
                if(delay>RESPONSE)missing++;
                else if(delay>longest)longest=delay;
            }
            if(missing){
                printf("MISS ledge %u rise %u offset %d: %u/256 immediate, %u missing\n",target,rise,offset,successful,missing);
                failures+=missing;
            }
            ok+=CLOCK-missing;
            if(longest>worst)worst=longest;
        }
    }
    printf("Reachability: %u covered start conditions, %u uncovered, tallest %u px, longest verified wait %u ticks.\n",ok,failures,max_height,worst);
    printf("Normal jump apex %d px. Wingbeat required at %u ledges.\n",apex,boosts);
    return failures || boosts!=3;
}
