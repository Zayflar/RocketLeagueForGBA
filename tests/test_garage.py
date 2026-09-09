"""Exercise actual car meshes and showroom renderer on host; write preview PPMs."""
from pathlib import Path
import subprocess, tempfile, os, re
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    d=Path(tmp)
    for name in ('engine3d.h','engine3d.c','render.h','render.c','models.h','models.c','car_models.inc'):
        s=(root/name).read_text()
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
    hud=main[main.index("static void draw_hud_box"):main.index("static void draw_match_hud")]
    menus=main[main.index("static int menu_text_width"):main.index("static void draw_centered_text_line")]
    shadows=main[main.index("static void draw_car_shadow"):main.index("/* A ball needs")]
    harness='''#include "models.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
u16 pal_bg_mem[256];
u32 REG_DISPCNT, REG_BG2PA, REG_BG2PD, REG_BG2PB, REG_BG2PC, REG_BG2X, REG_BG2Y;
u32 REG_DMA3SAD,REG_DMA3DAD,REG_DMA3CNT;
static void draw_centered_text_line(const char *s,int y,u8 c) {draw_string(s,(240-strlen(s)*8)/2,y,c);}
'''+state+hud+menus+'static int is_hockey_match;\n'+shadows+garage+'''
int main(void) {
    init_3d_engine(); init_mesh_normals();
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
        }
    }
    int32_t identity[9]={4096,0,0,0,4096,0,0,0,4096};
    Mesh invalid=*car_models[0]; invalid.vertex_count=1;
    assert(draw_model_world_mat(&invalid,(Vector3){0,0,0},identity,256,3,5)==0);
    puts("PASS: 18 loadouts, complete rotations, mesh/UV validity, invalid mesh rejection");
}
'''
    (d/'test.c').write_text(harness)
    subprocess.run(['cc','-O1','-g','-fsanitize=address,undefined','-Wno-pointer-to-int-cast','-I',str(d),*[str(d/f) for f in ('test.c','engine3d.c','render.c','models.c')],'-lm','-o',str(d/'test')],check=True)
    output=Path(os.environ.get("GARAGE_PREVIEW_DIR", str(d/"previews"))); output.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(d/'test')],cwd=output,check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0','UBSAN_OPTIONS':'halt_on_error=1'})
