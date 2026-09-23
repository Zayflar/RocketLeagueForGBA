"""Exercise real ROM input edges and fixed ticks in headless mGBA."""
from pathlib import Path
import subprocess, tempfile, re, os, shutil
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['/opt/devkitpro/devkitARM/bin/arm-none-eabi-nm',str(root/'gba_3d.elf')],text=True)
symbols={v[2]:int(v[0],16) for line in nm.splitlines() if len(v:=line.split())==3}
disasm=subprocess.check_output(['/opt/devkitpro/devkitARM/bin/arm-none-eabi-objdump','-d',str(root/'gba_3d.elf')],text=True)
key_return=int(re.search(r'\n\s*([0-9a-f]+):[^\n]*\bbl\s+[^\n]*<key_poll>',disasm).group(1),16)+4
source=(root/'main.c').read_text()
a=source.index('typedef struct {\n    Vector3 pos;\n    Vector3 vel;')
car=source[a:source.index('} Car;',a)+6]
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)
    (p/'offset.c').write_text('#include <stddef.h>\n#include <stdio.h>\ntypedef int fixed; typedef struct {int x,y,z;} Vector3;\n'+car+'\nint main(void){printf("%zu %zu %zu",offsetof(Car,can_double_jump),offsetof(Car,is_on_ground),offsetof(Car,flip_timer));}')
    subprocess.run(['cc',str(p/'offset.c'),'-o',str(p/'offset')],check=True)
    double,ground,flip=map(int,subprocess.check_output([str(p/'offset')],text=True).split())
    read=lambda symbol,offset=0:f'r/4 0x{symbols[symbol]+offset:x}'
    commands=[f'b/t 0x{symbols["present_frame"]:x}','c',f'w/4 0x{symbols["game_state"]:x} 2',f'b/t 0x{key_return:x}','c',f'w/2 0x{symbols["__key_curr"]:x} 1',f'w/2 0x{symbols["__key_prev"]:x} 0','d 2','c','c','c','c','c',read('match_timer'),f'b/t 0x{key_return:x}']
    for keys,previous in [(1,0),(1,1),(0,1),(1,0)]:
        commands+=['c',f'w/2 0x{symbols["__key_curr"]:x} {keys}',f'w/2 0x{symbols["__key_prev"]:x} {previous}','c',read('player',double),read('player',ground),read('player',flip),read('match_timer')]
    commands+=['q']
    shutil.copyfile(root/'gba_3d.gba',p/'test.gba')
    result=subprocess.run(['stdbuf','-oL','/usr/games/mgba','-d',str(p/'test.gba')],input='\n'.join(commands)+'\n',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'})
    values=[int(v,16) for v in re.findall(r'^\s*0x([0-9a-fA-F]{8})\s*$',result.stdout,re.M)]
    assert len(values)==17,result.stdout[-4000:]
    initial=values[0]
    for frame in range(4):
        double_left,on_ground,flip_timer,clock=values[1+frame*4:5+frame*4]
        assert not on_ground and not flip_timer,values
        assert double_left==(frame<3),values
        assert clock==initial-2*(frame+1),values
    print('PASS: two physics ticks per frame; one press jumps once, holding does not double-jump, second press does; clock stays real-time')
