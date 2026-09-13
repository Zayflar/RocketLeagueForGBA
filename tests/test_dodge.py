"""Exercise the actual dodge update: timing, recovery, and directional balance."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'main.c').read_text()
car = source[source.index('typedef struct {\n    Vector3 pos;\n    Vector3 vel;'):source.index('} Car;') + len('} Car;')]
frames = '\n'.join(line for line in source.splitlines() if line.startswith('#define FLIP_'))
update = source[source.index('    // Flip animation logic'):source.index('    // End flip animation')]
harness = '''#include <stdint.h>
#include <assert.h>
#include <math.h>
#include <stdio.h>
typedef int32_t fixed;
typedef struct { fixed x,y,z; } Vector3;
int custom_sin_fp[256], custom_cos_fp[256];
''' + frames + '\n' + car + '\nvoid step(Car *car) {\n' + update + '''
}
int main(void) {
    for(int i=0;i<256;i++) {
        custom_sin_fp[i]=lround(sin(i*6.283185307179586/256)*256);
        custom_cos_fp[i]=lround(cos(i*6.283185307179586/256)*256);
    }
    assert(FLIP_STEP_TICKS * 10 * 5 == FLIP_DURATION_TICKS * 6);
    int frames=(FLIP_DURATION_TICKS+FLIP_STEP_TICKS-1)/FLIP_STEP_TICKS;
    assert(frames==9);
    for(int yaw=0;yaw<256;yaw+=16) {
        double straight=0;
        for(int pitch=-1;pitch<=1;pitch++) for(int roll=-1;roll<=1;roll++) {
            if(!pitch && !roll) continue;
            Car c={0}; c.yaw=yaw; c.flip_timer=FLIP_DURATION_TICKS;
            c.flip_pitch_dir=pitch; c.flip_roll_dir=roll;
            for(int frame=1;frame<=frames;frame++) {
                step(&c);
                int remaining=FLIP_DURATION_TICKS-frame*FLIP_STEP_TICKS;
                if(remaining<0) remaining=0;
                assert(c.flip_timer==remaining);
                int angle=((FLIP_DURATION_TICKS-remaining)*256/FLIP_DURATION_TICKS)&255;
                assert(c.visual_pitch==((pitch*angle)&255));
                assert(c.visual_roll==((roll*angle)&255));
                if(frame<frames) assert(c.visual_pitch || c.visual_roll);
            }
            assert(!c.visual_pitch && !c.visual_roll);
            fixed vx=c.vel.x, vz=c.vel.z;
            step(&c);
            assert(c.vel.x==vx && c.vel.z==vz);
            double speed=hypot(vx,vz);
            if(pitch==-1 && roll==0) straight=speed;
            if(straight) assert(fabs(speed-straight)<straight*0.02);
        }
    }
    puts("PASS: faster full dodge rotation, neutral recovery, balanced directional impulse");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)
    (path/'test.c').write_text(harness)
    subprocess.run(['cc','-fsanitize=undefined','-O1',str(path/'test.c'),'-lm','-o',str(path/'test')],check=True)
    subprocess.run([str(path/'test')],check=True)
