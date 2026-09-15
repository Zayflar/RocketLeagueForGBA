#ifndef LINK_H
#define LINK_H
#include <tonc.h>
void link_open(void);
void link_close(void);
int link_player_id(void);
int link_exchange(u16 payload,u16 values[2]);
int link_step(u16 buttons,int elapsed,u16 buttons_out[2],int *elapsed_out);
#endif
