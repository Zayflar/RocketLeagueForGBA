import math
phi = (1 + math.sqrt(5)) / 2
verts = [
    [-1,  phi,  0], [ 1,  phi,  0], [-1, -phi,  0], [ 1, -phi,  0],
    [ 0, -1,  phi], [ 0,  1,  phi], [ 0, -1, -phi], [ 0,  1, -phi],
    [ phi,  0, -1], [ phi,  0,  1], [-phi,  0, -1], [-phi,  0,  1]
]
# Normalize
for v in verts:
    l = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    v[0] /= l; v[1] /= l; v[2] /= l

faces = [
    [0,11,5], [0,5,1], [0,1,7], [0,7,10], [0,10,11],
    [1,5,9], [5,11,4], [11,10,2], [10,7,6], [7,1,8],
    [3,9,4], [3,4,2], [3,2,6], [3,6,8], [3,8,9],
    [4,9,5], [2,4,11], [6,2,10], [8,6,7], [9,8,1]
]

# subdivide once
edge_to_v = {}
new_verts = list(verts)
new_faces = []
def get_mid(v1, v2):
    if v2 < v1: v1, v2 = v2, v1
    if (v1,v2) in edge_to_v: return edge_to_v[(v1,v2)]
    p1 = verts[v1]; p2 = verts[v2]
    mid = [(p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2]
    l = math.sqrt(mid[0]**2 + mid[1]**2 + mid[2]**2)
    mid = [mid[0]/l, mid[1]/l, mid[2]/l]
    new_verts.append(mid)
    idx = len(new_verts)-1
    edge_to_v[(v1,v2)] = idx
    return idx

for f in faces:
    a,b,c = f
    ab = get_mid(a,b)
    bc = get_mid(b,c)
    ca = get_mid(c,a)
    new_faces.append([a,ab,ca])
    new_faces.append([b,bc,ab])
    new_faces.append([c,ca,bc])
    new_faces.append([ab,bc,ca])

print(f"#define SPHERE_VCOUNT {len(new_verts)}")
print(f"#define SPHERE_FCOUNT {len(new_faces)}")
print("static Vector3 sphere_verts[SPHERE_VCOUNT] = {")
for v in new_verts:
    x = int(v[0] * 21)
    y = int(v[1] * 21)
    z = int(v[2] * 21)
    print(f"    {{ INT_TO_FP({x}), INT_TO_FP({y}), INT_TO_FP({z}) }},")
print("};")

print("static Face sphere_faces[SPHERE_FCOUNT] = {")
for i, f in enumerate(new_faces):
    color = "0" if (i % 3) == 0 else "7"
    print(f"    {{ {f[0]}, {f[1]}, {f[2]}, {color} }},")
print("};")

