import sys
import math

print("Decoding JPEG... this may take a few minutes...")
sys.path.append("python-jpeg-decoder")
import jpeg

# jpeg.image_rgb is a 2D array [y][x] of (r, g, b) tuples.
# image dimensions are jpeg.sof.samples_per_line, jpeg.sof.num_lines

src_w = jpeg.sof.samples_per_line
src_h = jpeg.sof.num_lines
pixels = jpeg.image_rgb

print(f"Decoded image {src_w}x{src_h}")

# Nearest neighbor resize to 240x160
dest_w, dest_h = 240, 160
resized = []
for y in range(dest_h):
    src_y = int(y * src_h / dest_h)
    row = []
    for x in range(dest_w):
        src_x = int(x * src_w / dest_w)
        row.append(pixels[src_y][src_x])
    resized.append(row)

print("Resized to 240x160")

# Setup Palette
baseColors = [
    (31, 31, 31), (31, 0, 0), (0, 31, 0), (0, 10, 31),
    (31, 31, 0), (0, 31, 31), (31, 16, 0), (25, 0, 25)
]

palette = []
for c in range(8):
    for s in range(16):
        r = (baseColors[c][0] * s) // 15
        g = (baseColors[c][1] * s) // 15
        b = (baseColors[c][2] * s) // 15
        palette.append((r*255//31, g*255//31, b*255//31))

sysColors = [
    (1,1,5), (0,31,16), (31,31,31), (31,24,0), (0,0,0),
    (0,26,12), (4,22,4), (6,28,6), (8,18,2), (31,31,0)
]
for c in sysColors:
    palette.append((c[0]*255//31, c[1]*255//31, c[2]*255//31))

while len(palette) < 256:
    palette.append((0,0,0))

def closest_color(r, g, b):
    min_d = float('inf')
    idx = 0
    for i, p in enumerate(palette):
        d = (r - p[0])**2 + (g - p[1])**2 + (b - p[2])**2
        if d < min_d:
            min_d = d
            idx = i
    return idx

out_indices = []
print("Quantizing and Dithering...")

# Flatten for dithering
flat_r = [float(p[0]) for row in resized for p in row]
flat_g = [float(p[1]) for row in resized for p in row]
flat_b = [float(p[2]) for row in resized for p in row]

for y in range(dest_h):
    for x in range(dest_w):
        i = y * dest_w + x
        r = flat_r[i]
        g = flat_g[i]
        b = flat_b[i]
        
        idx = closest_color(r, g, b)
        out_indices.append(idx)
        
        nr, ng, nb = palette[idx]
        errR, errG, errB = r - nr, g - ng, b - nb
        
        def distribute(dx, dy, factor):
            nx, ny = x + dx, y + dy
            if 0 <= nx < dest_w and ny < dest_h:
                ni = ny * dest_w + nx
                flat_r[ni] += errR * factor
                flat_g[ni] += errG * factor
                flat_b[ni] += errB * factor
                
        distribute(1, 0, 7/16)
        distribute(-1, 1, 3/16)
        distribute(0, 1, 5/16)
        distribute(1, 1, 1/16)

print("Writing to coverart.h")
with open("coverart.h", "w") as f:
    f.write("#ifndef COVERART_H\n#define COVERART_H\n\n#include <tonc.h>\n\n")
    f.write("const u8 coverart_data[38400] __attribute__((aligned(4))) = {\n")
    for i in range(0, len(out_indices), 16):
        chunk = out_indices[i:i+16]
        hex_chunk = ", ".join(f"0x{p:02X}" for p in chunk)
        f.write(f"    {hex_chunk},\n")
    f.write("};\n\n#endif\n")

print("DONE!")
