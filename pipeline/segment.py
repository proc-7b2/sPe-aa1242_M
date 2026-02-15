def repair_mesh_part(mesh):
    """
    CLEANUP & HOLE FIX:
    - Removes duplicate vertices (doubles)
    - Fills holes
    - Decimates to simplify geometry (keeps UVs)
    """
    if mesh.is_empty:
        return mesh
    
    # 1. Remove Doubles (Small distance to keep detail)
    # This is the trimesh equivalent of your Blender remove_doubles
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    
    # 2. Fill Holes
    mesh.fill_holes()
    
    # 3. Clean up internal/junk geometry
    mesh.remove_infinite_values()
    mesh.remove_unreferenced_vertices()

    # 4. "Safe" Decimation
    # This reduces triangle count while trying to preserve UVs.
    # We only decimate if the mesh is very dense (over 5000 faces per part)
    if len(mesh.faces) > 5000:
        # 0.8 keeps 80% of the geometry.
        mesh = mesh.simplify_quadratic_decimation(int(len(mesh.faces) * 0.8))

    # 5. Shading Fix
    mesh.fix_normals()
    
    return mesh
