wheel_centers = [
    (-14, 0, 12),  # FL
    ( 14, 0, 12),  # FR
    (-14, 0, -10), # RL
    ( 14, 0, -10)  # RR
]
w = 4 # half-width
h = 6 # half-height
l = 6 # half-length

verts = []
faces = []

start_v = 30 # current car vertices end at 29
for idx, center in enumerate(wheel_centers):
    cx, cy, cz = center
    # 8 vertices per box
    v_base = start_v + idx * 8
    verts.extend([
        (cx - w, cy - h, cz - l), # 0
        (cx + w, cy - h, cz - l), # 1
        (cx + w, cy + h, cz - l), # 2
        (cx - w, cy + h, cz - l), # 3
        (cx - w, cy - h, cz + l), # 4
        (cx + w, cy - h, cz + l), # 5
        (cx + w, cy + h, cz + l), # 6
        (cx - w, cy + h, cz + l)  # 7
    ])
    # 6 faces per box
    faces.extend([
        (v_base+0, v_base+3, v_base+2), (v_base+0, v_base+2, v_base+1), # back
        (v_base+4, v_base+5, v_base+6), (v_base+4, v_base+6, v_base+7), # front
        (v_base+0, v_base+4, v_base+7), (v_base+0, v_base+7, v_base+3), # left
        (v_base+1, v_base+2, v_base+6), (v_base+1, v_base+6, v_base+5), # right
        (v_base+3, v_base+7, v_base+6), (v_base+3, v_base+6, v_base+2), # top
        (v_base+0, v_base+1, v_base+5), (v_base+0, v_base+5, v_base+4)  # bottom
    ])

print("// --- GENERATED WHEEL VERTS ---")
for v in verts:
    print(f"    {{ INT_TO_FP({v[0]}), INT_TO_FP({v[1]}), INT_TO_FP({v[2]}) }},")

print("// --- GENERATED WHEEL FACES ---")
for i in range(0, len(faces), 2):
    f1 = faces[i]
    f2 = faces[i+1]
    print(f"    {{ {f1[0]}, {f1[1]}, {f1[2]}, 132, {{{{0,0}}, {{0,0}}, {{0,0}}}} }}, {{ {f2[0]}, {f2[1]}, {f2[2]}, 132, {{{{0,0}}, {{0,0}}, {{0,0}}}} }},")

