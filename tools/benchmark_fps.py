"""Measure ROM frame intervals in headless mGBA, in a reproducible seeded scene.
Not a complete gameplay benchmark; results are emulated GBA cycles, not host speed.
"""
from pathlib import Path
import subprocess,os,re,tempfile,shutil,sys,json
rom=Path(sys.argv[1] if len(sys.argv)>1 else 'gba_3d.gba').resolve()
elf=rom.with_suffix('.elf')
nm=subprocess.check_output(['/opt/devkitpro/devkitARM/bin/arm-none-eabi-nm',str(elf)],text=True)
symbols={v[2]:int(v[0],16) for l in nm.splitlines() if len(v:=l.split())==3}
disasm=subprocess.check_output(['/opt/devkitpro/devkitARM/bin/arm-none-eabi-objdump','-d',str(elf)],text=True)
# Press A in Play through the actual menu handler after key_poll. This calls
# reset_match and initializes opponents/pads, unlike forcing a training state.
key_return=int(re.search(r'\n\s*([0-9a-f]+):[^\n]*\bbl\s+[^\n]*<key_poll>',disasm).group(1),16)+4
commands=[f'b/t 0x{symbols["swap_buffers"]:x}','c',
    f'w/4 0x{symbols["game_state"]:x} 2',f'b/t 0x{key_return:x}','c',
    f'w/2 0x{symbols["__key_curr"]:x} 1',f'w/2 0x{symbols["__key_prev"]:x} 0','d 2','c']+['c']*30+[
    f'r/4 0x{symbols["game_state"]:x}','q']
with tempfile.TemporaryDirectory() as tmp:
    target=Path(tmp)/'bench.gba';shutil.copyfile(rom,target)
    result=subprocess.run(['stdbuf','-oL','/usr/games/mgba','-d',str(target)],input='\n'.join(commands)+'\n',text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},timeout=20)
states=re.findall(r'^\s*0x([0-9A-Fa-f]{8})\s*$',result.stdout,re.M)
assert states and int(states[-1],16)==8, "Benchmark did not remain in active gameplay"
cycles=[int(x) for x in re.findall(r'Cycle: (\d+)',result.stdout)]
assert len(cycles)>=18,result.stdout[-2000:]
intervals=[b-a for a,b in zip(cycles[-13:-1],cycles[-12:])]
print(json.dumps(dict(rom=str(rom),frames=len(intervals),mean_cycles=round(sum(intervals)/len(intervals)),fps=round(16777216*len(intervals)/sum(intervals),2),target_cycles=280896)))
