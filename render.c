/**
 * @file render.c
 * @brief 2D rendering primitives, Cohen-Sutherland line clipping, and triangle rasterization.
 */

#include "engine3d.h"
#include <stdlib.h>

/* --- Custom 8x8 Bitmap Font --- */
static const u8 font_8x8[42][8] = {
    { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 }, // Space (0)
    { 0x00, 0x00, 0x18, 0x18, 0x00, 0x18, 0x18, 0x00 }, // : (1)
    { 0x00, 0x00, 0x00, 0x3c, 0x3c, 0x00, 0x00, 0x00 }, // - (2)
    { 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x00 }, // . (3)
    { 0x00, 0x02, 0x06, 0x0c, 0x18, 0x30, 0x60, 0x40 }, // / (4)
    { 0x00, 0x62, 0x66, 0x0c, 0x18, 0x30, 0x66, 0x46 }, // % (5)
    
    // Numbers 0-9
    { 0x00, 0x3c, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3c }, // 0
    { 0x00, 0x18, 0x38, 0x18, 0x18, 0x18, 0x18, 0x7e }, // 1
    { 0x00, 0x3c, 0x66, 0x06, 0x1c, 0x30, 0x60, 0x7e }, // 2
    { 0x00, 0x3c, 0x66, 0x06, 0x1c, 0x06, 0x66, 0x3c }, // 3
    { 0x00, 0x0c, 0x1c, 0x3c, 0x6c, 0x7e, 0x0c, 0x0c }, // 4
    { 0x00, 0x7e, 0x60, 0x7c, 0x06, 0x06, 0x66, 0x3c }, // 5
    { 0x00, 0x3c, 0x60, 0x7c, 0x66, 0x66, 0x66, 0x3c }, // 6
    { 0x00, 0x7e, 0x06, 0x0c, 0x18, 0x30, 0x30, 0x30 }, // 7
    { 0x00, 0x3c, 0x66, 0x66, 0x3c, 0x66, 0x66, 0x3c }, // 8
    { 0x00, 0x3c, 0x66, 0x66, 0x66, 0x3e, 0x06, 0x3c }, // 9
    
    // Letters A-Z
    { 0x00, 0x3c, 0x66, 0x66, 0x7e, 0x66, 0x66, 0x66 }, // A
    { 0x00, 0x7c, 0x66, 0x66, 0x7c, 0x66, 0x66, 0x7c }, // B
    { 0x00, 0x3c, 0x66, 0x60, 0x60, 0x60, 0x66, 0x3c }, // C
    { 0x00, 0x78, 0x6c, 0x66, 0x66, 0x66, 0x6c, 0x78 }, // D
    { 0x00, 0x7e, 0x60, 0x60, 0x7c, 0x60, 0x60, 0x7e }, // E
    { 0x00, 0x7e, 0x60, 0x60, 0x7c, 0x60, 0x60, 0x60 }, // F
    { 0x00, 0x3c, 0x66, 0x60, 0x6e, 0x66, 0x66, 0x3e }, // G
    { 0x00, 0x66, 0x66, 0x66, 0x7e, 0x66, 0x66, 0x66 }, // H
    { 0x00, 0x3c, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3c }, // I
    { 0x00, 0x1e, 0x06, 0x06, 0x06, 0x66, 0x66, 0x3c }, // J
    { 0x00, 0x66, 0x6c, 0x78, 0x70, 0x78, 0x6c, 0x66 }, // K
    { 0x00, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7e }, // L
    { 0x00, 0x63, 0x77, 0x7f, 0x6b, 0x63, 0x63, 0x63 }, // M
    { 0x00, 0x66, 0x76, 0x7e, 0x7e, 0x6e, 0x66, 0x66 }, // N
    { 0x00, 0x3c, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3c }, // O
    { 0x00, 0x7c, 0x66, 0x66, 0x7c, 0x60, 0x60, 0x60 }, // P
    { 0x00, 0x3c, 0x66, 0x66, 0x66, 0x6e, 0x3c, 0x02 }, // Q
    { 0x00, 0x7c, 0x66, 0x66, 0x7c, 0x78, 0x6c, 0x66 }, // R
    { 0x00, 0x3c, 0x66, 0x60, 0x3c, 0x06, 0x66, 0x3c }, // S
    { 0x00, 0x7e, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18 }, // T
    { 0x00, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3c }, // U
    { 0x00, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3c, 0x18 }, // V
    { 0x00, 0x63, 0x63, 0x63, 0x6b, 0x7f, 0x77, 0x63 }, // W
    { 0x00, 0x66, 0x66, 0x3c, 0x18, 0x3c, 0x66, 0x66 }, // X
    { 0x00, 0x66, 0x66, 0x66, 0x3c, 0x18, 0x18, 0x18 }, // Y
    { 0x00, 0x7e, 0x06, 0x0c, 0x18, 0x30, 0x60, 0x7e }  // Z
};


