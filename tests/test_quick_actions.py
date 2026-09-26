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
    write=lambda symbol,value:f'w/4 0x{symbols[symbol]:x} {value}'
    commands=[f'b/t 0x{symbols["present_frame"]:x}','c',f'b/t 0x{key_return:x}']
    def case(state,keys,setup,reads):
        commands.extend(['c',write('game_state',state),f'w/2 0x{symbols["__key_curr"]:x} {keys}',f'w/2 0x{symbols["__key_prev"]:x} 0']+setup+['c']+[read(name) for name in reads])
    case(9,1,[write('pause_selection',1),write('score_blue',4),write('score_orange',2)],['game_state','score_blue','score_orange','match_timer'])
    case(18,5,[write('current_training_level',3)],['game_state','current_training_level'])
    case(18,6,[write('current_training_level',9)],['game_state','current_training_level'])
    commands+=['q']
    shutil.copyfile(root/'gba_3d.gba',p/'test.gba')
    result=subprocess.run(['stdbuf','-oL','/usr/games/mgba','-d',str(p/'test.gba')],input='\n'.join(commands)+'\n',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'})
    values=[int(v,16) for v in re.findall(r'^\s*0x([0-9a-fA-F]{8})\s*$',result.stdout,re.M)]
    assert values[:3]==[8,0,0],values
    assert 7196<=values[3]<=7200,values
    assert values[4] in (17,18) and values[5]==3,values
    assert values[6] in (17,18) and values[7]==0,values
    print('PASS: pause restart resets match; training retry retains drill; next drill wraps')
