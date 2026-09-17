#include <tonc.h>
#include "audio.h"
extern const unsigned char audio_data[];
static const struct {unsigned offset,samples,frames;} clips[AUDIO_COUNT]={
#include "assets/audio/sounds.inc"
};
static volatile int enabled=1,effect=-1,loop=-1,effect_frames,loop_frames,hit_cooldown;
static unsigned hit_variant;
static const unsigned short routing=SDS_AL|SDS_AR|SDS_ATMR1|SDS_BL|SDS_BR|SDS_BTMR1;
static int priority(int id) {return id==AUDIO_GOAL?5:id<=AUDIO_HIT3?3:id==AUDIO_JUMP?2:1;}
static void start(int channel,int id) {
    const unsigned char *data=audio_data+clips[id].offset;
    if(channel==0) {
        REG_DMA1CNT=0;REG_SNDDSCNT=routing|SDS_ARESET;
        REG_DMA1SAD=(u32)data;REG_DMA1DAD=(u32)&REG_FIFO_A;
        REG_DMA1CNT=DMA_ENABLE|DMA_REPEAT|DMA_32|DMA_DST_FIXED|DMA_AT_FIFO;
        effect_frames=clips[id].frames;
    } else {
        REG_DMA2CNT=0;REG_SNDDSCNT=routing|SDS_BRESET;
        REG_DMA2SAD=(u32)data;REG_DMA2DAD=(u32)&REG_FIFO_B;
        REG_DMA2CNT=DMA_ENABLE|DMA_REPEAT|DMA_32|DMA_DST_FIXED|DMA_AT_FIFO;
        loop_frames=clips[id].frames;
    }
}
void audio_init(void) {
    REG_SNDSTAT=SSTAT_ENABLE;REG_SNDDMGCNT=0;
    REG_SNDDSCNT=routing|SDS_ARESET|SDS_BRESET;
    REG_TM1CNT=0;REG_TM1D=65536-2048;REG_TM1CNT=TM_ENABLE;
    REG_DMA1CNT=REG_DMA2CNT=0;
    effect=loop=-1;effect_frames=loop_frames=hit_cooldown=0;enabled=1;
}
void audio_vblank(void) {
    if(hit_cooldown>0)--hit_cooldown;
    if(effect>=0 && --effect_frames<=0) {
        REG_DMA1CNT=0;REG_SNDDSCNT=routing|SDS_ARESET;effect=-1;
    }
    if(loop>=0 && --loop_frames<=0)start(1,loop);
}
void audio_play(int sound) {
    if(sound<0 || sound>=AUDIO_COUNT)return;
    unsigned short ime=REG_IME;REG_IME=0;
    if(enabled && (effect<0 || (sound!=effect && priority(sound)>priority(effect)))) {effect=sound;start(0,sound);}
    REG_IME=ime;
}
void audio_impact(int strength) {
    if(strength<128 || hit_cooldown)return;
    hit_cooldown=6;audio_play(AUDIO_HIT+(hit_variant++%3));
}
void audio_loop(int sound) {
    if(sound>=AUDIO_COUNT)sound=-1;
    unsigned short ime=REG_IME;REG_IME=0;
    if(!enabled)sound=-1;
    if(sound!=loop) {
        REG_DMA2CNT=0;REG_SNDDSCNT=routing|SDS_BRESET;
        loop=sound;if(sound>=0)start(1,sound);
    }
    REG_IME=ime;
}
void audio_set_enabled(int on) {
    unsigned short ime=REG_IME;REG_IME=0;enabled=!!on;
    if(!enabled) {
        REG_DMA1CNT=REG_DMA2CNT=0;effect=loop=-1;
        REG_SNDDSCNT=routing|SDS_ARESET|SDS_BRESET;
    }
    REG_IME=ime;
}
int audio_enabled(void){return enabled;}
