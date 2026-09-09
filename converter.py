#!/usr/bin/env python3
"""
GBA 3D Engine Mesh Converter
Converts STL and Blender meshes to 3D engine C headers in 8.8 fixed-point format.
Supports standalone STL decimation (vertex clustering) and Blender decimate integration.
"""

import os
import sys
import math
import struct
import argparse

# Check if running inside Blender
try:
    import bpy
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

class STLParser:
    @staticmethod
    def is_binary_stl(filepath):
        if not os.path.exists(filepath):
            return False
        # Read first 80 bytes
        with open(filepath, 'rb') as f:
            header = f.read(80)
            if len(header) < 80:
                return False
            
            # Check for binary indicator:
            # File size should be exactly: 84 + 50 * num_triangles
            try:
                num_triangles_bytes = f.read(4)
                if len(num_triangles_bytes) < 4:
                    return False
                num_triangles = struct.unpack('<I', num_triangles_bytes)[0]
                expected_size = 84 + 50 * num_triangles
                actual_size = os.path.getsize(filepath)
                return expected_size == actual_size
            except Exception:
                return False

    @staticmethod
    def parse_binary(filepath):
        vertices = []
        faces = []
        with open(filepath, 'rb') as f:
            f.read(80) # Skip header
            num_triangles = struct.unpack('<I', f.read(4))[0]
            
            for i in range(num_triangles):
                # Each facet is 50 bytes:
                # 3 floats normal (12 bytes)
                # 3 floats * 3 vertices (36 bytes)
                # 2 bytes attribute count (2 bytes)
                data = f.read(50)
                if len(data) < 50:
                    break
                floats = struct.unpack('<12f', data[:48])
                v1 = (floats[3], floats[4], floats[5])
                v2 = (floats[6], floats[7], floats[8])
                v3 = (floats[9], floats[10], floats[11])
                
                idx = len(vertices)
                vertices.extend([v1, v2, v3])
                faces.append((idx, idx+1, idx+2))
                
        return vertices, faces

    @staticmethod
    def parse_ascii(filepath):
        vertices = []
        faces = []
        current_tri = []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0] == 'vertex':
                    try:
                        x = float(parts[1])
                        y = float(parts[2])
                        z = float(parts[3])
                        current_tri.append((x, y, z))
                        if len(current_tri) == 3:
                            idx = len(vertices)
                            vertices.extend(current_tri)
                            faces.append((idx, idx+1, idx+2))
                            current_tri = []
                    except (ValueError, IndexError):
                        pass
        return vertices, faces

    @classmethod
    def load(cls, filepath):
        if cls.is_binary_stl(filepath):
            print(f"Parsing Binary STL: {filepath}")
            return cls.parse_binary(filepath)
        else:
            print(f"Parsing ASCII STL: {filepath}")
            return cls.parse_ascii(filepath)