static u16 font_offsets[42][64] __attribute__((section(".ewram")));
static u8 font_counts[42];
extern u8 font_pixel_lut[42][8][8]; // Initialized in engine3d.c

static inline int get_font_index(char c) {
    if (c == ' ') return 0;
    if (c == ':') return 1;
    if (c == '-') return 2;
    if (c == '.') return 3;
    if (c == '/') return 4;
    if (c == '%') return 5;
    if (c >= '0' && c <= '9') return 6 + (c - '0');
    if (c >= 'a' && c <= 'z') return 16 + (c - 'a');
    if (c >= 'A' && c <= 'Z') return 16 + (c - 'A');
    return 0;
}

void init_render(void) {
    // Pre-calculate Font Pixel LUT (unrolls bitwise character checks)
    for (int c = 0; c < 42; c++) {
        font_counts[c]=0;
        for (int r = 0; r < 8; r++) {
            u8 bits = font_8x8[c][r];
            for (int col = 0; col < 8; col++) {
                font_pixel_lut[c][r][col] = (bits & (1 << (7 - col))) ? 1 : 0;
                if(font_pixel_lut[c][r][col])font_offsets[c][font_counts[c]++]=r*240+col;
            }
        }
    }
}

/* --- Buffer Management --- */
void clear_screen(u8 color) {
    u32 color32 = (u32)color * 0x01010101u;
    memset32(frame_buffer, color32, (240 * RENDER_HEIGHT) / 4);
}

static volatile u32 video_frame;
void video_vblank(void) { ++video_frame; }
u32 video_ticks(void) {return video_frame;}

/* Separate presentation point also permits cycle-accurate pacing measurements. */
static __attribute__((noinline)) void present_frame(void) {REG_DISPCNT ^= DCNT_PAGE;}

void swap_buffers(void) {
    static u32 last_present_frame=0xffffffffu;
    u32 back_buffer = (REG_DISPCNT & DCNT_PAGE) ? 0x06000000 : 0x0600A000;
    
    REG_DMA3SAD = (u32)frame_buffer;
    REG_DMA3DAD = back_buffer;
    REG_DMA3CNT = ((240 * RENDER_HEIGHT) / 4) | DMA_ENABLE | DMA_32;
    
    /* Present every two VBlanks (~29.86 Hz), after the hidden-page DMA.
       If rendering misses its slot, wait for a safe blank and rebase there. */
    while((last_present_frame!=0xffffffffu && video_frame-last_present_frame<2) ||
          REG_VCOUNT<160 || REG_VCOUNT>225) VBlankIntrWait();
    last_present_frame=video_frame;
    present_frame();
}

/* --- Fast 32-bit Word Span Filler --- */
/* Keep the small surface-aware path in ROM, preserving the IWRAM stack. */
static __attribute__((noinline,long_call)) void shadow_span_fill(u8 *dst,u8 shade,int count) {
    int core=shade==SHADOW_GRASS_CORE || shade==SHADOW_ICE_CORE;
    while(count--) {
        int base=*dst,level;
        if(base>=150 && base<=157)level=base-150-1-core;
        else if(base>=SHADOW_RAMP_START && base<SHADOW_RAMP_START+8)
            level=base-SHADOW_RAMP_START-core;
        else {*dst++=shade;continue;}
        *dst++=SHADOW_RAMP_START+(level<0?0:level);
    }
}

