import sys
from PIL import Image

# GBA uses 5-bit color (0-31), so 8-bit color is scaled by 31/255
def rgb5_to_rgb8(r, g, b):
    return (int((r * 255) / 31), int((g * 255) / 31), int((b * 255) / 31))

def main():
    # Construct the exact palette GBA uses
    base_colors = [
        (31, 31, 31), # White/Gray
        (31, 0,  0),  # Red
        (0,  31, 0),  # Green
        (0,  10, 31), # Blue
        (31, 31, 0),  # Yellow
        (0,  31, 31), # Cyan
        (31, 16, 0),  # Orange
        (25, 0,  25)  # Purple
    ]

    palette_rgb = []
    
    # 0 to 127
    for c in range(8):
        for s in range(16):
            r = (base_colors[c][0] * s) // 15
            g = (base_colors[c][1] * s) // 15
            b = (base_colors[c][2] * s) // 15
            palette_rgb.extend(rgb5_to_rgb8(r, g, b))
            
    # 128 to 137 (system colors)
    system_colors = [
        (1, 1, 5),
        (0, 31, 16),
        (31, 31, 31),
        (31, 24, 0),
        (0, 0, 0),
        (0, 26, 12),
        (4, 22, 4),
        (6, 28, 6),
        (8, 18, 2),
        (31, 31, 0)
    ]
    
    for r, g, b in system_colors:
        palette_rgb.extend(rgb5_to_rgb8(r, g, b))
        
    # Fill the rest with black (up to 256)
    while len(palette_rgb) < 256 * 3:
        palette_rgb.extend((0, 0, 0))

    # Create a palette image to use with PIL
    pal_img = Image.new("P", (16, 16))
    pal_img.putpalette(palette_rgb)

    # Open cover art
    try:
        img = Image.open("menu.webp")
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Resize to exactly 240x160 (GBA screen)
    img = img.resize((240, 160), Image.Resampling.LANCZOS)
    
    # Convert to RGB just in case
    img = img.convert("RGB")

    # Quantize using our palette image with dithering
    img_quant = img.quantize(palette=pal_img, dither=Image.Dither.FLOYDSTEINBERG)

    # Export to C header
    pixels = list(img_quant.getdata())
    
    with open("menu_art.h", "w") as f:
        f.write("#ifndef MENU_ART_H\n")
        f.write("#define MENU_ART_H\n\n")
        f.write("#include <tonc.h>\n\n")
        f.write("const u8 menu_art_data[38400] __attribute__((aligned(4))) = {\n")
        
        for i in range(0, len(pixels), 16):
            chunk = pixels[i:i+16]
            hex_chunk = ", ".join(f"0x{p:02X}" for p in chunk)
            f.write(f"    {hex_chunk},\n")
            
        f.write("};\n\n")
        f.write("#endif // MENU_ART_H\n")
        
    print("Successfully generated menu_art.h!")

if __name__ == "__main__":
    main()
