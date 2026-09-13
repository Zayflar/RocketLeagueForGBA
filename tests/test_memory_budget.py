"""Keep fast-code/data allocation clear of the GBA user stack."""
from pathlib import Path
import os,subprocess
root=Path(__file__).resolve().parents[1]
nm=Path(os.environ.get('DEVKITARM','/opt/devkitpro/devkitARM'))/'bin/arm-none-eabi-nm'
output=subprocess.check_output([str(nm),str(root/'gba_3d.elf')],text=True)
symbols={parts[2]:int(parts[0],16) for line in output.splitlines() if len(parts:=line.split())==3}
# Audited maximum render chain is ~4 KB; retain another KB of headroom.
stack=symbols['__sp_usr']-symbols['__fini_array_end']
ewram=0x02040000-symbols['__ewram_end']
assert stack>=5120, f'Only {stack} bytes remain for the user stack'
assert ewram>=4096, f'Only {ewram} bytes remain in EWRAM'
print(f'PASS: {stack} bytes of stack space; {ewram} bytes of EWRAM headroom')