static IWRAM_CODE __attribute__((noinline)) void inline_span_fill(u8 *dst, u32 color4, int count) {
    if (count <= 0) return;
    u8 shade=(u8)color4;
    if(shade>=SHADOW_GRASS_EDGE && shade<=SHADOW_ICE_CORE) {
        shadow_span_fill(dst,shade,count);
        return;
    }
    if (count < 8) {
        while (count > 0) {
            *dst++ = (u8)color4;
            count--;
        }
        return;
    }
    
    // Align destination to 4-byte boundary
    while ((uintptr_t)dst & 3) {
        *dst++ = (u8)color4;
        count--;
    }
    
    // Fast 32-bit word stores
    u32 *dst32 = (u32 *)dst;
    while (count >= 16) {
        dst32[0] = color4;
        dst32[1] = color4;
        dst32[2] = color4;
        dst32[3] = color4;
        dst32 += 4;
        count -= 16;
    }
    while (count >= 4) {
        *dst32++ = color4;
        count -= 4;
    }
    
    // Trailing bytes
    dst = (u8 *)dst32;
    while (count > 0) {
        *dst++ = (u8)color4;
        count--;
    }
}

IWRAM_CODE void fast_span_fill(u8 *dst, u32 color4, int count) {
    inline_span_fill(dst, color4, count);
}

/* --- Line and Point Drawing --- */
IWRAM_CODE void draw_point(int x, int y, u8 color) {
    if (x >= 0 && x < RENDER_WIDTH && y >= 0 && y < RENDER_HEIGHT) {
        frame_buffer[y * 240 + x] = color;
    }
}

// Cohen-Sutherland outcodes
#define INSIDE 0 // 0000
#define LEFT   1 // 0001
#define RIGHT  2 // 0010
#define BOTTOM 4 // 0100
#define TOP    8 // 1000

static inline int compute_outcode(int x, int y) {
    int code = INSIDE;
    if (x < 0) code |= LEFT;
    else if (x >= RENDER_WIDTH) code |= RIGHT;
    if (y < 0) code |= TOP;
    else if (y >= RENDER_HEIGHT) code |= BOTTOM;
    return code;
}

IWRAM_CODE void draw_line(int x0, int y0, int x1, int y1, u8 color) {
    int outcode0 = compute_outcode(x0, y0);
    int outcode1 = compute_outcode(x1, y1);
    int accept = 0;

    // Cohen-Sutherland line clipping
    while (1) {
        if (!(outcode0 | outcode1)) {
            // Both endpoints inside
            accept = 1;
            break;
        } else if (outcode0 & outcode1) {
            // Both endpoints share an outside zone (trivial reject)
            break;
        } else {
            // At least one point is outside
            int outcodeOut = outcode0 ? outcode0 : outcode1;
            int x = 0, y = 0;

            // Find intersection point using y = y0 + slope * (x - x0), x = x0 + (1 / slope) * (y - y0)
            if (outcodeOut & TOP) {           // point is above the clip window
                x = x0 + (x1 - x0) * (0 - y0) / (y1 - y0);
                y = 0;
            } else if (outcodeOut & BOTTOM) { // point is below the clip window
                x = x0 + (x1 - x0) * ((RENDER_HEIGHT - 1) - y0) / (y1 - y0);
                y = RENDER_HEIGHT - 1;
            } else if (outcodeOut & RIGHT) {  // point is to the right of clip window
                y = y0 + (y1 - y0) * ((RENDER_WIDTH - 1) - x0) / (x1 - x0);
                x = RENDER_WIDTH - 1;
            } else if (outcodeOut & LEFT) {   // point is to the left of clip window
                y = y0 + (y1 - y0) * (0 - x0) / (x1 - x0);
                x = 0;
            }

            // Move outside point to intersection point
            if (outcodeOut == outcode0) {
                x0 = x;
                y0 = y;
                outcode0 = compute_outcode(x0, y0);
            } else {
                x1 = x;
                y1 = y;
                outcode1 = compute_outcode(x1, y1);
            }
        }
    }

    if (!accept) return; // Entire line was clipped outside

    /* Pitch rails and HUD strokes often span a whole scanline. Use word
       stores instead of visiting each pixel with the general line loop. */
    if(y0==y1) {
        int left=x0<x1?x0:x1;
        int right=x0>x1?x0:x1;
        fast_span_fill(frame_buffer+y0*240+left,color*0x01010101u,right-left+1);
        return;
    }

    // Fast Bresenham without bounds checking since the line is guaranteed to be within [0, RENDER_WIDTH) x [0, RENDER_HEIGHT)
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy, e2;
    int y_step = sy * 240;
    u8 *ptr = &frame_buffer[y0 * 240 + x0];

    while (1) {
        *ptr = color;
        if (x0 == x1 && y0 == y1) break;
        e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; ptr += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; ptr += y_step; }
    }
}

