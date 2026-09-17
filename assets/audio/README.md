# Core gameplay audio

Eight clips imported from the user's RocketLeague-Audio folder cover three ball
impacts, jumping, goal explosions, quiet menu navigation/confirmation, and boost. Engine, idle, pickup,
achievement, and music cues have been removed. Source files remain unchanged.

Regenerate with `python3 tools/import_audio.py [path/to/gba_audio/pcm]` and `make`.
The goal uses the full 5.96-second source, decoded to the cached development WAV
`source/goal_explosion.wav` from
`GoalExplosions/SFX_GoalExplosion_NewDefault/SFX_GoalExplosion_NewDefault_0001.ogg`.
It was decoded using the source repository's `decode_to_wave` GStreamer helper at
8192 Hz. Other clips use the prepared WAV pack. `manifest.json` records the inputs.
Only `sounds.bin` and the descriptor table are linked into the cartridge.

The importer removes DC offset, resamples to 8192 Hz signed 8-bit mono, balances
levels, fades edges, aligns each sample, and appends 512 silent guard bytes.
Direct Sound A / DMA1 plays one effect; Direct Sound B / DMA2 plays the current
boost loop. Both use timer 1, leaving the frame/link clock on timer 0.
VBlank stops finished samples and restarts loops, independent of rendering.
No software mixer or persistent sample RAM buffer is needed.

Impacts run up to 1.2 seconds, jump up to one second, and goals nearly six seconds.
Repeated/equal-priority events do not cut off or restart an active effect. Goals
can interrupt impacts, which can interrupt jumps. Impact requests also have a
six-VBlank cooldown. Continuous sounds stop on release, pause, or leaving gameplay.
No engine or idle loops remain. Menu navigation is 0.1 seconds at 12% sample gain;
confirmation is 0.2 seconds at 18% gain. Boost loops only while the player boosts.

Host tests cover sample padding, durations, priorities, duplicate suppression,
loop restart, mute, and expiry. Actual GBA/emulator listening remains unverified.

Update: the bank now contains nine clips, including `music_map_09` for the main
menu only. Its roughly 32-second excerpt loops at 25% sample gain. There is no
song-title metadata in the supplied archive. Engine/idle sounds remain absent.
