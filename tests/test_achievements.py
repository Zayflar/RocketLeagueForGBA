"""Test achievement events, duplicate prevention, and interrupted SRAM saves."""
from pathlib import Path
import subprocess,tempfile,os
root=Path(__file__).resolve().parents[1]
main=(root/'main.c').read_text()
a=main.index('        if(network_step) {\n            int local_team=')
b=main.index('        if(achievement_toast_timer>0)',a)
events=main[a:b]
source='''#include "achievements.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#define FP_SCALE 256
enum {STATE_PLAY,STATE_GOAL,STATE_GAMEOVER,STATE_TUTORIAL_COMPLETE,STATE_TRAINING,STATE_REPLAY};
typedef struct {int is_on_ground,surface_wall,surface_angle,speed;} Car;
Car player,opponent;
int dt_time_frames=1,network_step=1,link_match,side,game_state,achievement_previous_state,scoring_team,is_hockey_match,score_blue,score_orange;
int link_player_id(void){return side;}
void events(void) {
'''+events+'''}
int main(void) {
    unsigned char sram[192];memset(sram,255,sizeof(sram));achievements_init(sram);
    for(int i=0;i<ACH_COUNT;i++)assert(!achievement_progress[i]);
    achievement_previous_state=STATE_PLAY;game_state=STATE_GOAL;scoring_team=6;events();
    assert(!achievement_progress[ACH_GOAL]);
    scoring_team=3;events();assert(achievement_progress[ACH_GOAL]==1);
    assert(achievement_next_unlock()==ACH_GOAL);assert(achievement_next_unlock()==-1);
    achievement_previous_state=STATE_GOAL;events();assert(achievement_progress[ACH_TEN_GOALS]==1);
    achievement_previous_state=STATE_TRAINING;events();assert(achievement_progress[ACH_TEN_GOALS]==1);
    achievement_previous_state=STATE_PLAY;link_match=1;side=1;scoring_team=6;is_hockey_match=1;events();
    assert(achievement_progress[ACH_HOCKEY]==1 && achievement_progress[ACH_TEN_GOALS]==2);
    network_step=0;events();assert(achievement_progress[ACH_TEN_GOALS]==2);network_step=1;
    game_state=STATE_GAMEOVER;score_blue=1;score_orange=2;events();assert(achievement_progress[ACH_WIN]==1);
    game_state=STATE_TUTORIAL_COMPLETE;events();assert(achievement_progress[ACH_TUTORIAL]==1);
    game_state=STATE_PLAY;opponent=(Car){1,1,64,512};
    for(int i=0;i<180;i++){events();}
    assert(achievement_progress[ACH_WALL]==180);
    for(int i=0;i<20;i++)achievement_add(ACH_TEN_GOALS,1);
    assert(achievement_progress[ACH_GOALS_25]==22);
    assert(achievement_progress[ACH_WALL_15]==180);
    assert(achievement_progress[ACH_MATCH]==1 && achievement_progress[ACH_LINK_WIN]==1);
    assert(achievement_progress[ACH_HOCKEY_WIN]==1 && !achievement_progress[ACH_SOCCER_WIN]);
    assert(!achievement_progress[ACH_SHUTOUT]);
    /* Completed base milestones must continue feeding higher tiers. */
    achievement_add(ACH_TEN_GOALS,100);assert(achievement_progress[ACH_GOALS_100]==100);
    achievement_add(ACH_WALL,4000);assert(achievement_progress[ACH_WALL_60]==3600);
    for(int i=0;i<ACH_COUNT;i++)achievement_add(i,achievement_targets[i]);
    for(int i=0;i<ACH_COUNT;i++)assert(achievement_progress[i]==achievement_targets[i]);
    achievements_init(sram);
    for(int i=0;i<ACH_COUNT;i++)assert(achievement_progress[i]==achievement_targets[i]);
    assert(achievement_next_unlock()==-1); /* Loading never repeats notifications. */
    /* The first goal is committed to slot 0; next progress to slot 1. */
    memset(sram,0xff,sizeof(sram));achievements_init(sram);
    achievement_add(ACH_GOAL,1);achievement_add(ACH_TEN_GOALS,1);
    sram[191]=0;achievements_init(sram); /* interrupted second commit */
    assert(achievement_progress[ACH_GOAL]==1 && achievement_progress[ACH_TEN_GOALS]==0);
    sram[72]^=1;achievements_init(sram); /* checksum rejects corrupted first slot */
    for(int i=0;i<ACH_COUNT;i++)assert(!achievement_progress[i]);
    /* Legacy six-slot save migrates without dropping earned unlocks. */
    memset(sram,255,sizeof(sram));
    unsigned char old[32]={0};old[0]='A';old[1]='C';old[2]='H';old[3]='1';old[4]=7;
    old[8]=1;old[10]=6;old[16]=180;old[31]=0xa5;
    unsigned hash=2166136261u;for(int i=0;i<20;i++)hash=(hash^old[i])*16777619u;
    for(int i=0;i<4;i++)old[20+i]=hash>>(8*i);
    memcpy(sram,old,32);achievements_init(sram);
    assert(achievement_progress[ACH_GOAL]==1 && achievement_progress[ACH_TEN_GOALS]==6);
    assert(achievement_progress[ACH_GOALS_25]==6 && achievement_progress[ACH_WALL_60]==180);
    assert(achievement_next_unlock()==-1);
    memset(sram,255,64);achievements_init(sram); /* Migration committed a new save. */
    assert(achievement_progress[ACH_GOAL]==1 && achievement_progress[ACH_GOALS_100]==6);
    achievements_init(0);achievement_add(ACH_WIN,1);assert(achievement_progress[ACH_WIN]==1);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);(p/'test.c').write_text(source)
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-fsanitize=address,undefined','-I',str(root),str(p/'test.c'),str(root/'achievements.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True,env={**os.environ,"ASAN_OPTIONS":"detect_leaks=0","UBSAN_OPTIONS":"halt_on_error=1"})
print('PASS: 24 achievements and legacy-save migration, local team attribution, no replay/paused duplication, progress, unlock queue, SRAM reload and corrupt/interrupted save recovery')
