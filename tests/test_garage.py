"""Exercise actual car meshes and showroom renderer on host; write preview PPMs."""
from pathlib import Path
import subprocess, tempfile, os, re
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    d=Path(tmp)
    for name in ('engine3d.h','engine3d.c','render.h','render.c','models.h','models.c','car_models.inc','stadium.c','stadium.h'):
        s=(Path(os.environ['STADIUM_SOURCE']) if name=='stadium.c' and 'STADIUM_SOURCE' in os.environ else root/name).read_text()
        if name=='engine3d.c' and os.environ.get('STADIUM_PROFILE'):
            s='long profile_project, profile_lines, profile_meshes;\n'+s
            s=s.replace('int project_vertex_world(Vector3 world_pos, int *sx, int *sy) {', 'int project_vertex_world(Vector3 world_pos, int *sx, int *sy) { ++profile_project;')
            s=s.replace('void draw_world_line(Vector3 a, Vector3 b, u8 color) {', 'void draw_world_line(Vector3 a, Vector3 b, u8 color) { ++profile_lines;')
            s=s.replace('int render_mode) {\n    /* Reject unsupported', 'int render_mode) {\n    ++profile_meshes;\n    /* Reject unsupported')
        s=re.sub(r'__attribute__\(\(section\("\.iwram"\), target\("arm"\), long_call\)\)', '',s)
        (d/name).write_text(s)
    (d/'tonc.h').write_text('''#pragma once
#include <stdint.h>
#include <math.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
extern u16 pal_bg_mem[256];
extern u32 REG_DISPCNT, REG_BG2PA, REG_BG2PD, REG_BG2PB, REG_BG2PC, REG_BG2X, REG_BG2Y;
extern u32 REG_DMA3SAD,REG_DMA3DAD,REG_DMA3CNT;
#define DCNT_MODE4 0
#define DCNT_BG2 0
#define DCNT_PAGE 0
#define DMA_ENABLE 0
#define DMA_32 0
static inline int lu_sin(int a) { return lround(sin(a*6.283185307179586/65536)*4096); }
static inline int lu_cos(int a) { return lround(cos(a*6.283185307179586/65536)*4096); }
static inline void memcpy32(void *p,const void *s,int n) { u32 *q=p; const u32 *r=s; while(n--) *q++=*r++; }
static inline void memset32(void *p,u32 v,int n) { u32 *q=p; while(n--) *q++=v; }
''')
    main=(root/'main.c').read_text()
    state=main[main.index('static int garage_side'):main.index('static int pause_selection')]
    garage=main[main.index('static void draw_garage'):main.index('static void draw_menu_screen')]
    hud=main[main.index("static void draw_hud_box"):main.index("static void draw_ball_indicator")]
    menus=main[main.index("static int menu_text_width"):main.index("static void draw_centered_text_line")]
    shadows=main[main.index("static void draw_car_shadow"):main.index("static void radar_point")]
    hud_text=main[main.index('static void draw_hud_text'):main.index('static void draw_hud_box')]
    match_hud=main[main.index('static void draw_ball_indicator'):main.index('/* --- Main Application Frame logic')]
    pitch=main[main.index('static const Vector3 center_circle_pts'):main.index('/* Small floodlight')]
    radar=main[main.index('static void radar_point'):main.index('/* --- Big Minimap')]
    pitch_constants='\n'.join(line for line in main.splitlines() if line.startswith(('#define STADIUM_', '#define CAGE_', '#define GOAL_HALF_WIDTH')))
    car_code=main[main.index('typedef struct {\n    Vector3 pos;\n    Vector3 vel;'):main.index('\n\ntypedef struct {\n    Vector3 pos;\n    Vector3 vel;')]
    boost_code=main[main.index('static void apply_player_boost'):main.index('/* --- Physics Core Logic --- */')]
    particle_code=main[main.index('typedef struct {',main.index('/* --- Particles --- */')):main.index('enum {',main.index('/* --- Particles --- */'))]
    particle_spawn=main[main.index('void spawn_boost_particle'):main.index('void spawn_skid_particle')]
    constants='\n'.join(line for line in main.splitlines() if line.startswith(('#define FLIP_', '#define BOOST_ACCEL', '#define MAX_DRIVE_SPEED')))
    harness='''#include "models.h"
#include "stadium.h"
#include <stdlib.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
u16 pal_bg_mem[256];
u32 REG_DISPCNT, REG_BG2PA, REG_BG2PD, REG_BG2PB, REG_BG2PC, REG_BG2X, REG_BG2Y;
u32 REG_DMA3SAD,REG_DMA3DAD,REG_DMA3CNT;
static void draw_centered_text_line(const char *s,int y,u8 c) {draw_string(s,(240-strlen(s)*8)/2,y,c);}
static void save_preview(const char *name) {
    FILE *out=fopen(name,"wb"); assert(out);
    fprintf(out,"P6\\n240 160\\n255\\n");
    for(int i=0;i<240*160;i++) {
        unsigned c=pal_bg_mem[frame_buffer[i]];
        fputc((c&31)*255/31,out); fputc(((c>>5)&31)*255/31,out); fputc(((c>>10)&31)*255/31,out);
    }
    fclose(out);
}
'''+state+hud+menus+'static int is_hockey_match;\n'+shadows+garage+constants+'\n'+car_code+particle_code+particle_spawn+'''
static Car player,opponent;
static int enable_opponent=1;
static struct {Vector3 pos;} ball;
static int game_state, show_boost_alert;
enum {STATE_TUTORIAL=99,STATE_REPLAY,STATE_TRAINING};
static int score_blue=2,score_orange=1,match_timer=3600,cam_mode,scoring_team=3,state_timer=100;
static struct {int boosted;} tutorial_progress;
'''+pitch_constants+'\n'+pitch+radar+boost_code+hud_text+match_hud+'''
int main(void) {
    init_3d_engine(); init_dynamic_models(); init_mesh_normals();
    /* Gameplay detail levels remain valid and reduce both transforms and faces. */
    for(int model=0;model<3;model++) {
        const Mesh *levels[3]={car_models[model],car_gameplay_mesh(model,100*100),car_gameplay_mesh(model,300*300)};
        for(int level=1;level<3;level++) {
            const Mesh *mesh=levels[level];
            assert(mesh->vertex_count<levels[level-1]->vertex_count);
            assert(mesh->face_count<levels[level-1]->face_count);
            for(int f=0;f<mesh->face_count;f++) {
                Face face=mesh->faces[f];
                assert(face.v1<mesh->vertex_count && face.v2<mesh->vertex_count && face.v3<mesh->vertex_count);
                Vector3 a=mesh->vertices[face.v1],b=mesh->vertices[face.v2],c=mesh->vertices[face.v3];
                int x1=(b.x-a.x)/256,y1=(b.y-a.y)/256,z1=(b.z-a.z)/256;
                int x2=(c.x-a.x)/256,y2=(c.y-a.y)/256,z2=(c.z-a.z)/256;
                assert(y1*z2-z1*y2 || z1*x2-x1*z2 || x1*y2-y1*x2);
                for(int v=0;v<3;v++) assert(face.uv[v][0]<64 && face.uv[v][1]<64);
            }
            set_camera_lookat((Vector3){0,30*256,-90*256},(Vector3){0,10*256,0},0);
            for(int angle=0;angle<256;angle+=8) {
                clear_screen(135);
                assert(draw_model_world(mesh,(Vector3){0,0,0},angle,angle,angle,256,3,RENDER_TEXTURED)>0);
            }
        }
    }
    assert(ball_gameplay_mesh(100*100)->vertex_count==42);
    assert(ball_gameplay_mesh(300*300)->vertex_count==12);
    assert(ball_gameplay_mesh(300*300)->face_count==20);
    for(int yaw=0;yaw<256;yaw+=8) {
        set_camera((Vector3){0,0,0},yaw,0);
        assert(!world_sphere_visible((Vector3){0,0,0},256));
        Vector3 front={custom_sin_fp[yaw]*100,0,custom_cos_fp[yaw]*100};
        assert(world_sphere_visible(front,14*256));
        front.x=-front.x;front.z=-front.z;
        assert(!world_sphere_visible(front,14*256));
    }
    set_camera((Vector3){0,0,0},0,0);
    assert(world_sphere_visible((Vector3){110*256,0,100*256},14*256)); /* edge overlap */
    assert(!world_sphere_visible((Vector3){200*256,0,100*256},14*256));
    assert(!world_sphere_visible((Vector3){0,200*256,100*256},14*256));
    /* Actual thrust must follow the visible nose throughout all diagonal flips. */
    for(int yaw=0;yaw<256;yaw+=32) for(int pitch=-1;pitch<=1;pitch++) for(int roll=-1;roll<=1;roll++) {
        if(!pitch && !roll) continue;
        for(int ticks=1;ticks<=50;ticks++) {
            player=(Car){0}; player.yaw=yaw; player.flip_timer=ticks;
            player.flip_pitch_dir=pitch; player.flip_roll_dir=roll;
            player.pos=(Vector3){0,80*256,0}; player.boost=100*256; player.boost_requested=1;
            int32_t rotation[9]; build_car_rotation(&player,rotation);
            /* An orthonormal matrix preserves unit-length forward at all angles. */
            double length=sqrt((double)rotation[2]*rotation[2]+(double)rotation[5]*rotation[5]+(double)rotation[8]*rotation[8]);
            assert(fabs(length-4096)<10);
            memset(particles,0,sizeof(particles));
            apply_player_boost();
            assert(player.vel.x==FP_MUL(rotation[2]>>4,(256*1848)/1000));
            assert(player.vel.y==FP_MUL(rotation[5]>>4,(256*1848)/1000));
            assert(player.vel.z==FP_MUL(rotation[8]>>4,(256*1848)/1000));
            assert(!player.boost_requested && player.boost==100*256-310);
            for(int i=0;i<3;i++) {
                assert(particles[i].life==15);
                int dot=particles[i].vel.x*(rotation[2]>>4)+particles[i].vel.y*(rotation[5]>>4)+particles[i].vel.z*(rotation[8]>>4);
                assert(dot<0); /* Exhaust always travels away from the nose. */
            }
        }
    }
    for(int m=0;m<3;m++) {
        const Mesh *mesh=car_models[m];
        assert(mesh->vertex_count<=256 && mesh->face_count<=320);
        for(int i=0;i<mesh->face_count;i++) {
            Face f=mesh->faces[i];
            assert(f.v1<mesh->vertex_count && f.v2<mesh->vertex_count && f.v3<mesh->vertex_count);
            Vector3 a=mesh->vertices[f.v1],b=mesh->vertices[f.v2],c=mesh->vertices[f.v3];
            int x1=(b.x-a.x)/256,y1=(b.y-a.y)/256,z1=(b.z-a.z)/256;
            int x2=(c.x-a.x)/256,y2=(c.y-a.y)/256,z2=(c.z-a.z)/256;
            assert(y1*z2-z1*y2 || z1*x2-x1*z2 || x1*y2-y1*x2);
            for(int v=0;v<3;v++) assert(f.uv[v][0]<64 && f.uv[v][1]<64);
        }
        for(int side=0;side<2;side++) for(int paint=0;paint<3;paint++) {
            garage_side=side; garage_model[side]=m; garage_paint[side]=paint;
            for(int frame=0;frame<768;frame++) draw_garage();
            char path[80]; snprintf(path,sizeof(path),"garage-%d-%d-%d.ppm",m,side,paint);
            FILE *out=fopen(path,"wb"); fprintf(out,"P6\\n240 160\\n255\\n");
            for(int i=0;i<240*160;i++) {unsigned c=pal_bg_mem[frame_buffer[i]];
                fputc((c&31)*255/31,out); fputc(((c>>5)&31)*255/31,out); fputc(((c>>10)&31)*255/31,out);}
            fclose(out);
        }
    }
    /* Every orientation must leave the visible bounds center stationary. */
    for (int model=0; model<CAR_MODEL_COUNT; ++model) {
        const Mesh *mesh=car_models[model];
        Vector3 lo=mesh->vertices[0], hi=lo;
        for(int i=1;i<mesh->vertex_count;++i) {
            Vector3 v=mesh->vertices[i];
            if(v.x<lo.x) lo.x=v.x; if(v.x>hi.x) hi.x=v.x;
            if(v.y<lo.y) lo.y=v.y; if(v.y>hi.y) hi.y=v.y;
            if(v.z<lo.z) lo.z=v.z; if(v.z>hi.z) hi.z=v.z;
        }
        Vector3 center={(lo.x+hi.x)/2,(lo.y+hi.y)/2,(lo.z+hi.z)/2};
        Vector3 origin={123*256,42*256,-76*256};
        for(int yaw=0;yaw<256;yaw+=17) for(int a=0;a<256;++a) {
            int32_t base[9], rot[9];
            build_model_rotation(yaw,0,0,base);
            build_model_rotation(yaw,a,(a*3)&255,rot);
            Vector3 p=car_render_position(model,origin,yaw,rot);
            int c[3]={center.x,center.y,center.z};
            int o[3]={origin.x,origin.y,origin.z}, t[3]={p.x,p.y,p.z};
            for(int axis=0;axis<3;++axis) {
                int expected=o[axis]+((base[axis*3]*c[0]+base[axis*3+1]*c[1]+base[axis*3+2]*c[2])>>12);
                int actual=t[axis]+((rot[axis*3]*c[0]+rot[axis*3+1]*c[1]+rot[axis*3+2]*c[2])>>12);
                assert(actual==expected);
            }
            p=car_render_position(model,origin,yaw,base);
            assert(p.x==origin.x && p.y==origin.y && p.z==origin.z);
        }
    }
    /* Actual menu fill stays opaque and safely clips at screen edges. */
    clear_screen(31); draw_menu_text_box("PLAY",82,131,136);
    assert(frame_buffer[81*240+54]==8);
    draw_menu_text_box("BOTTOM",155,130,300);
    draw_menu_text_box("TOP",0,130,136);
    /* Ground footprints survive yaw, height, camera cropping and both pitches. */
    for(int ice=0;ice<2;ice++) {
        is_hockey_match=ice;
        for(int h=0;h<=160;h+=20) for(int yaw=0;yaw<256;yaw+=16) {
            clear_screen(ice?14:135);
            set_camera_lookat((Vector3){0,30*256,-80*256},(Vector3){0,0,0},0);
            draw_car_shadow((Vector3){0,h*256,0},yaw,1);
            int pixels=0;
            for(int i=0;i<240*160;i++) pixels+=frame_buffer[i]!=(ice?14:135);
            assert(pixels>0);
            for(int i=0;i<240*160;i++) assert(frame_buffer[i]!=132);
            draw_ball_ground_shadow((Vector3){0,h*256,0});
            for(int i=0;i<240*160;i++) assert(frame_buffer[i]!=132);
        }
        active_pitch_mode=ice;
        if(ice) init_hockey_pitch_texture(); else init_pitch_texture();
        set_camera_lookat((Vector3){0,35*256,-100*256},(Vector3){0,15*256,0},0);
        draw_environment_background(ice?14:128);
        if(ice) for(int i=0;i<240*160;i++) {
            assert(frame_buffer[i]!=16 && frame_buffer[i]!=48 && frame_buffer[i]!=83);
        }
        draw_stadium_crowd((Vector3){0,35*256,-100*256},336*256,504*256);
        draw_soccer_pitch((Vector3){0,35*256,-100*256});
        draw_car_shadow((Vector3){-16*256,0,0},32,0);
        draw_ball_ground_shadow((Vector3){25*256,14*256,0});
        draw_model_world(car_gameplay_mesh(0,100*100),(Vector3){-16*256,0,0},32,0,0,256,3,RENDER_TEXTURED);
        draw_model_world(&sphere_mesh,(Vector3){25*256,14*256,0},0,0,0,170,130,RENDER_FLAT);
        draw_stadium_goal(459*256,109*256,75*256,ice?28:131);
        save_preview(ice?"scene-ice.ppm":"scene-grass.ppm");
        u8 untouched[5]={frame_buffer[3*240+3],frame_buffer[3*240+86],frame_buffer[3*240+171],frame_buffer[142*240+3],frame_buffer[154*240+170]};
        player.pos=(Vector3){-16*256,0,0};player.boost=74*256;
        ball.pos=(Vector3){25*256,14*256,0};opponent.pos=(Vector3){30*256,0,190*256};
        draw_radar();draw_match_hud();
        assert(frame_buffer[3*240+3]==untouched[0] && frame_buffer[3*240+86]==untouched[1]);
        assert(frame_buffer[3*240+171]==untouched[2] && frame_buffer[142*240+3]==untouched[3]);
        assert(frame_buffer[154*240+170]==untouched[4]);
        if(!ice) save_preview("transparent-hud.ppm");
        u8 goal_corner=frame_buffer[52*240+39];draw_goal_celebration_panel();
        assert(frame_buffer[52*240+39]==goal_corner);
        if(!ice) save_preview("transparent-goal.ppm");
        if(!ice) {
            set_camera_lookat((Vector3){-90*256,55*256,270*256},(Vector3){0,35*256,459*256},0);
            draw_environment_background(128);
            draw_stadium_goal(459*256,109*256,75*256,131);
            save_preview("goal-design.ppm");
            for(int charge=0;charge<=100;charge+=25) {
                memset(frame_buffer,128,240*160);
                fast_draw_boost(charge,212,136);
                assert(frame_buffer[146*240+212]==128); /* open center outside glyph */
                assert(frame_buffer[155*240+193]==128); /* no rectangular backing */
                assert(frame_buffer[115*240+212]==(charge>=75?131:149));
                char name[32];sprintf(name,"boost-%d.ppm",charge);save_preview(name);
            }
        }
        set_camera((Vector3){0,0,0},0,0);
        int ix,iy;
        assert(!world_target_indicator((Vector3){0,0,100*256},&ix,&iy));
        assert(world_target_indicator((Vector3){200*256,0,50*256},&ix,&iy) && ix>120);
        assert(world_target_indicator((Vector3){-200*256,0,50*256},&ix,&iy) && ix<120);
        assert(world_target_indicator((Vector3){0,0,-50*256},&ix,&iy) && iy>72);
        for(int x=-600;x<=600;x+=100) for(int z=-600;z<=600;z+=100) {
            if(world_target_indicator((Vector3){x*256,80*256,z*256},&ix,&iy))
                assert(ix>=14 && ix<=226 && iy>=30 && iy<=114);
        }
    }
    is_hockey_match=active_pitch_mode=0; init_pitch_texture();
    for(int yaw=0;yaw<256;yaw+=16) {
        Vector3 camera={0,35*256,0};
        set_camera(camera,yaw,0); draw_environment_background(128);
        draw_stadium_crowd(camera,336*256,504*256);
        draw_soccer_pitch(camera);
        if(yaw==32) save_preview("stadium.ppm");
    }
    /* Crossing the near plane must clip net segments safely, even outside walls. */
    for(int x=-400;x<=400;x+=200) {
        Vector3 camera={x*256,30*256,490*256};
        set_camera(camera,64,0);
        draw_soccer_pitch(camera);
        draw_stadium_crowd(camera,336*256,504*256);
    }
    for(int frame=0;frame<10;frame++) {
        int ticks=frame*6; if(ticks>50) ticks=50;
        int angle=(ticks*256/50)&255;
        int32_t rotation[9]; build_dodge_rotation(32,1,1,angle,rotation);
        Vector3 pos={0,20*256,0};
        set_camera_lookat((Vector3){0,40*256,-100*256},(Vector3){0,25*256,0},0);
        draw_environment_background(128);
        draw_car_shadow(pos,32,0);
        draw_model_world_mat(car_gameplay_mesh(0,100*100),car_render_position(0,pos,32,rotation),rotation,256,3,RENDER_TEXTURED);
        char name[40]; snprintf(name,sizeof(name),"flip-%02d.ppm",frame); save_preview(name);
    }
    for(int detail=0;detail<2;detail++) {
        for(int model=0;model<3;model++) {
            set_camera_lookat((Vector3){0,29*256,-68*256},(Vector3){0,9*256,0},0);
            clear_screen(144);
            const Mesh *mesh=detail?car_far_models[model]:car_match_models[model];
            draw_model_world(mesh,(Vector3){0,0,0},32,0,0,256,3,RENDER_TEXTURED);
            char name[40];snprintf(name,sizeof(name),"lod-%d-%d.ppm",model,detail);save_preview(name);
        }
        set_camera_lookat((Vector3){0,10*256,-80*256},(Vector3){0,0,0},0);
        clear_screen(144);
        draw_model_world(ball_gameplay_mesh(detail?300*300:100*100),(Vector3){0,0,0},0,0,0,170,130,RENDER_FLAT);
        save_preview(detail?"ball-far.ppm":"ball-near.ppm");
    }
    int32_t identity[9]={4096,0,0,0,4096,0,0,0,4096};
    Mesh invalid=*car_models[0]; invalid.vertex_count=1;
    assert(draw_model_world_mat(&invalid,(Vector3){0,0,0},identity,256,3,5)==0);
    puts("PASS: gameplay LODs, frustum culling, 18 loadouts, complete rotations, fixed car pivots, diagonal thrust/exhaust, stadium camera sweep, mesh/UV validity, invalid mesh rejection");
}
'''
    if os.environ.get('STADIUM_PROFILE'):
        harness=harness.replace('    puts("PASS:', '''    extern long profile_project,profile_lines,profile_meshes;
    profile_project=profile_lines=profile_meshes=0;
    for(int yaw=0;yaw<256;yaw+=16) {
        Vector3 camera={0,35*256,0}; set_camera(camera,yaw,0);
        draw_stadium_crowd(camera,336*256,504*256);
        draw_soccer_pitch(camera);
    }
    printf("STADIUM / 16 VIEWS: %ld projections, %ld clipped world lines, %ld mesh draws\\n",profile_project,profile_lines,profile_meshes);
    puts("PASS:''')
    (d/'test.c').write_text(harness)
    subprocess.run(['cc','-O1','-g','-fsanitize=address,undefined','-Wno-pointer-to-int-cast','-I',str(d),*[str(d/f) for f in ('test.c','engine3d.c','render.c','models.c','stadium.c')],'-lm','-o',str(d/'test')],check=True)
    output=Path(os.environ.get("GARAGE_PREVIEW_DIR", str(d/"previews"))); output.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(d/'test')],cwd=output,check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0','UBSAN_OPTIONS':'halt_on_error=1'})
