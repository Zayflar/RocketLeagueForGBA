"""Verify hidden-page copying and at most one presentation per VBlank."""
from pathlib import Path
import subprocess,tempfile
source=(Path(__file__).resolve().parents[1]/'render.c').read_text()
code=source[source.index('static volatile u32 video_frame'):source.index('/* --- Fast 32-bit Word Span Filler --- */')]
harness='''#include <stdint.h>
#include <assert.h>
#include <stdio.h>
typedef uintptr_t u32;
#define RENDER_HEIGHT 160
#define DCNT_PAGE 16
#define DMA_ENABLE (1u<<31)
#define DMA_32 (1u<<26)
static u32 REG_DISPCNT,REG_DMA3SAD,REG_DMA3DAD,REG_DMA3CNT;
static int REG_VCOUNT,waits;
static char frame_buffer[240*160];
static void wait_vblank(void);
#define VBlankIntrWait wait_vblank
'''+code+'''
static void wait_vblank(void) {
    /* Hidden-page DMA was issued before the wait, with the old page visible. */
    assert(REG_DMA3DAD==((REG_DISPCNT&DCNT_PAGE)?0x06000000:0x0600A000));
    assert(REG_DMA3CNT==((240*160)/4|DMA_ENABLE|DMA_32));
    ++waits;video_vblank();REG_VCOUNT=160;
}
int main(void) {
    REG_VCOUNT=80;swap_buffers();assert(waits==1 && (REG_DISPCNT&DCNT_PAGE));
    /* A second fast frame must not present in the same blanking interval. */
    REG_VCOUNT=180;swap_buffers();assert(waits==2 && !(REG_DISPCNT&DCNT_PAGE));
    /* Work ending in the next VBlank can flip immediately. */
    video_vblank();REG_VCOUNT=175;swap_buffers();assert(waits==2);
    video_vblank();REG_VCOUNT=227;swap_buffers();assert(waits==3);
    REG_VCOUNT=20;swap_buffers();assert(waits==4);
    puts("PASS: copy before sync, one flip per VBlank, safe active/late-frame waits");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);(p/'test.c').write_text(harness)
    subprocess.run(['cc','-std=c99','-fsanitize=undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
