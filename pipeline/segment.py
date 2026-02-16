import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def repair_mesh_part(mesh):
    """Cleans up sliced geometry to ensure it is valid for Roblox/Blender."""
    if mesh.is_empty:
        return mesh
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    mesh.remove_infinite_values()
    mesh.remove_unreferenced_vertices()
    mesh.fill_holes()
    if len(mesh.faces) > 8000:
        target = int(len(mesh.faces) * 0.7)
        mesh = mesh.simplify_quadratic_decimation(target)
    mesh.fix_normals()
    return mesh

def segment_r6_components(mesh, head_height_ratio=0.22, torso_height_ratio=0.45):
    """
    Uses geometric slicing to partition a mesh into 6 R6 parts.
    Calculates volumes and centers for each part.
    """
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    total_width = bounds_max[0] - bounds_min[0]
    center_x = (bounds_min[0] + bounds_max[0]) / 2

    # Define the Y-axis cut lines (Up/Down)
    head_y = bounds_max[1] - (total_height * head_height_ratio)
    leg_y = bounds_min[1] + (total_height * (1 - head_height_ratio - torso_height_ratio))
    
    # Define the X-axis cut lines (Side to Side for arms)
    # Typically arms are the outer 20-25% of the width
    arm_spread = total_width * 0.25
    left_arm_x = center_x - arm_spread
    right_arm_x = center_x + arm_spread

    parts_geometry = {}

    # --- 1. SLICE HEAD ---
    parts_geometry["Head"] = trimesh.intersections.slice_mesh_plane(
        mesh, plane_normal=[0, 1, 0], plane_origin=[0, head_y, 0], cap=True)

    # --- 2. SLICE LEGS ---
    lower_body = trimesh.intersections.slice_mesh_plane(
        mesh, plane_normal=[0, -1, 0], plane_origin=[0, leg_y, 0], cap=True)
    
    parts_geometry["LeftLeg"] = trimesh.intersections.slice_mesh_plane(
        lower_body, plane_normal=[-1, 0, 0], plane_origin=[center_x, 0, 0], cap=True)
    parts_geometry["RightLeg"] = trimesh.intersections.slice_mesh_plane(
        lower_body, plane_normal=[1, 0, 0], plane_origin=[center_x, 0, 0], cap=True)

    # --- 3. SLICE MIDDLE (Torso + Arms) ---
    # First, isolate the middle band
    mid_section = trimesh.intersections.slice_mesh_plane(
        mesh, plane_normal=[0, -1, 0], plane_origin=[0, head_y, 0], cap=True)
    mid_section = trimesh.intersections.slice_mesh_plane(
        mid_section, plane_normal=[0, 1, 0], plane_origin=[0, leg_y, 0], cap=True)

    # Split middle band into LeftArm, Torso, RightArm
    parts_geometry["LeftArm"] = trimesh.intersections.slice_mesh_plane(
        mid_section, plane_normal=[-1, 0, 0], plane_origin=[left_arm_x, 0, 0], cap=True)
    
    parts_geometry["RightArm"] = trimesh.intersections.slice_mesh_plane(
        mid_section, plane_normal=[1, 0, 0], plane_origin=[right_arm_x, 0, 0], cap=True)
    
    # Torso is what remains in the center
    torso_temp = trimesh.intersections.slice_mesh_plane(
        mid_section, plane_normal=[1, 0, 0], plane_origin=[left_arm_x, 0, 0], cap=True)
    parts_geometry["Torso"] = trimesh.intersections.slice_mesh_plane(
        torso_temp, plane_normal=[-1, 0, 0], plane_origin=[right_arm_x, 0, 0], cap=True)

    # --- FINAL CLEANUP & DATA ---
    final_r6 = {}
    for name in R6_NAMES:
        m = parts_geometry.get(name, trimesh.Trimesh())
        repaired = repair_mesh_part(m)
        
        # Add metadata to the mesh object for the pipeline to use
        repaired.metadata['volume'] = repaired.volume
        repaired.metadata['center'] = repaired.centroid.tolist()
        final_r6[name] = repaired
            
    return final_r6
