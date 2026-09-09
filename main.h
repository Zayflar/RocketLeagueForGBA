/**
 * @file main.h
 * @brief Architecture definitions and structures for the GBA Super Smash Bros. Demake.
 * @details Target platform: Game Boy Advance (ARM7TDMI, 16.78 MHz).
 * Uses libtonc for register mapping, video definitions, and BIOS interrupt calls.
 */

#ifndef MAIN_H
#define MAIN_H

#include <tonc.h>

/* --- Fixed-Point Math Definitions (8.8 format) --- */
typedef int32_t fixed;

#define FX_SHIFT        8
#define FX_SCALE        256
#define FX_ONE          (1 << FX_SHIFT)

#define INT_TO_FX(n)    ((fixed)((n) << FX_SHIFT))
#define FX_TO_INT(f)    ((int32_t)((f) >> FX_SHIFT))
#define FX_MUL(a, b)    ((fixed)(((int64_t)(a) * (b)) >> FX_SHIFT))
#define FX_DIV(a, b)    ((fixed)((((int64_t)(a)) << FX_SHIFT) / (b)))

/* Constant-expression GBA BGR555 Color compiler macro */
#define RGB5(r,g,b)     (((r) & 31) | (((g) & 31) << 5) | (((b) & 31) << 10))

/* --- Screen Constants --- */
#define SCREEN_WIDTH    240
#define SCREEN_HEIGHT   160

/* --- Physics Configuration (8.8 Fixed-Point values) --- */
#define PHYS_GRAVITY     (INT_TO_FX(0) + 40)   // ~0.15 px/frame^2 (40/256)
#define PHYS_FRICTION    (INT_TO_FX(0) + 30)   // Ground friction deceleration (30/256)
#define PHYS_AIR_RES     (INT_TO_FX(0) + 10)   // Air resistance (10/256)
#define PHYS_RUN_ACCEL   (INT_TO_FX(0) + 45)   // Acceleration (45/256)
#define PHYS_MAX_RUN     (INT_TO_FX(2))        // Max run velocity (2.0 px/frame)
#define PHYS_JUMP_FORCE  (-INT_TO_FX(4) - 128)  // Initial jump velocity (~ -4.5 px/frame)

/* --- Character Selection Configuration --- */
#define NUM_CHARACTERS   16

#define PLAYER_WIDTH    INT_TO_FX(16)
#define PLAYER_HEIGHT   INT_TO_FX(16)

/* --- Character Definition / Database Struct --- */
typedef struct {
    const char *name;       ///< Display name of character
    fixed max_speed;        ///< Maximum horizontal speed
    fixed run_accel;        ///< Acceleration per running frame
    fixed jump_force;       ///< Vertical launch velocity on jump
    int32_t weight;         ///< Character weight (affects knockback: higher weight = less launch)
    int32_t attack_damage;  ///< Raw damage percentage added per hit
    fixed attack_knockback; ///< Knockback multiplier / launching scalar
    fixed attack_range;     ///< Horizontal width of attack hitbox
    u16 color_primary;      ///< Primary body color in BGR555
    u16 color_secondary;    ///< Secondary clothing/hair color in BGR555
} CharacterDef;

/* --- Game Modes --- */
typedef enum {
    MODE_TITLE = 0,         ///< Splash title menu screen
    MODE_MENU,              ///< Character select screen
    MODE_BATTLE            ///< In-game fight
} GameMode;

/* --- Player States --- */
typedef enum {
    STATE_IDLE = 0,
    STATE_RUN,
    STATE_JUMP,
    STATE_ATTACK,
    STATE_HITSTUN
} PlayerState;

/* --- Player Structure --- */
typedef struct {
    int32_t char_id;        ///< Index into character_db (0 to 15)
    
    fixed x;                ///< X position (fixed-point)
    fixed y;                ///< Y position (fixed-point)
    fixed vx;               ///< X velocity (fixed-point)
    fixed vy;               ///< Y velocity (fixed-point)
    
    int32_t facing;         ///< Facing direction: 1 = Right, -1 = Left
    int32_t damage_percent; ///< Cumulative damage percentage (affects knockback)
    PlayerState state;      ///< Current character state
    int32_t state_timer;    ///< Timer used to count frames in timed states (attack/hitstun)
    
    int32_t on_ground;      ///< Boolean flag (1 if standing on platform, 0 otherwise)
    u32 oam_id;             ///< Assigned sprite index in OAM (0 or 1 for characters)
    u32 tile_offset;        ///< Base tile offset in VRAM obj block
} Player;

/* --- Platform / Bounding Box (AABB) --- */
typedef struct {
    fixed x1;               ///< Left bound (fixed-point)
    fixed y1;               ///< Top bound (fixed-point)
    fixed x2;               ///< Right bound (fixed-point)
    fixed y2;               ///< Bottom bound (fixed-point)
} Platform;

/* --- Shared Global Variables --- */
extern Player player1;
extern Player player2;
extern OBJ_ATTR obj_buffer[128];
extern const Platform stage_platform;
extern const CharacterDef character_db[NUM_CHARACTERS];

extern GameMode game_mode;
extern int32_t cursor_p1;
extern int32_t cursor_p2;
extern int32_t menu_step;

/* --- Initialize Functions --- */
void init_hardware(void);
void init_players(void);
void handle_inputs(void);

#endif /* MAIN_H */
