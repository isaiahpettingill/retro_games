#include "game.h"
#include <string.h>
#include "course.inc"

const char * const zone_names[] = {"BASE CAMP","KHUMBU ICEFALL","WESTERN CWM","LHOTSE FACE","YELLOW BAND","SOUTH COL","SOUTH SUMMIT","SUMMIT RIDGE"};
uint8_t zone,ground,nearby,wing,tumble,settled,facing,frame,camp,grace;
uint8_t crumble[LAST+1],recall_count,boost_anim,notice,spin;
int16_t h,cam,x16;
int8_t vx,vy,wind;
uint16_t falls;
static int16_t takeoff;
static uint8_t frac,coyote,buffer,flap_queued,rag_left,spin_clock,impact,immunity,breaking;

static int8_t slide_at(uint8_t t) {
    t>>=1; t&=63u;
    if(t>31u)t=63u-t;
    return (int8_t)(t>>1)-8;
}
uint8_t ledge_x(uint8_t i) {
    if(route[i].kind!=GLIDER)return route[i].x;
    return (uint8_t)(route[i].x+slide_at(frame+route[i].phase));
}
uint8_t shard_x(uint8_t i) {
    return ledge_x(i)+((route[i].phase&1u)?4u:route[i].width*8u-5u);
}
int16_t shard_h(uint8_t i) {
    uint8_t t=(frame+route[i].phase)&127u;
    if(t<30u)return route[i].h+57; /* A flashing mark precedes the falling ice. */
    if(t<65u)return route[i].h+58-(int16_t)(t-30u)*2;
    return -1000;
}
static uint8_t stands(uint8_t i) {
    int16_t x=x16>>4, left=ledge_x(i);
    return (x+3>left && x-3<left+((uint16_t)route[i].width<<3));
}
static uint8_t solid(uint8_t i) {
    return !crumble[i] || crumble[i]>125u;
}
static void horizontal(void) {
    x16+=vx;
    if(x16<96){x16=96;vx=tumble?(-vx/2):0;}
    if(x16>2464){x16=2464;vx=tumble?(-vx/2):0;}
}
static void track(void) {
    while(nearby<LAST && h>=route[nearby+1].h)++nearby;
    while(nearby && h<route[nearby].h)--nearby;
}
void reset_at(uint8_t mark) {
    uint8_t idx=mark*SECTION;
    memset(crumble,0,sizeof(crumble));breaking=0;
    h=route[idx].h; ground=nearby=idx; zone=mark;
    x16=(mark ? route[idx].x+route[idx].width*4u : 24u)<<4;
    wing=1;facing=1;cam=(h>45)?h-45:0;
    takeoff=h;vx=vy=0;tumble=settled=frac=impact=spin=wind=buffer=0;
    recall_count=boost_anim=flap_queued=0;coyote=6;immunity=64;notice=75;
}
static void ragdoll(int8_t kick) {
    if(tumble)return;
    tumble=1;settled=0;flap_queued=0;ground=NONE;wing=0;rag_left=120;impact=0;
    spin_clock=0;spin=facing?0u:4u;vx=kick;
    if(vy>0)vy=0;
    if(falls<9999u)++falls;
    sound(3);
}
static void arrive(uint8_t i) {
    ground=i;h=route[i].h;frac=0;vy=0;wing=1;flap_queued=0;coyote=6;takeoff=h;
    if(route[i].kind==FRAGILE && !crumble[i]){crumble[i]=174;++breaking;}
    if(i==LAST){finish();return;}
    if(i && route[i].kind==CAMP && i/SECTION>camp) {
        camp=i/SECTION;commit_save();notice=100;sound(5);
    }
}
static void rag_floor(uint8_t i) {
    int8_t speed=-vy;
    h=route[i].h;frac=0;
    if(rag_left>15u && speed>14 && impact<4u) {
        vy=(speed>>1)+1;
        if(vy>30)vy=30;
        vx=(vx*3)/4;
        if(vx==0 && impact==0)vx=facing?9:-9;
        ++impact;spin_clock=0;sound(4);
    }else {
        ground=i;vy=0;settled=1;
        if(route[i].kind==FRAGILE && !crumble[i]){crumble[i]=174;++breaking;}
    }
}
static void apply_wind(void) {
    uint8_t f=frame;
    wind=0;
    if(zone<3 || (zone==4 && (nearby&3u)==0))return;
    if(zone==3 && (nearby&3u)<2)return;
    if((f&127u)<49u)wind=(f&128u)?-1:1;
    if(zone>=6 && (f&127u)<65u)wind=(f&128u)?-1:1;
}
void play_step(uint8_t held,uint8_t pressed) {
    uint8_t i,lo,hi;int8_t dir=0,limit=28;
    int16_t prev,delta;
    frame++;
    if(notice)--notice;
    if(immunity)--immunity;
    if(boost_anim)--boost_anim;
    if(breaking)for(i=1;i<=LAST;i++)if(crumble[i] && !--crumble[i])--breaking;
    if(held&J_SELECT) {
        if(recall_count<48 && ++recall_count==48) {
            reset_at(camp);recall_count=49;sound(5);return;
        }
    }else recall_count=0;
    apply_wind();
    if(ground!=NONE) {
        if(route[ground].kind==GLIDER) {
            int8_t carry=slide_at(frame+route[ground].phase)-slide_at(frame-1+route[ground].phase);
            x16+=(int16_t)carry*16;
        }
        if(!solid(ground)){
            ground=NONE;coyote=5;takeoff=h;
            if(tumble)settled=0;
        }
    }
    if(tumble) {
        if(rag_left)--rag_left;
        if(!settled || vx>4 || vx< -4) {
            if(++spin_clock >= (uint8_t)(4u+impact*2u)) {
                spin_clock=0;spin=(spin+(vx<0?7u:1u))&7u;
            }
        }
        if(ground!=NONE) {
            if((frame&1u)==0){if(vx>0)vx--;else if(vx<0)vx++;}
            if(!rag_left){tumble=settled=0;immunity=70;vx=0;arrive(ground);}
        }
    }else{
        if((held&J_LEFT) && !(held&J_RIGHT))dir=-1;
        if((held&J_RIGHT) && !(held&J_LEFT))dir=1;
        if(dir) {
            int8_t acceleration=(ground!=NONE && route[ground].kind==ICE)?2:4;
            vx+=dir*acceleration;facing=(dir>0);
        }else{
            int8_t drag=(ground!=NONE && route[ground].kind==ICE)?1:5;
            if(vx>drag)vx-=drag;else if(vx< -drag)vx+=drag;else vx=0;
        }
        if((pressed&J_A) && (ground!=NONE || coyote))buffer=7;
        if(buffer && (ground!=NONE || coyote)){
            takeoff=h;vy=65;frac=0;ground=NONE;coyote=0;buffer=0;wing=1;
            flap_queued=(pressed&J_B)!=0;sound(1);
        }else if(ground==NONE && (pressed&(J_A|J_B)) && wing){
            flap_queued=1;
        }else if((pressed&J_A) && !wing){buffer=6;}
        /* Keep an early tap until the wingbeat can add useful height. */
        if(flap_queued && ground==NONE && wing && vy<=24){
            flap_queued=0;vy=55;wing=0;boost_anim=13;sound(2);
        }
        if(buffer)--buffer;
        if(ground==NONE && wind){vx+=wind*2;limit=30;}
        if(vx>limit)vx=limit;
        if(vx< -limit)vx=-limit;
    }
    horizontal();
    if(ground!=NONE && !stands(ground)) {
        ground=NONE;takeoff=h;coyote=tumble?0:6;settled=0;
    }
    if(ground==NONE) {
        prev=h;
        if(vy> -76)vy-=3;
        delta=(int16_t)frac+vy;h+=delta>>4;frac=(uint8_t)delta&15u;
        if(coyote)--coyote;
        if(!tumble && vy<0 && h<takeoff-10)
            ragdoll(vx>6?vx:(vx< -6?vx:(facing?14:-14)));
        track();
        if(vy<=0) {
            hi=(nearby<LAST)?nearby+1:nearby;
            lo=nearby?nearby-1:0;
            for(i=hi;;--i) {
                if(route[i].h<=prev && route[i].h>=h && solid(i) && stands(i)){
                    if(tumble)rag_floor(i);else arrive(i);
                    break;
                }
                if(i==lo)break;
            }
        }
    }
    if(h<0){if(tumble)rag_floor(0);else arrive(0);}
    if(game_mode!=PLAY)return;
    track();
    if(!tumble && !immunity) {
        lo=nearby>1?nearby-2:0;hi=(nearby+2<LAST)?nearby+2:LAST;
        for(i=lo;i<=hi;i++)if(route[i].spike && ((frame+route[i].phase)&127u)>=30u){
            int16_t drop=shard_h(i),dx=(x16>>4)-shard_x(i);
            if(dx>-7 && dx<7 && drop>h && drop<h+17) {
                ragdoll(dx<0?-27:27);vy=12;break;
            }
        }
    }
    while(zone<7 && h>=camp_alt[zone+1]+5)++zone;
    while(zone && h<camp_alt[zone]-10)--zone;
    /* Keep the approach and the landing visible in both directions. */
    if(h-cam>48)cam=h-48;
    if(h-cam<34)cam=h-34;
    if(cam<0)cam=0;
}
