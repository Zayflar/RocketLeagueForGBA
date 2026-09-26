"""Run the actual tutorial setup, success checks, retries, and lesson progression."""
from pathlib import Path
import subprocess, tempfile
s=(Path(__file__).resolve().parents[1]/'main.c').read_text()
states=s[s.index('typedef enum {'):s.index('} GameState;')+len('} GameState;')]
defs=s[s.index('typedef enum {',s.index('/* --- Tutorial')):s.index('#define NUM_TRAINING_LEVELS')]
car=s[s.index('typedef struct {\n    Vector3 pos;\n    Vector3 vel;'):s.index('} Car;')+len('} Car;')]
setup=s[s.index('static void setup_tutorial_stage'):s.index('static const char *tutorial_control_hint')]
advance=s[s.index('static void complete_tutorial_stage'):s.index('static void apply_player_boost')]
a=s.index('                    const TutorialStage *stage =',s.index('case STATE_TUTORIAL:\n            case STATE_TRAINING:'))
b=s.index('                    if (completed) complete_tutorial_stage();',a)+len('                    if (completed) complete_tutorial_stage();')
checks=s[a:b]
harness='''#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <stdio.h>
typedef uint8_t u8;
typedef int32_t fixed;
typedef struct {fixed x,y,z;} Vector3;
#define FP_SCALE 256
#define FP_SHIFT 8
#define KEY_B 1
static int held_boost;
static int key_is_down(int key) {return held_boost;}
static void spawn_explosion(Vector3 p,u8 color) {}
'''+states+defs+car+'''
static Car player;
static struct {Vector3 pos,vel;} ball;
static char particles[100];
static int camera_yaw,cam_mode,chase_turn_velocity;
static void reset_steering(Car *c){c->steer_velocity=c->steer_fraction=0;}
static GameState game_state;
'''+setup+advance+'\nstatic void check_lesson(void) {\n'+checks+'\n}\n'+'''
int main(void) {
    for(int lesson=0;lesson<NUM_TUTORIAL_STAGES;lesson++) {
        current_tutorial_stage=lesson;
        setup_tutorial_stage();
        assert(game_state==STATE_TUTORIAL && !tutorial_flash_timer);
        assert(player.speed==0 && player.boost==100*256 && !player.boost_requested);
        assert(ball.vel.z==0 && cam_mode==0);
        check_lesson(); assert(tutorial_flash_timer==0);
        switch(tutorial_stages[lesson].objective) {
        case TUTORIAL_DRIVE_GATE:
            player.pos=tutorial_active_target();player.speed=3*256;tutorial_progress.accelerated=1;break;
        case TUTORIAL_STEER_GATES:
            tutorial_progress.steered=1;
            for(int gate=0;gate<NUM_STEERING_GATES-1;gate++) {
                player.pos=tutorial_active_target();check_lesson();
                assert(!tutorial_flash_timer && current_tutorial_gate==gate+1);
            }
            player.pos=tutorial_active_target();break;
        case TUTORIAL_BOOST_GATE:
            player.pos=tutorial_active_target();tutorial_progress.boosted=1;held_boost=1;break;
        case TUTORIAL_JUMP_GATE:
            tutorial_progress.jumped=1;player.is_on_ground=0;player.pos.y=10*256;break;
        case TUTORIAL_AERIAL_GATE:
            tutorial_progress.double_jumped=1;player.is_on_ground=0;player.pos.y=20*256;break;
        case TUTORIAL_AIM_SHOT:
            assert(ball.pos.z>player.pos.z && ball.pos.x==player.pos.x);
            tutorial_progress.ball_touched=1;tutorial_progress.goal_scored=1;break;
        }
        check_lesson();assert(tutorial_flash_timer==45 && current_tutorial_stage==lesson);
        advance_tutorial_stage();
        assert(game_state==(lesson==5?STATE_TUTORIAL_COMPLETE:STATE_TUTORIAL));
        assert(current_tutorial_stage==(lesson==5?5:lesson+1));
        /* Retry is a clean reset of the same lesson. */
        current_tutorial_stage=lesson;setup_tutorial_stage();
        assert(!tutorial_flash_timer && !tutorial_progress.jumped && !tutorial_progress.goal_scored);
        assert(player.pos.x==tutorial_stages[lesson].car_start_pos.x);
    }
    puts("PASS: all six lessons, visible success delay, automatic progression, retry, shot setup");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);(p/'test.c').write_text(harness)
    subprocess.run(['cc','-O1','-fsanitize=undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