/* --- Optimized Triangle Scanline Rasterizers (IWRAM) --- */
IWRAM_CODE void draw_triangle_flat_unclipped(int x0, int y0, int x1, int y1, int x2, int y2, u8 color) {
    if (y0 > y1) { int t; t=x0; x0=x1; x1=t; t=y0; y0=y1; y1=t; }
    if (y0 > y2) { int t; t=x0; x0=x2; x2=t; t=y0; y0=y2; y2=t; }
    if (y1 > y2) { int t; t=x1; x1=x2; x2=t; t=y1; y1=y2; y2=t; }

    if (y0 == y2) return; 

    u32 color4 = (u32)color * 0x01010101u;

    int32_t dy_02 = y2 - y0;
    int32_t dx_long = (x2 - x0) * custom_div_lut[dy_02];

    int32_t dx1 = x1 - x0;
    int32_t dy1 = y1 - y0;
    int32_t dx2 = x2 - x0;
    int cross = dx1 * dy_02 - dx2 * dy1;
    int is_right = (cross > 0);

    if (y1 > y0) {
        int32_t dy_01 = y1 - y0;
        int32_t dx_short = (x1 - x0) * custom_div_lut[dy_01];
        int32_t xa = x0 << 16;
        int32_t xb = x0 << 16;
        u8 *dst_row = &frame_buffer[y0 * 240];
        if (is_right) {
            for (int y = y0; y < y1; y++, dst_row += 240) {
                int left = xa >> 16, right = xb >> 16;
                if (right >= left) inline_span_fill(dst_row + left, color4, right - left + 1);
                xa += dx_long; xb += dx_short;
            }
        } else {
            for (int y = y0; y < y1; y++, dst_row += 240) {
                int left = xb >> 16, right = xa >> 16;
                if (right >= left) inline_span_fill(dst_row + left, color4, right - left + 1);
                xa += dx_long; xb += dx_short;
            }
        }
    }
    if (y2 > y1) {
        int32_t dy_12 = y2 - y1;
        int32_t dx_short = (x2 - x1) * custom_div_lut[dy_12];
        int32_t xa = (x0 << 16) + dx_long * (y1 - y0);
        int32_t xb = x1 << 16;
        u8 *dst_row = &frame_buffer[y1 * 240];
        if (is_right) {
            for (int y = y1; y <= y2; y++, dst_row += 240) {
                int left = xa >> 16, right = xb >> 16;
                if (right >= left) inline_span_fill(dst_row + left, color4, right - left + 1);
                xa += dx_long; xb += dx_short;
            }
        } else {
            for (int y = y1; y <= y2; y++, dst_row += 240) {
                int left = xb >> 16, right = xa >> 16;
                if (right >= left) inline_span_fill(dst_row + left, color4, right - left + 1);
                xa += dx_long; xb += dx_short;
            }
        }
    }
}

