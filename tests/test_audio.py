"""Exercise the real DMA audio scheduler and verify imported sample boundaries."""
from pathlib import Path
import tempfile,subprocess,os,re,json
root=Path(__file__).resolve().parents[1]
bank=(root/'assets/audio/sounds.bin').read_bytes()
entries=[tuple(map(int,m)) for m in re.findall(r'\{(\d+),(\d+),(\d+)\}',(root/'assets/audio/sounds.inc').read_text())]
assert len(entries)==9
assert entries[0][1]>=int(1.19*8192)
assert entries[3][1]>5.9*8192
for offset,count,frames in entries:
    assert offset%4==0 and count>0
    assert count <= frames*8192*280896/16777216 < count+138
    assert bank[offset+count:offset+count+512]==bytes(512)
    assert max(bank[offset:offset+count])>0
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)
    macros=['SDS_AL','SDS_AR','SDS_ATMR1','SDS_BL','SDS_BR','SDS_BTMR1','SDS_ARESET','SDS_BRESET','SSTAT_ENABLE','TM_ENABLE','DMA_ENABLE','DMA_REPEAT','DMA_32','DMA_DST_FIXED','DMA_AT_FIFO']
    registers=['REG_DMA1CNT','REG_DMA1SAD','REG_DMA1DAD','REG_DMA2CNT','REG_DMA2SAD','REG_DMA2DAD','REG_FIFO_A','REG_FIFO_B','REG_SNDDSCNT','REG_SNDSTAT','REG_SNDDMGCNT','REG_TM1CNT','REG_TM1D','REG_IME']
    (p/'tonc.h').write_text('#include <stdint.h>\ntypedef uintptr_t u32;\n'+'\n'.join(f'#define {name} (1u<<{i})' for i,name in enumerate(macros))+'\nstatic u32 '+','.join(registers)+';\n')
    (p/'test.c').write_text('''#include <assert.h>
#include "audio.c"
const unsigned char audio_data[400000]={0};
int main(void) {
 REG_IME=1;audio_init();assert(audio_enabled() && REG_TM1D==63488);
 audio_loop(AUDIO_BOOST);assert(loop==AUDIO_BOOST && REG_DMA2CNT);
 int duration=loop_frames;
 audio_loop(AUDIO_BOOST);assert(loop_frames==duration); /* no per-frame restarts */
 for(int i=0;i<duration;i++)audio_vblank();
 assert(loop_frames==duration && REG_DMA2CNT);
 audio_impact(127);assert(effect==-1);
 audio_impact(512);assert(effect==AUDIO_HIT && hit_cooldown==6);
 audio_impact(512);assert(effect==AUDIO_HIT);
 audio_play(AUDIO_JUMP);assert(effect==AUDIO_HIT);
 int remaining=effect_frames;audio_play(AUDIO_HIT2);
 assert(effect==AUDIO_HIT && effect_frames==remaining); /* let the impact finish */
 audio_play(AUDIO_GOAL);assert(effect==AUDIO_GOAL);
 audio_vblank();remaining=effect_frames;audio_play(AUDIO_GOAL);
 assert(effect_frames==remaining); /* repeated events do not restart the tail */
 audio_play(AUDIO_HIT2);assert(effect==AUDIO_GOAL);
 duration=effect_frames;
 for(int i=0;i<duration;i++)audio_vblank();
 assert(effect==-1 && !REG_DMA1CNT && REG_DMA2CNT);
 audio_loop(AUDIO_BOOST);assert(loop==AUDIO_BOOST);
 audio_loop(-1);assert(loop==-1 && !REG_DMA2CNT);
 audio_play(AUDIO_SELECT);audio_set_enabled(0);
 assert(!audio_enabled() && !REG_DMA1CNT && !REG_DMA2CNT);
 audio_play(AUDIO_GOAL);audio_loop(AUDIO_BOOST);assert(effect==-1 && loop==-1);
 audio_set_enabled(1);audio_loop(AUDIO_BOOST);assert(loop==AUDIO_BOOST);
 audio_loop(AUDIO_MUSIC);assert(loop==AUDIO_MUSIC);
 audio_loop(-1);assert(!REG_DMA2CNT);
 assert(REG_IME==1);
 return 0;
}
''')
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-fsanitize=address,undefined','-I',str(p),'-I',str(root),str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0','UBSAN_OPTIONS':'halt_on_error=1'})
print('PASS: sample alignment/padding, independent effect/loop DMA, priorities, cooldowns, loop restart, expiry, mute, interrupt-state preservation')
