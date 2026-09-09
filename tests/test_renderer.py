"""Run actual clipping/texture C routines on the host with guarded buffers."""
from pathlib import Path
import subprocess
import tempfile
import os

root = Path(__file__).resolve().parents[1]
engine = (root / 'engine3d.c').read_text()
render = (root / 'render.c').read_text()
clip = engine[engine.index('#define NEAR_PLANE'):engine.index('static inline void project_clip_v')]
atlas = engine[engine.index('static void init_car_texture'):engine.index('void init_pitch_texture')]
raster = render[render.index('static inline int32_t texture_recip'):]
preamble = r'''
#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;
typedef int32_t fixed;
#define FP_SCALE 256
#define IWRAM_CODE
#define RENDER_WIDTH 240
#define RENDER_HEIGHT 160
u8 frame_buffer[240*160];
u8 car_texture[64][64];
int32_t custom_div_lut[2048];
'''
main = r'''
int main(void) {
    for (int i=1; i<2048; ++i) custom_div_lut[i]=65536/i;
    init_car_texture();
    assert(car_texture[0][5] == 14);
    assert(car_texture[0][0] == 0);
    for (int mask=0; mask<8; ++mask) {
        ClipV v[3]={{0,0,0,0,0},{4096,0,0,63,0},{0,4096,0,0,63}};
        for(int i=0;i<3;++i) v[i].z=(mask&(1<<i))?4096:0;
        ClipTri out[2];
        int n=clip_tri_near(v[0],v[1],v[2],out);
        int inside=!!(mask&1)+!!(mask&2)+!!(mask&4);
        assert(n==(inside==0?0:inside==2?2:1));
        for(int t=0;t<n;++t) {
            ClipV a=out[t].v[0],b=out[t].v[1],c=out[t].v[2];
            assert((int64_t)(b.x-a.x)*(c.y-a.y)-(int64_t)(b.y-a.y)*(c.x-a.x)>0);
            for(int j=0;j<3;++j) {
                assert(out[t].v[j].z>=NEAR_PLANE);
                assert(out[t].v[j].u>=0 && out[t].v[j].u<=63);
            }
        }
    }
    /* Distinct columns reveal lost/overflowing UV interpolation. */
    u8 tex[64][64];
    for(int y=0;y<64;++y) for(int x=0;x<64;++x) tex[y][x]=x+1;
    draw_triangle_textured_unclipped(10,10,0,0,210,10,63,0,10,110,0,63,tex,99);
    assert(frame_buffer[10*240+110]>28 && frame_buffer[10*240+110]<36);
    /* The visible prefix must be identical when the right edge is cropped. */
    u8 row[160];
    memcpy(row,frame_buffer+10*240+10,160);
    memset(frame_buffer,0,sizeof(frame_buffer));
    draw_triangle_textured_clipped(80,10,0,0,280,10,63,0,80,110,0,63,tex,99);
    assert(memcmp(row,frame_buffer+10*240+80,160)==0);
    /* Oversized projected edges must not index beyond the reciprocal table. */
    draw_triangle_textured_clipped(-100,-3000,0,0,300,20,63,0,120,3000,0,63,tex,99);
    puts("PASS: atlas, all clipping masks, UV gradients, viewport cropping, large edges");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/'renderer.c'; exe=Path(tmp)/'renderer'
    src.write_text(preamble+atlas+clip+raster+main)
    subprocess.run(['cc','-O1','-g','-fsanitize=address,undefined',str(src),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True, env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0", "UBSAN_OPTIONS": "halt_on_error=1"})
