#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TARGET_W 240
#define TARGET_H 160

typedef struct {
    unsigned char r, g, b;
} Color;

int color_dist(Color a, Color b) {
    int dr = a.r - b.r;
    int dg = a.g - b.g;
    int db = a.b - b.b;
    return dr*dr + dg*dg + db*db;
}

int main(int argc, char **argv) {
    int w, h, channels;
    unsigned char *img = stbi_load(argv[1], &w, &h, &channels, 3);
    if (!img) return 1;

    unsigned char *scaled = malloc(TARGET_W * TARGET_H * 3);
    for (int y = 0; y < TARGET_H; y++) {
        for (int x = 0; x < TARGET_W; x++) {
            int src_x = x * w / TARGET_W;
            int src_y = y * h / TARGET_H;
            scaled[(y * TARGET_W + x) * 3 + 0] = img[(src_y * w + src_x) * 3 + 0];
            scaled[(y * TARGET_W + x) * 3 + 1] = img[(src_y * w + src_x) * 3 + 1];
            scaled[(y * TARGET_W + x) * 3 + 2] = img[(src_y * w + src_x) * 3 + 2];
        }
    }

    // Very simple 6-6-6 palette generation (216 colors)
    Color palette[256];
    int pal_count = 0;
    for(int r=0; r<6; r++) {
        for(int g=0; g<6; g++) {
            for(int b=0; b<6; b++) {
                palette[pal_count].r = r * 51;
                palette[pal_count].g = g * 51;
                palette[pal_count].b = b * 51;
                pal_count++;
            }
        }
    }
    // Fill rest with black
    while(pal_count < 256) {
        palette[pal_count].r = 0;
        palette[pal_count].g = 0;
        palette[pal_count].b = 0;
        pal_count++;
    }

    FILE *f = fopen("title_bg.h", "w");
    fprintf(f, "const unsigned short title_pal[256] = {\n");
    for (int i = 0; i < 256; i++) {
        int r = palette[i].r >> 3;
        int g = palette[i].g >> 3;
        int b = palette[i].b >> 3;
        unsigned short rgb5 = r | (g << 5) | (b << 10);
        fprintf(f, "0x%04x, ", rgb5);
    }
    fprintf(f, "\n};\n");

    fprintf(f, "const unsigned char title_bitmap[%d] = {\n", TARGET_W * TARGET_H);
    for (int i = 0; i < TARGET_W * TARGET_H; i++) {
        Color c = { scaled[i*3], scaled[i*3+1], scaled[i*3+2] };
        int best_idx = 0;
        int best_dist = 9999999;
        for (int p = 0; p < 216; p++) {
            int dist = color_dist(c, palette[p]);
            if (dist < best_dist) {
                best_dist = dist;
                best_idx = p;
            }
        }
        fprintf(f, "%d,", best_idx);
        if ((i + 1) % 30 == 0) fprintf(f, "\n");
    }
    fprintf(f, "\n};\n");

    fclose(f);
    return 0;
}
