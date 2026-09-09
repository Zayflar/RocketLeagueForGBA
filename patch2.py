import os

with open("models.c", "r") as f:
    code = f.read()

# Generate wheel verts
wheel_centers = [
    (-15, -4, 10),
    ( 15, -4, 10),
    (-15, -4, -10),
    ( 15, -4, -10)
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
vert_str = vert_str.rstrip(",\n") + "\n"

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
face_str = face_str.rstrip(",\n") + "\n"

# 1. Update car_vertices
old_verts_end = "{ -INT_TO_FP(9),  INT_TO_FP(15), -INT_TO_FP(15) }  // 29 left-back"
new_verts_end = "{ -INT_TO_FP(9),  INT_TO_FP(15), -INT_TO_FP(15) }, // 29 left-back\n" + vert_str
code = code.replace("static const Vector3 car_vertices[30] = {", "static const Vector3 car_vertices[62] = {")
code = code.replace(old_verts_end, new_verts_end)

# 2. Update opp_car_vertices
code = code.replace("static const Vector3 opp_car_vertices[30] = {", "static const Vector3 opp_car_vertices[62] = {")
# opp_car_verts also has the same end line. Since we already replaced it in car_vertices, let's just make sure we replace it globally if there are multiple.
# Wait, replace() replaces all occurrences. So both car_verts and opp_car_verts are patched!

# 3. Update car_faces
old_wheels = """    // 4 WHEELS - Black color = 132
    { 11, 10, 12, 132, {{0,0}, {0,0}, {0,0}} }, { 11, 12, 13, 132, {{0,0}, {0,0}, {0,0}} },
    { 14, 15, 16, 132, {{0,0}, {0,0}, {0,0}} }, { 15, 17, 16, 132, {{0,0}, {0,0}, {0,0}} },
    { 19, 18, 20, 132, {{0,0}, {0,0}, {0,0}} }, { 19, 20, 21, 132, {{0,0}, {0,0}, {0,0}} },
    { 22, 23, 24, 132, {{0,0}, {0,0}, {0,0}} }, { 23, 25, 24, 132, {{0,0}, {0,0}, {0,0}} },"""
new_wheels = "    // 4 WHEELS - Black color = 132\n" + face_str + "    // Dummy flat wheels to keep indices 10-25 valid\n" + old_wheels
# Wait, if we keep old wheels, it wastes 8 faces (which is fine, they are inside the new wheels!).
# But we changed the size! car_faces was 28. If we append 48 faces, it's 28 + 48 = 76.
# If we replace old_wheels, it's 28 - 8 + 48 = 68.
# But wait, indices 10-25 are used by old wheels. But they are not used by the chassis! So we CAN replace them!
# Ah, I don't need dummy wheels. The chassis uses vertices 0-9 and 26-29.
# The old wheel vertices are 10-25. Since the faces for chassis don't reference 10-25, we don't need dummy faces!
# BUT we DO need dummy vertices at 10-25 because the spoiler references 26-29!
# So replacing old_wheels with new_wheels is fine, but old_wheels are at the TOP of car_faces. 
# Let's just append the new wheel faces at the end of car_faces.

old_faces_end_car = "{ 27, 26, 29, 3, {{0,0},{0,0},{0,0}} }   // Spoiler back"
new_faces_end_car = "{ 27, 26, 29, 3, {{0,0},{0,0},{0,0}} },   // Spoiler back\n" + face_str
code = code.replace("static const Face car_faces[28] = {", "static const Face car_faces[68] = {")
code = code.replace(old_wheels, "    // Old wheels removed")
code = code.replace(old_faces_end_car, new_faces_end_car)

old_faces_end_opp = "{ 27, 26, 29, 6, {{0,0},{0,0},{0,0}} }   // Spoiler back"
new_faces_end_opp = "{ 27, 26, 29, 6, {{0,0},{0,0},{0,0}} },   // Spoiler back\n" + face_str
code = code.replace("static const Face opp_car_faces[30] = {", "static const Face opp_car_faces[70] = {")
code = code.replace(old_faces_end_opp, new_faces_end_opp)

# 4. Update Mesh sizes
code = code.replace("    30,\n    28,\n    car_vertices", "    62,\n    68,\n    car_vertices")
code = code.replace("    30,\n    30,\n    opp_car_vertices", "    62,\n    70,\n    opp_car_vertices")

with open("models.c", "w") as f:
    f.write(code)

print("Patching done!")
