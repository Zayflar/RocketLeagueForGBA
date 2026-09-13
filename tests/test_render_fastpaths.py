"""Check optimized grass/projection paths against the original pixel equations."""
from pathlib import Path
import subprocess,tempfile,os
source=(Path(__file__).resolve().parents[1]/'engine3d.c').read_text()
helpers=source[source.index('static void draw_grass_span'):source.index('/* --- Buffer Management --- */')]
harness='''#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;typedef uint32_t u32;typedef int32_t fixed;
#define RENDER_SCALE 1
#define IWRAM_CODE
static int fills;
static void fast_span_fill(u8 *dst,u32 color,int count) {++fills;memset(dst,color&255,count);}
'''+helpers+'''
int main(void) {
    u8 colors[4]={135,142,130,108},buffer[242];
    int cases=0;
    for(int z=-117504;z<=117504;z+=257) for(int step=-1600;step<=1600;step+=64) {
        int count=240;
        while(count>0 && (z+(count-1)*step < -117504 || z+(count-1)*step>117504)) count--;
        memset(buffer,222,sizeof(buffer));
        draw_grass_span(buffer+1,count,z,step,colors);
        assert(buffer[0]==222 && buffer[count+1]==222);
        for(int i=0;i<count;i++) {
            int sample=z+i*step;
            int row=((sample<0?-sample:sample)>>9)&511;
            assert(buffer[i+1]==colors[(row/24)&1]);
        }
        cases++;
    }
    /* Check both sides of every exact stripe boundary, including zero. */
    for(int boundary=-9;boundary<=9;boundary++) for(int offset=-1;offset<=1;offset++) {
        int z=boundary*12288+offset;
        for(int step=-1;step<=1;step++) {
            draw_grass_span(buffer,100,z,step,colors);
            for(int i=0;i<100;i++) assert(buffer[i]==colors[(abs(z+i*step)/12288)&1]);
        }
    }
    unsigned seed=1;
    for(int i=0;i<200000;i++) {
        seed=seed*1664525u+1013904223u;int x=(int)(seed%1000001)-500000;
        seed=seed*1664525u+1013904223u;int y=(int)(seed%1000001)-500000;
        seed=seed*1664525u+1013904223u;int z=2048+seed%500000;
        int sx,sy;project_camera_point(x,y,z,&sx,&sy);
        assert(sx==x*120/z+120 && sy==-y*120/z+80);
    }
    fills=0;draw_grass_span(buffer,240,-60000,128,colors);
    assert(fills<=4);
    printf("PASS: %d grass spans match per-pixel sampling; 200000 projections match exact division; 240-pixel sample uses %d bulk fills\\n",cases,fills);
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.c').write_text(harness)
 subprocess.run(['cc','-O2','-fsanitize=undefined,address',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0','UBSAN_OPTIONS':'halt_on_error=1'})
