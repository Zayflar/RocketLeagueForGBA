/**
 * @file engine3d.h
 * @brief High-performance 3D engine definitions for the GBA (Mode 4).
 */

#ifndef ENGINE3D_H
#define ENGINE3D_H

#include <tonc.h>

#ifdef IWRAM_CODE
#undef IWRAM_CODE
#endif
#define IWRAM_CODE __attribute__((section(".iwram"), target("arm"), long_call))

#include "render.h"
#ifdef __arm__
#define ROM_ARM_CODE __attribute__((target("arm"),long_call))
#else
#define ROM_ARM_CODE
#endif

/* --- Fixed-Point Math Definitions (8.8 format) --- */
typedef int32_t fixed;

#define FP_SHIFT        8
#define FP_SCALE        256
#define FP_ONE          (1 << FP_SHIFT)

#define INT_TO_FP(n)    ((fixed)((n) * FP_SCALE))
#define FP_TO_INT(f)    ((int32_t)((f) >> FP_SHIFT))
#define FP_MUL(a, b)    (((a) * (b)) >> FP_SHIFT)
#define FP_DIV(a, b)    (((a) * FP_SCALE) / (b))

/* Constant-expression GBA BGR555 Color compiler macro */

/* --- 3D Vector Structure --- */
typedef struct {
    fixed x;
    fixed y;
    fixed z;
} Vector3;

/* --- 3D Face / Polygon Structure (Packed 4-byte 32-bit aligned struct) --- */
typedef struct {
    u8 v1;           ///< Index of first vertex (0-255)
    u8 v2;           ///< Index of second vertex (0-255)
    u8 v3;           ///< Index of third vertex (0-255)
    u8 base_color;   ///< Material group (0-7), or a literal palette index
    u8 uv[3][2];     ///< UV coordinates: uv[vertex][0=U, 1=V]
} Face;

/* --- 3D Mesh Structure --- */
typedef struct {
    const char *name;
    uint16_t vertex_count;
    uint16_t face_count;
    const Vector3 *vertices;
    const Face *faces;
    const Vector3 *face_normals;
} Mesh;

/* --- Rendering Modes --- */
#define RENDER_POINT_CLOUD 0
#define RENDER_WIREFRAME   1
#define RENDER_FLAT        2
#define RENDER_OUTLINED    3
#define RENDER_OUTLINED_WHITE 4
#define RENDER_TEXTURED    5
#define RENDER_ACCENTS     6 /* textured paint/glass panels; flat tyres and sides */

/* --- Shared EWRAM Frame Buffer --- */
extern u8 frame_buffer[240 * 160];
extern u8 pitch_texture[512][256];
extern u8 car_texture[64][64]; // UV editable car texture
extern int performance_mode; /* 1=Fast match graphics, 0=Detailed */
extern int active_pitch_mode; /* 0=soccer, 1=hockey */

/* --- Look-Up Tables --- */
extern fixed custom_div_lut[2048];
extern int32_t custom_sin_lut[256];
extern int32_t custom_cos_lut[256];
extern int16_t custom_sin_fp[256];
extern int16_t custom_cos_fp[256];
extern u8 custom_sqrt_lut[4096];

/* --- Function Prototypes --- */

/**
 * @brief Fast single-cycle square root using LUT + bit shifts.
 */
int32_t fast_sqrt(int32_t val);

/**
 * @brief Initialize 3D engine, setup Mode 4 palette and buffer.
 */
void init_3d_engine(void);

/**
 * @brief Generate soccer pitch floor texture.
 */
void init_pitch_texture(void);

/**
 * @brief Generate hockey ice rink floor texture.
 */
void init_hockey_pitch_texture(void);

/**
 * @brief Renders the sky and pseudo-raycast floor seamlessly (Mode 7 style).
 */
void draw_environment_background(u8 sky_color);

/**
 * @brief Transform, project, light, and render a 3D Mesh.
 * @return Number of visible/rendered polygons (for stats)
 */
int draw_model(const Mesh *mesh, int angle_x, int angle_y, fixed scale, fixed z_offset, int render_mode);

/**
 * @brief Set the 3D camera position and orientation in the world.
 */
int camera_sin_q8(int angle);
int camera_cos_q8(int angle);
void set_camera_q8(Vector3 pos, int yaw, int pitch);
void set_camera(Vector3 pos, int yaw, int pitch);
void set_camera_lookat(Vector3 pos, Vector3 target, int pitch);

/**
 * @brief Projects a 3D world coordinate to 2D screen coordinates.
 * @return 1 if point is in front of camera (renderable), 0 if behind (clipped).
 */
int project_vertex_world(Vector3 world_pos, int *sx, int *sy);
int draw_soccer_ball(Vector3 pos, int yaw, int pitch);
void draw_world_line(Vector3 a, Vector3 b, u8 color);
int world_sphere_visible(Vector3 pos, fixed radius);
int world_bounds_visible(Vector3 lo, Vector3 hi);
int world_target_indicator(Vector3 pos, int *sx, int *sy);

/**
 * @brief Transform, project, light, and render a 3D Mesh in world coordinates relative to the camera.
 * @param color_override If >= 0, overrides the base color of all faces (useful for teams)
 * @return Number of visible/rendered polygons
 */
/* Dedicated environment colors, separate from UI and black tyre materials. */
enum {
    SHADOW_RAMP_START = 224, SHADOW_GRASS_EDGE = 158, SHADOW_GRASS_CORE,
    SHADOW_ICE_EDGE, SHADOW_ICE_CORE,
    SKY_GRADIENT_START, SKY_GRADIENT_COUNT = 16,
    ICE_SURFACE_STRIPE = SKY_GRADIENT_START + SKY_GRADIENT_COUNT,
    STAND_DARK, STAND_LIGHT, STAND_RAIL, CROWD_BLUE, CROWD_ORANGE, CROWD_NEUTRAL, WALL_HEX
};

void build_dodge_rotation(int yaw, int pitch_dir, int roll_dir, int angle, int32_t mod_m[9]);
void build_model_rotation(int yaw, int pitch, int roll, int32_t mod_m[9]);
int draw_model_world(const Mesh *mesh, Vector3 pos, int yaw, int pitch, int roll, fixed scale, int color_override, int render_mode);
int draw_model_world_mat(const Mesh *mesh, Vector3 pos, const int32_t mod_m[9], fixed scale, int color_override, int render_mode);

/**
 * @brief Fast integer square root.
 */
int32_t int_sqrt(int32_t val);

void init_mesh_normals(void);

#endif /* ENGINE3D_H */
