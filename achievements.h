#ifndef ACHIEVEMENTS_H
#define ACHIEVEMENTS_H
#include <stdint.h>
enum { ACH_GOAL, ACH_TEN_GOALS, ACH_WIN, ACH_HOCKEY, ACH_WALL, ACH_TUTORIAL,
    ACH_GOALS_25, ACH_GOALS_50, ACH_GOALS_100,
    ACH_WINS_5, ACH_WINS_10, ACH_WINS_25,
    ACH_HOCKEY_10, ACH_HOCKEY_25,
    ACH_WALL_15, ACH_WALL_30, ACH_WALL_60,
    ACH_MATCH, ACH_MATCHES_10, ACH_MATCHES_50,
    ACH_SOCCER_WIN, ACH_HOCKEY_WIN, ACH_LINK_WIN, ACH_SHUTOUT, ACH_COUNT };
extern const char *const achievement_names[ACH_COUNT];
extern const char *const achievement_descriptions[ACH_COUNT];
extern const uint16_t achievement_targets[ACH_COUNT];
extern uint16_t achievement_progress[ACH_COUNT];
void achievements_init(volatile unsigned char *storage);
void achievement_add(int id, unsigned amount);
int achievement_next_unlock(void);
#endif
