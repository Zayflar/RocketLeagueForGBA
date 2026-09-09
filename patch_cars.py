import re

with open("models.c", "r") as f:
    code = f.read()

# Generate wheel verts
wheel_centers = [
    (-14, 0, 12),
    ( 14, 0, 12),
    (-14, 0, -10),
    ( 14, 0, -10)
]
w = 3
h = 4
l = 4

verts = []
for center in wheel_centers:
    cx, cy, cz = center
    verts.extend([
        (cx - w, cy - h, cz - l), (cx + w, cy - h, cz - l),
        (cx + w, cy + h, cz - l), (cx - w, cy + h, cz - l),
        (cx - w, cy - h, cz + l), (cx + w, cy - h, cz + l),
        (cx + w, cy + h, cz + l), (cx - w, cy + h, cz + l)
    ])

vert_str = ""
for i in range(0, len(verts), 4):
    v_chunk = verts[i:i+4]
    vert_str += "    " + ", ".join([f"{{ INT_TO_FP({v[0]}), INT_TO_FP({v[1]}), INT_TO_FP({v[2]}) }}" for v in v_chunk]) + ",\n"

# Generate wheel faces
faces = []
start_v = 30
for idx in range(4):
    v_base = start_v + idx * 8
    faces.extend([
        (v_base+0, v_base+3, v_base+2), (v_base+0, v_base+2, v_base+1),
        (v_base+4, v_base+5, v_base+6), (v_base+4, v_base+6, v_base+7),
        (v_base+0, v_base+4, v_base+7), (v_base+0, v_base+7, v_base+3),
        (v_base+1, v_base+2, v_base+6), (v_base+1, v_base+6, v_base+5),
        (v_base+3, v_base+7, v_base+6), (v_base+3, v_base+6, v_base+2),
        (v_base+0, v_base+1, v_base+5), (v_base+0, v_base+5, v_base+4)
    ])

face_str = ""
for i in range(0, len(faces), 2):
    f1 = faces[i]
    f2 = faces[i+1]
    face_str += f"    {{ {f1[0]}, {f1[1]}, {f1[2]}, 132, {{{{0,0}}, {{0,0}}, {{0,0}}}} }}, {{ {f2[0]}, {f2[1]}, {f2[2]}, 132, {{{{0,0}}, {{0,0}}, {{0,0}}}} }},\n"

# Patch models.c: car_vertices
code = re.sub(r'static const Vector3 car_vertices\[30\] = \{', 'static const Vector3 car_vertices[62] = {', code)
code = re.sub(r'(    \{ -INT_TO_FP\(9\),  INT_TO_FP\(15\), -INT_TO_FP\(15\) \}  // 29 left-back\n)\};', r'\1' + vert_str.rstrip(',\n') + '\n};', code)

# Patch models.c: car_faces
code = re.sub(r'static const Face car_faces\[28\] = \{', 'static const Face car_faces[44] = {', code)
code = re.sub(r'    // 4 WHEELS - Black color = 132\n(?:    \{ \d+, \d+, \d+, 132.*\}\},?\n){4}', '    // 4 WHEELS - Black color = 132 (Replaced by 3D boxes below)\n', code)
code = re.sub(r'(    \{ 27, 26, 29, 3, \{\{0,0\},\{0,0\},\{0,0\}\} \}   // Spoiler back\n)\};', r'\1' + face_str.rstrip(',\n') + '\n};', code)

# Update car_mesh size
code = re.sub(r'    30,\n    28,\n    car_vertices', '    62,\n    44,\n    car_vertices', code)

# Patch models.c: opp_car_vertices
code = re.sub(r'static const Vector3 opp_car_vertices\[30\] = \{', 'static const Vector3 opp_car_vertices[62] = {', code)
code = re.sub(r'(    \{ -INT_TO_FP\(9\),  INT_TO_FP\(15\), -INT_TO_FP\(15\) \}  // 29 left-back\n)\};', r'\1' + vert_str.rstrip(',\n') + '\n};', code)

# Patch models.c: opp_car_faces
code = re.sub(r'static const Face opp_car_faces\[30\] = \{', 'static const Face opp_car_faces[46] = {', code)
code = re.sub(r'    // 4 WHEELS - Black color = 132\n(?:    \{ \d+, \d+, \d+, 132.*\}\},?\n){4}', '    // 4 WHEELS - Black color = 132 (Replaced by 3D boxes below)\n', code)
code = re.sub(r'(    \{ 27, 26, 29, 6, \{\{0,0\},\{0,0\},\{0,0\}\} \}   // Spoiler back\n)\};', r'\1' + face_str.rstrip(',\n') + '\n};', code)

# Update opp_car_mesh size
code = re.sub(r'    30,\n    30,\n    opp_car_vertices', '    62,\n    46,\n    opp_car_vertices', code)

with open("models.c", "w") as f:
    f.write(code)

with open("main.c", "r") as f:
    main_code = f.read()

main_code = re.sub(r'static void draw_car_2d_wheels[\s\S]*?\}\n\n/\*', '/*', main_code)
main_code = re.sub(r'                    draw_car_2d_wheels\(player\.pos, player\.yaw\);\n', '', main_code)
main_code = re.sub(r'                    draw_car_2d_wheels\(opponent\.pos, opponent\.yaw\);\n', '', main_code)

with open("main.c", "w") as f:
    f.write(main_code)

print("Patched!")
