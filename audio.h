#ifndef AUDIO_H
#define AUDIO_H
#include "assets/audio/sounds.h"
void audio_init(void);
void audio_vblank(void);
void audio_play(int sound);
void audio_impact(int strength);
void audio_loop(int sound);
void audio_set_enabled(int enabled);
int audio_enabled(void);
#endif
