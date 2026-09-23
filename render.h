/**
 * @file render.h
 * @brief High-performance 2D rendering primitives for the GBA (Mode 4).
 */

#ifndef RENDER_H
#define RENDER_H

#include <tonc.h>

#define SCREEN_WIDTH 240
#define SCREEN_HEIGHT 160

/* --- Rendering Resolution Options --- */
// 1 = 240x160 (Native), 2 = 120x80 (4x Faster)
#ifndef RENDER_SCALE
#define RENDER_SCALE 1
#endif
#define RENDER_WIDTH (SCREEN_WIDTH / RENDER_SCALE)
#define RENDER_HEIGHT (SCREEN_HEIGHT / RENDER_SCALE)

/* Constant-expression GBA BGR555 Color compiler macro */
#define RGB5(r, g, b) (((r) & 31) | (((g) & 31) << 5) | (((b) & 31) << 10))

/* --- Shared EWRAM Frame Buffer --- */
extern u8 frame_buffer[240 * 160];

/* --- Function Prototypes --- */

/**
 * @brief Initialize 2D rendering systems (e.g. font pixel LUT).
 */
void init_render(void);

/**
 * @brief Clear the off-screen frame buffer.
 */
void clear_screen(u8 color);

/**
 * @brief Copy EWRAM frame buffer to the active GBA VRAM page.
 */
void swap_buffers(void);
void video_vblank(void);
u32 video_ticks(void);

/**
 * @brief Draw a 2x2 point on the screen (scaled automatically by RENDER_SCALE).
 */
void draw_point(int x, int y, u8 color);

/**
 * @brief Draw a line using Cohen-Sutherland clipping and Bresenham's algorithm.
 */
void draw_line(int x0, int y0, int x1, int y1, u8 color);

/**
 * @brief Fast 32-bit word aligned scanline filler.
 */
void fast_span_fill(u8 *dst, u32 color4, int count);

/**
 * @brief Draw a flat-filled triangle (Unclipped fast-path).
 */
void draw_triangle_flat_unclipped(int x0, int y0, int x1, int y1, int x2,
                                  int y2, u8 color);

/**
 * @brief Draw a flat-filled triangle with boundary clipping.
 */
void draw_triangle_flat_clipped(int x0, int y0, int x1, int y1, int x2, int y2,
                                u8 color);

/**
 * @brief Draw an affine textured triangle (Unclipped fast-path).
 */
void draw_triangle_textured_unclipped(int x0, int y0, int u0, int v0,
                                      int x1, int y1, int u1, int v1,
                                      int x2, int y2, int u2, int v2,
                                      const u8 tex[64][64], u8 fallback_color);

/**
 * @brief Draw an affine textured triangle with boundary clipping.
 */
void draw_triangle_textured_clipped(int x0, int y0, int u0, int v0,
                                    int x1, int y1, int u1, int v1,
                                    int x2, int y2, int u2, int v2,
                                    const u8 tex[64][64], u8 fallback_color);

/**
 * @brief Draw a single character using the custom 8x8 font.
 */
void draw_char(char c, int x, int y, u8 color);

/**
 * @brief Draw a string using the custom 8x8 font.
 */
void draw_string(const char *str, int x, int y, u8 color);

#endif /* RENDER_H */