IWRAM_CODE void draw_triangle_flat_clipped(int x0, int y0, int x1, int y1, int x2, int y2, u8 color) {
    if (y0 > y1) { int t; t=x0; x0=x1; x1=t; t=y0; y0=y1; y1=t; }
    if (y0 > y2) { int t; t=x0; x0=x2; x2=t; t=y0; y0=y2; y2=t; }
    if (y1 > y2) { int t; t=x1; x1=x2; x2=t; t=y1; y1=y2; y2=t; }

    if (y0 == y2) return; 

    int y_top = y0 < 0 ? 0 : y0;
    int y_bot = y2 > RENDER_HEIGHT - 1 ? RENDER_HEIGHT - 1 : y2;
    if (y_top > y_bot) return;

    u32 color4 = (u32)color * 0x01010101u;

    int32_t dy_02 = y2 - y0;
    int32_t dx_long = (x2 - x0) * (dy_02 < 2048 ? custom_div_lut[dy_02] : 65536 / dy_02);

    int32_t dx1 = x1 - x0;
    int32_t dy1 = y1 - y0;
    int32_t dx2 = x2 - x0;
    int cross = dx1 * dy_02 - dx2 * dy1;
    int is_right = (cross > 0);

    if (y1 > y0) {
        int32_t dy_01 = y1 - y0;
        int32_t dx_short = (x1 - x0) * (dy_01 < 2048 ? custom_div_lut[dy_01] : 65536 / dy_01);
        int32_t xa = x0 * 65536;
        int32_t xb = x0 * 65536;
        if (y0 < 0) {
            xa += dx_long * (-y0);
            xb += dx_short * (-y0);
        }
        int y_end = y1 < RENDER_HEIGHT ? y1 : RENDER_HEIGHT;
        u8 *dst_row = &frame_buffer[y_top * 240];
        if (is_right) {
            for (int y = y_top; y < y_end; y++, dst_row += 240) {
                int left = xa >> 16, right = xb >> 16;
                if (left < 0) left = 0;
                if (right > RENDER_WIDTH - 1) right = RENDER_WIDTH - 1;
                if (right >= left) inline_span_fill(dst_row + left, color4, right - left + 1);
                xa += dx_long; xb += dx_short;
            }
        } else {
            for (int y = y_top; y < y_end; y++, dst_row += 240) {
                int left = xb >> 16, right = xa >> 16;
                if (left < 0) left = 0;
                if (right > RENDER_WIDTH - 1) right = RENDER_WIDTH - 1;
                if (right >= left) inline_span_fill(dst_row + left, color4, right - left + 1);
                xa += dx_long; xb += dx_short;
            }
        }
    }
    if (y2 > y1 && y1 < RENDER_HEIGHT) {
        int32_t dy_12 = y2 - y1;
        int32_t dx_short = (x2 - x1) * (dy_12 < 2048 ? custom_div_lut[dy_12] : 65536 / dy_12);
        int32_t xa = (x0 * 65536) + dx_long * (y1 - y0);
        int32_t xb = x1 * 65536;
        int y_start = y1 < 0 ? 0 : y1;
        if (y1 < 0) {
            xa += dx_long * (-y1);
            xb += dx_short * (-y1);
        }
        u8 *dst_row = &frame_buffer[y_start * 240];
        if (is_right) {
            for (int y = y_start; y <= y_bot; y++, dst_row += 240) {
                int left = xa >> 16, right = xb >> 16;
                if (left < 0) left = 0;
                if (right > RENDER_WIDTH - 1) right = RENDER_WIDTH - 1;
                if (right >= left) inline_span_fill(dst_row + left, color4, right - left + 1);
                xa += dx_long; xb += dx_short;
            }
        } else {
            for (int y = y_start; y <= y_bot; y++, dst_row += 240) {
                int left = xb >> 16, right = xa >> 16;
                if (left < 0) left = 0;
                if (right > RENDER_WIDTH - 1) right = RENDER_WIDTH - 1;
                if (right >= left) inline_span_fill(dst_row + left, color4, right - left + 1);
                xa += dx_long; xb += dx_short;
            }
        }
    }
}

/* --- Font Renderer --- */
IWRAM_CODE void draw_char(char c, int x, int y, u8 color) {
    x /= RENDER_SCALE;
    y /= RENDER_SCALE;
    int idx = get_font_index(c);
    if(x>=0 && x+7<RENDER_WIDTH && y>=0 && y+7<RENDER_HEIGHT) {
        u8 *dst=frame_buffer+y*240+x;
        for(int i=0;i<font_counts[idx];i++)dst[font_offsets[idx][i]]=color;
        return;
    }
    for (int r = 0; r < 8; r++) {
        int draw_y = y + r;
        if (draw_y < 0 || draw_y >= RENDER_HEIGHT) continue;
        
        u8 *dst = &frame_buffer[draw_y * 240 + x];
        u8 *src = font_pixel_lut[idx][r];
        
        if (x >= 0 && x + 7 < RENDER_WIDTH) {
            if (src[0]) dst[0] = color;
            if (src[1]) dst[1] = color;
            if (src[2]) dst[2] = color;
            if (src[3]) dst[3] = color;
            if (src[4]) dst[4] = color;
            if (src[5]) dst[5] = color;
            if (src[6]) dst[6] = color;
            if (src[7]) dst[7] = color;
        } else {
            for (int col = 0; col < 8; col++) {
                int draw_x = x + col;
                if (draw_x >= 0 && draw_x < RENDER_WIDTH && src[col]) {
                    dst[col] = color;
                }
            }
        }
    }
}

