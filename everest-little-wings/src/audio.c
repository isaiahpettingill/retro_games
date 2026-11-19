#include "game.h"
/* A short pentatonic field motif, played quietly behind the movement sounds. */
static const uint16_t notes[]={1312,1458,1550,1660,1750,1800,1850,1900};
static const uint8_t score[]={0,2,4,255,3,2,0,255,1,3,5,255,4,2,1,255,0,2,4,6,5,3,2,255,1,3,4,255,2,1,0,255};
static uint8_t beat,note;
void audio_init(void){
    NR52_REG=0x80;NR50_REG=0x55;NR51_REG=0xff;
}
void sound(uint8_t id){
    static const uint16_t freq[]={0,1450,1740,1070,520,1800,1940};
    uint16_t f=freq[id];if(muted)return;
    if(id==3 || id==4){
        NR41_REG=49;NR42_REG=(id==3?0x72:0x42);NR43_REG=(id==3?0x45:0x31);NR44_REG=0xc0;
    }else{
        NR10_REG=(id==1?0x13:(id==2?0x12:0));
        NR11_REG=0x80|43;NR12_REG=0x82;NR13_REG=(uint8_t)f;NR14_REG=0xc0|(f>>8);
    }
}
void music_tick(void){
    uint8_t n;uint16_t f;
    if(muted || game_mode==PAUSE || game_mode==GUIDE || game_mode==CONFIRM)return;
    if(++beat<23)return;
    beat=0;n=score[note++&31u];if(n==255)return;
    f=notes[(n+(game_mode==PLAY?(zone>>1):0u))&7u];
    NR21_REG=0x80|28;NR22_REG=0x32;NR23_REG=(uint8_t)f;NR24_REG=0xc0|(f>>8);
}