def simplify_mesh_clustering(vertices, faces, grid_resolution):
    """
    Simplifies mesh using Vertex Clustering (pure Python, zero dependencies).
    Groups vertices in a bounding grid, merges them, and removes degenerate/duplicate faces.
    """
    if not vertices:
        return [], []
        
    print(f"Simplifying mesh: Original Vertices={len(vertices)}, Faces={len(faces)}")
    
    # 1. Bounding Box
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    
    dx = max_x - min_x
    dy = max_y - min_y
    dz = max_z - min_z
    
    max_dim = max(dx, dy, dz)
    cell_size = max_dim / grid_resolution if max_dim > 0 else 1.0
    
    # 2. Map vertices to grid cells and gather centroids
    grid_cells = {} # key -> list of vertex coordinates
    vertex_to_cell_key = {} # vertex_index -> key
    
    for i, v in enumerate(vertices):
        # Calculate cell coordinates
        gx = int(math.floor((v[0] - min_x) / cell_size)) if cell_size > 0 else 0
        gy = int(math.floor((v[1] - min_y) / cell_size)) if cell_size > 0 else 0
        gz = int(math.floor((v[2] - min_z) / cell_size)) if cell_size > 0 else 0
        
        key = (gx, gy, gz)
        vertex_to_cell_key[i] = key
        
        if key not in grid_cells:
            grid_cells[key] = []
        grid_cells[key].append(v)
        
    # Calculate cell centroids
    cell_centroids = {}
    new_vertices = []
    cell_key_to_new_index = {}
    
    for key, verts in grid_cells.items():
        cx = sum(v[0] for v in verts) / len(verts)
        cy = sum(v[1] for v in verts) / len(verts)
        cz = sum(v[2] for v in verts) / len(verts)
        
        new_index = len(new_vertices)
        new_vertices.append((cx, cy, cz))
        cell_key_to_new_index[key] = new_index
        
    # 3. Re-map faces
    new_faces = []
    seen_faces = set()
    
    for f in faces:
        # Get new index of each vertex in the triangle
        n1 = cell_key_to_new_index[vertex_to_cell_key[f[0]]]
        n2 = cell_key_to_new_index[vertex_to_cell_key[f[1]]]
        n3 = cell_key_to_new_index[vertex_to_cell_key[f[2]]]
        
        # Remove degenerate triangles (two or more vertices are identical)
        if n1 == n2 or n2 == n3 or n3 == n1:
            continue
            
        # Remove duplicate triangles (regardless of winding direction order)
        face_sig = tuple(sorted((n1, n2, n3)))
        if face_sig in seen_faces:
            continue
        
        seen_faces.add(face_sig)
        new_faces.append((n1, n2, n3))
        
    print(f"Simplified result: Vertices={len(new_vertices)}, Faces={len(new_faces)}")
    return new_vertices, new_faces


def process_and_export_c(vertices, faces, mesh_name, out_file, scale_target=50.0, base_color=6):
    """
    Centers, scales, and exports mesh vertices and faces to GBA C source format.
    """
    if not vertices:
        print("Error: No vertices to export.")
        return
        
    # 1. Center vertices
    cx = sum(v[0] for v in vertices) / len(vertices)
    cy = sum(v[1] for v in vertices) / len(vertices)
    cz = sum(v[2] for v in vertices) / len(vertices)
    
    centered_verts = []
    for v in vertices:
        centered_verts.append((v[0] - cx, v[1] - cy, v[2] - cz))
        
    # 2. Scale vertices to target bounding size
    max_dist = 0.0
    for v in centered_verts:
        d = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
        if d > max_dist:
            max_dist = d
            
    scale_factor = scale_target / max_dist if max_dist > 0 else 1.0
    
    scaled_verts = []
    for v in centered_verts:
        scaled_verts.append((v[0] * scale_factor, v[1] * scale_factor, v[2] * scale_factor))
        
    # 3. Convert to 8.8 fixed-point format
    fixed_verts = []
    for v in scaled_verts:
        fixed_verts.append((
            int(round(v[0] * 256)),
            int(round(v[1] * 256)),
            int(round(v[2] * 256))
        ))
        
    # Write C format
    c_name = mesh_name.lower().replace(" ", "_").replace("-", "_")
    
    output = []
    output.append(f"// Generated 3D Mesh code for GBA Engine: {mesh_name}")
    output.append('#include "engine3d.h"\n')
    
    # Vertices array
    output.append(f"static const Vector3 {c_name}_vertices[{len(fixed_verts)}] = {{")
    for v in fixed_verts:
        output.append(f"    {{ {v[0]}, {v[1]}, {v[2]} }},")
    output.append("};\n")
    
    # Faces array
    output.append(f"static const Face {c_name}_faces[{len(faces)}] = {{")
    for f in faces:
        output.append(f"    {{ {f[0]}, {f[1]}, {f[2]}, {base_color} }},")
    output.append("};\n")
    
    # Mesh definition
    output.append(f"const Mesh {c_name}_mesh = {{")
    output.append(f'    "{mesh_name.upper()}",')
    output.append(f"    {len(fixed_verts)},")
    output.append(f"    {len(faces)},")
    output.append(f"    {c_name}_vertices,")
    output.append(f"    {c_name}_faces")
    output.append("};")
    
    with open(out_file, 'w') as f:
        f.write("\n".join(output) + "\n")
        
    print(f"Successfully generated GBA mesh file: {out_file}")