void draw_string(const char *str, int x, int y, u8 color) {
    while (*str) {
        draw_char(*str++, x, y, color);
        x += 8;
    }
}

// ---------------------------------------------------------
// TEXTURE MAPPING (Affine, Unclipped)
// ---------------------------------------------------------
/* Near-plane projection can produce edges taller than the reciprocal LUT. */
static inline int32_t texture_recip(int n) {
    return n <= 0 ? 0 : n < 2048 ? custom_div_lut[n] : 65536 / n;
}

IWRAM_CODE void draw_triangle_textured_unclipped(int x0, int y0, int u0, int v0,
                                      int x1, int y1, int u1, int v1,
                                      int x2, int y2, int u2, int v2,
                                      const u8 tex[64][64], u8 fallback_color) {
    if (y0 > y1) { int t; t=x0; x0=x1; x1=t; t=y0; y0=y1; y1=t; t=u0; u0=u1; u1=t; t=v0; v0=v1; v1=t; }
    if (y0 > y2) { int t; t=x0; x0=x2; x2=t; t=y0; y0=y2; y2=t; t=u0; u0=u2; u2=t; t=v0; v0=v2; v2=t; }
    if (y1 > y2) { int t; t=x1; x1=x2; x2=t; t=y1; y1=y2; y2=t; t=u1; u1=u2; u2=t; t=v1; v1=v2; v2=t; }

    if (y0 == y2) return; 

    int32_t dy_02 = y2 - y0;
    int32_t dx_long = (x2 - x0) * texture_recip(dy_02);
    int32_t du_long = (u2 - u0) * texture_recip(dy_02);
    int32_t dv_long = (v2 - v0) * texture_recip(dy_02);

    int cross = (x1 - x0) * dy_02 - (x2 - x0) * (y1 - y0);
    int is_right = (cross > 0);

    if (y1 > y0) {
        int32_t dy_01 = y1 - y0;
        int32_t dx_short = (x1 - x0) * texture_recip(dy_01);
        int32_t du_short = (u1 - u0) * texture_recip(dy_01);
        int32_t dv_short = (v1 - v0) * texture_recip(dy_01);
        
        int32_t xa = x0 * 65536, xb = x0 * 65536;
        int32_t ua = u0 << 16, ub = u0 << 16;
        int32_t va = v0 << 16, vb = v0 << 16;
        
        u8 *dst_row = &frame_buffer[y0 * 240];
        
        for (int y = y0; y < y1; y++, dst_row += 240) {
            int left = is_right ? (xa >> 16) : (xb >> 16);
            int right = is_right ? (xb >> 16) : (xa >> 16);
            int32_t u_l = is_right ? ua : ub;
            int32_t v_l = is_right ? va : vb;
            int32_t u_r = is_right ? ub : ua;
            int32_t v_r = is_right ? vb : va;
            
            if (right >= left) {
                int width = right - left + 1;
                int32_t inv_w = (width > 1) ? custom_div_lut[width - 1] : 0;
                int32_t du_x = ((int64_t)(u_r - u_l) * inv_w) >> 16;
                int32_t dv_x = ((int64_t)(v_r - v_l) * inv_w) >> 16;
                int32_t curr_u = u_l;
                int32_t curr_v = v_l;
                u8 *dst = dst_row + left;
                const u8 *tex_flat = &tex[0][0];
                for (int x = left; x <= right; x++) {
                    int tu = (curr_u >> 16) & 63;
                    int tv = (curr_v >> 16) & 63;
                    u8 c = tex_flat[(tv << 6) | tu];
                    *dst++ = c ? c : fallback_color;
                    curr_u += du_x;
                    curr_v += dv_x;
                }
            }
            xa += dx_long; xb += dx_short;
            ua += du_long; ub += du_short;
            va += dv_long; vb += dv_short;
        }
    }
    if (y2 > y1) {
        int32_t dy_12 = y2 - y1;
        int32_t dx_short = (x2 - x1) * texture_recip(dy_12);
        int32_t du_short = (u2 - u1) * texture_recip(dy_12);
        int32_t dv_short = (v2 - v1) * texture_recip(dy_12);
        
        int32_t xa = (x0 * 65536) + dx_long * (y1 - y0);
        int32_t xb = x1 * 65536;
        int32_t ua = (u0 << 16) + du_long * (y1 - y0);
        int32_t ub = u1 << 16;
        int32_t va = (v0 << 16) + dv_long * (y1 - y0);
        int32_t vb = v1 << 16;
        
        u8 *dst_row = &frame_buffer[y1 * 240];
        for (int y = y1; y <= y2; y++, dst_row += 240) {
            int left = is_right ? (xa >> 16) : (xb >> 16);
            int right = is_right ? (xb >> 16) : (xa >> 16);
            int32_t u_l = is_right ? ua : ub;
            int32_t v_l = is_right ? va : vb;
            int32_t u_r = is_right ? ub : ua;
            int32_t v_r = is_right ? vb : va;
            
            if (right >= left) {
                int width = right - left + 1;
                int32_t inv_w = (width > 1) ? custom_div_lut[width - 1] : 0;
                int32_t du_x = ((int64_t)(u_r - u_l) * inv_w) >> 16;
                int32_t dv_x = ((int64_t)(v_r - v_l) * inv_w) >> 16;
                int32_t curr_u = u_l;
                int32_t curr_v = v_l;
                u8 *dst = dst_row + left;
                const u8 *tex_flat = &tex[0][0];
                for (int x = left; x <= right; x++) {
                    int tu = (curr_u >> 16) & 63;
                    int tv = (curr_v >> 16) & 63;
                    u8 c = tex_flat[(tv << 6) | tu];
                    *dst++ = c ? c : fallback_color;
                    curr_u += du_x;
                    curr_v += dv_x;
                }
            }
            xa += dx_long; xb += dx_short;
            ua += du_long; ub += du_short;
            va += dv_long; vb += dv_short;
        }
    }
}

// ---------------------------------------------------------
// TEXTURE MAPPING (Affine, Clipped)
// ---------------------------------------------------------
ROM_ARM_CODE void draw_triangle_textured_clipped(int x0, int y0, int u0, int v0,
                                    int x1, int y1, int u1, int v1,
                                    int x2, int y2, int u2, int v2,
                                    const u8 tex[64][64], u8 fallback_color) {
    if (y0 > y1) { int t; t=x0; x0=x1; x1=t; t=y0; y0=y1; y1=t; t=u0; u0=u1; u1=t; t=v0; v0=v1; v1=t; }
    if (y0 > y2) { int t; t=x0; x0=x2; x2=t; t=y0; y0=y2; y2=t; t=u0; u0=u2; u2=t; t=v0; v0=v2; v2=t; }
    if (y1 > y2) { int t; t=x1; x1=x2; x2=t; t=y1; y1=y2; y2=t; t=u1; u1=u2; u2=t; t=v1; v1=v2; v2=t; }

    if (y0 == y2) return; 

    int y_top = y0 < 0 ? 0 : y0;
    int y_bot = y2 > RENDER_HEIGHT - 1 ? RENDER_HEIGHT - 1 : y2;
    if (y_top > y_bot) return;

    int32_t dy_02 = y2 - y0;
    int32_t dx_long = (x2 - x0) * texture_recip(dy_02);
    int32_t du_long = (u2 - u0) * texture_recip(dy_02);
    int32_t dv_long = (v2 - v0) * texture_recip(dy_02);

    int cross = (x1 - x0) * dy_02 - (x2 - x0) * (y1 - y0);
    int is_right = (cross > 0);

    if (y1 > y0) {
        int32_t dy_01 = y1 - y0;
        int32_t dx_short = (x1 - x0) * texture_recip(dy_01);
        int32_t du_short = (u1 - u0) * texture_recip(dy_01);
        int32_t dv_short = (v1 - v0) * texture_recip(dy_01);
        
        int32_t xa = x0 * 65536, xb = x0 * 65536;
        int32_t ua = u0 << 16, ub = u0 << 16;
        int32_t va = v0 << 16, vb = v0 << 16;
        if (y0 < 0) {
            xa += dx_long * (-y0); xb += dx_short * (-y0);
            ua += du_long * (-y0); ub += du_short * (-y0);
            va += dv_long * (-y0); vb += dv_short * (-y0);
        }
        int y_end = y1 < RENDER_HEIGHT ? y1 : RENDER_HEIGHT;
        u8 *dst_row = &frame_buffer[y_top * 240];
        
        for (int y = y_top; y < y_end; y++, dst_row += 240) {
            int left = is_right ? (xa >> 16) : (xb >> 16);
            int right = is_right ? (xb >> 16) : (xa >> 16);
            int32_t u_l = is_right ? ua : ub;
            int32_t v_l = is_right ? va : vb;
            int32_t u_r = is_right ? ub : ua;
            int32_t v_r = is_right ? vb : va;
            
            int span = right - left;
            int32_t inv_w = texture_recip(span);
            int32_t du_x = ((int64_t)(u_r - u_l) * inv_w) >> 16;
            int32_t dv_x = ((int64_t)(v_r - v_l) * inv_w) >> 16;
            if (left < 0) {
                u_l += du_x * (-left);
                v_l += dv_x * (-left);
                left = 0;
            }
            if (right >= RENDER_WIDTH) right = RENDER_WIDTH - 1;
            if (right >= left) {
                int32_t curr_u = u_l;
                int32_t curr_v = v_l;
                u8 *dst = dst_row + left;
                const u8 *tex_flat = &tex[0][0];
                for (int x = left; x <= right; x++) {
                    int tu = (curr_u >> 16) & 63;
                    int tv = (curr_v >> 16) & 63;
                    u8 c = tex_flat[(tv << 6) | tu];
                    *dst++ = c ? c : fallback_color;
                    curr_u += du_x;
                    curr_v += dv_x;
                }
            }
            xa += dx_long; xb += dx_short;
            ua += du_long; ub += du_short;
            va += dv_long; vb += dv_short;
        }
    }
    if (y2 > y1) {
        int32_t dy_12 = y2 - y1;
        int32_t dx_short = (x2 - x1) * texture_recip(dy_12);
        int32_t du_short = (u2 - u1) * texture_recip(dy_12);
        int32_t dv_short = (v2 - v1) * texture_recip(dy_12);
        
        int32_t xa = (x0 * 65536) + dx_long * (y1 - y0);
        int32_t xb = x1 * 65536;
        int32_t ua = (u0 << 16) + du_long * (y1 - y0);
        int32_t ub = u1 << 16;
        int32_t va = (v0 << 16) + dv_long * (y1 - y0);
        int32_t vb = v1 << 16;
        int y_start = y1 < 0 ? 0 : y1;
        if (y1 < 0) {
            xa += dx_long * (-y1); xb += dx_short * (-y1);
            ua += du_long * (-y1); ub += du_short * (-y1);
            va += dv_long * (-y1); vb += dv_short * (-y1);
        }
        
        u8 *dst_row = &frame_buffer[y_start * 240];
        for (int y = y_start; y <= y_bot; y++, dst_row += 240) {
            int left = is_right ? (xa >> 16) : (xb >> 16);
            int right = is_right ? (xb >> 16) : (xa >> 16);
            int32_t u_l = is_right ? ua : ub;
            int32_t v_l = is_right ? va : vb;
            int32_t u_r = is_right ? ub : ua;
            int32_t v_r = is_right ? vb : va;
            
            int span = right - left;
            int32_t inv_w = texture_recip(span);
            int32_t du_x = ((int64_t)(u_r - u_l) * inv_w) >> 16;
            int32_t dv_x = ((int64_t)(v_r - v_l) * inv_w) >> 16;
            if (left < 0) {
                u_l += du_x * (-left);
                v_l += dv_x * (-left);
                left = 0;
            }
            if (right >= RENDER_WIDTH) right = RENDER_WIDTH - 1;
            if (right >= left) {
                int32_t curr_u = u_l;
                int32_t curr_v = v_l;
                u8 *dst = dst_row + left;
                const u8 *tex_flat = &tex[0][0];
                for (int x = left; x <= right; x++) {
                    int tu = (curr_u >> 16) & 63;
                    int tv = (curr_v >> 16) & 63;
                    u8 c = tex_flat[(tv << 6) | tu];
                    *dst++ = c ? c : fallback_color;
                    curr_u += du_x;
                    curr_v += dv_x;
                }
            }
            xa += dx_long; xb += dx_short;
            ua += du_long; ub += du_short;
            va += dv_long; vb += dv_short;
        }
    }
}