def blender_export(mesh_name, decimate_ratio, out_file, scale_target, base_color):
    """
    Blender integrated exporter. Evaluates the active mesh object,
    decimates it, and exports it.
    """
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        # Fallback: grab the first mesh object in the scene
        mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        if not mesh_objs:
            print("Error: No mesh objects found in Blender scene.")
            sys.exit(1)
        obj = mesh_objs[0]
        
    print(f"Blender: Exporting mesh '{obj.name}'...")
    
    # Set active object
    bpy.context.view_layer.objects.active = obj
    
    # Duplicate object to avoid modifying original
    bpy.ops.object.duplicate(linked=False)
    dup_obj = bpy.context.active_object
    
    # Add decimate modifier
    if decimate_ratio < 1.0:
        dec_mod = dup_obj.modifiers.new(name="Decimate", type='DECIMATE')
        dec_mod.ratio = decimate_ratio
        bpy.ops.object.modifier_apply(modifier="Decimate")
        
    # Get mesh data
    mesh = dup_obj.data
    vertices = [tuple(v.co) for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons if len(p.vertices) == 3]
    
    # Handle quads by splitting them to triangles
    for p in mesh.polygons:
        if len(p.vertices) == 4:
            faces.append((p.vertices[0], p.vertices[1], p.vertices[2]))
            faces.append((p.vertices[2], p.vertices[3], p.vertices[0]))
            
    # Delete temporary duplicate
    bpy.ops.object.delete()
    
    process_and_export_c(vertices, faces, mesh_name, out_file, scale_target, base_color)


def main():
    if IN_BLENDER:
        # running inside Blender
        # Blender passes args after '--' to python
        argv = sys.argv
        if "--" in argv:
            args_list = argv[argv.index("--") + 1:]
        else:
            args_list = []
    else:
        args_list = sys.argv[1:]
        
    parser = argparse.ArgumentParser(description="Convert 3D meshes to GBA C source format.")
    parser.add_argument("input", nargs="?", help="Input STL or Blend file (ignored in Blender GUI mode)")
    parser.add_argument("-o", "--output", required=True, help="Output C header/source file (.c/.h)")
    parser.add_argument("-n", "--name", default="converted_mesh", help="Name of the Mesh in C code")
    parser.add_argument("-r", "--ratio", type=float, default=0.3, help="Blender Decimate ratio (0.0 to 1.0) / Standalone clustering ratio index")
    parser.add_argument("-g", "--grid", type=int, default=16, help="Grid size for vertex clustering decimation (standalone mode)")
    parser.add_argument("-s", "--scale", type=float, default=50.0, help="Output size scale bound (default: 50.0)")
    parser.add_argument("-c", "--color", type=int, default=6, help="Palette base color index (0-7, default: 6 - Orange)")
    
    args = parser.parse_args(args_list)
    
    if IN_BLENDER:
        blender_export(args.name, args.ratio, args.output, args.scale, args.color)
    else:
        if not args.input:
            print("Error: Input STL file required in standalone mode.")
            parser.print_help()
            sys.exit(1)
            
        if not os.path.exists(args.input):
            print(f"Error: Input file '{args.input}' not found.")
            sys.exit(1)
            
        vertices, faces = STLParser.load(args.input)
        
        # Simplify mesh if grid size is positive and ratio < 1.0
        if args.ratio < 1.0 or args.grid != 0:
            vertices, faces = simplify_mesh_clustering(vertices, faces, args.grid)
            
        process_and_export_c(vertices, faces, args.name, args.output, args.scale, args.color)

if __name__ == "__main__":
    main()
