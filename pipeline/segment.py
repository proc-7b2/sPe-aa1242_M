import numpy as np
import trimesh

def segment_r15_components(mesh):
    """
    Advanced R15 Segmenter: Uses spatial clustering and local-only slicing
    to prevent cross-contamination between body parts.
    """
    # 1. Basic Setup
    bounds = mesh.bounds
    center_x = (bounds[0][0] + bounds[1][0]) / 2
    total_height = bounds[1][1] - bounds[0][1]
    total_width = bounds[1][0] - bounds[0][0]
    
    # Thresholds based on your specific 'Chibi' model proportions
    head_height_threshold = bounds[1][1] - (total_height * 0.38) # Big head protection
    hip_line = bounds[0][1] + (total_height * 0.42)
    arm_gap = total_width * 0.18 # Distance from center to start arm-cut

    final_parts = {}

    # --- STEP 1: ISOLATE THE CENTRAL CORE (HEAD & TORSO) ---
    # We take a vertical 'slice' of the middle of the character first.
    core_mask = trimesh.intersections.slice_mesh_plane(mesh, [1, 0, 0], [center_x - arm_gap, 0, 0], cap=True)
    core_mask = trimesh.intersections.slice_mesh_plane(core_mask, [-1, 0, 0], [center_x + arm_gap, 0, 0], cap=True)

    # --- STEP 2: SEGMENT HEAD vs TORSO ---
    final_parts["Head"] = trimesh.intersections.slice_mesh_plane(core_mask, [0, 1, 0], [0, head_height_threshold, 0], cap=True)
    
    torso_full = trimesh.intersections.slice_mesh_plane(core_mask, [0, -1, 0], [0, head_height_threshold, 0], cap=True)
    torso_full = trimesh.intersections.slice_mesh_plane(torso_full, [0, 1, 0], [0, hip_line, 0], cap=True)
    
    # Split Torso into Upper/Lower
    t_bounds = torso_full.bounds
    t_mid = (t_bounds[0][1] + t_bounds[1][1]) / 2
    final_parts["UpperTorso"] = trimesh.intersections.slice_mesh_plane(torso_full, [0, 1, 0], [0, t_mid, 0], cap=True)
    final_parts["LowerTorso"] = trimesh.intersections.slice_mesh_plane(torso_full, [0, -1, 0], [0, t_mid, 0], cap=True)

    # --- STEP 3: ISOLATE & SLICE ARMS (LOCAL ONLY) ---
    # We slice the arms from the ORIGINAL mesh but filter by X-position 
    # so we don't accidentally grab the core again.
    left_arm_raw = trimesh.intersections.slice_mesh_plane(mesh, [-1, 0, 0], [center_x - arm_gap, 0, 0], cap=True)
    # Filter out anything too high (head) or too low (legs) to be an arm
    left_arm_raw = trimesh.intersections.slice_mesh_plane(left_arm_raw, [0, -1, 0], [0, head_height_threshold, 0], cap=True)
    left_arm_raw = trimesh.intersections.slice_mesh_plane(left_arm_raw, [0, 1, 0], [0, hip_line, 0], cap=True)
    
    final_parts["LeftUpperArm"], final_parts["LeftLowerArm"], final_parts["LeftHand"] = slice_limb_local(left_arm_raw)

    right_arm_raw = trimesh.intersections.slice_mesh_plane(mesh, [1, 0, 0], [center_x + arm_gap, 0, 0], cap=True)
    right_arm_raw = trimesh.intersections.slice_mesh_plane(right_arm_raw, [0, -1, 0], [0, head_height_threshold, 0], cap=True)
    right_arm_raw = trimesh.intersections.slice_mesh_plane(right_arm_raw, [0, 1, 0], [0, hip_line, 0], cap=True)
    
    final_parts["RightUpperArm"], final_parts["RightLowerArm"], final_parts["RightHand"] = slice_limb_local(right_arm_raw)

    # --- STEP 4: ISOLATE & SLICE LEGS ---
    legs_raw = trimesh.intersections.slice_mesh_plane(mesh, [0, -1, 0], [0, hip_line, 0], cap=True)
    
    left_leg_raw = trimesh.intersections.slice_mesh_plane(legs_raw, [-1, 0, 0], [center_x, 0, 0], cap=True)
    final_parts["LeftUpperLeg"], final_parts["LeftLowerLeg"], final_parts["LeftFoot"] = slice_limb_local(left_leg_raw)

    right_leg_raw = trimesh.intersections.slice_mesh_plane(legs_raw, [1, 0, 0], [center_x, 0, 0], cap=True)
    final_parts["RightUpperLeg"], final_parts["RightLowerLeg"], final_parts["RightFoot"] = slice_limb_local(right_leg_raw)

    return final_parts

def slice_limb_local(limb_mesh):
    """Helper to slice a limb into 3 even segments vertically."""
    if limb_mesh.is_empty or len(limb_mesh.vertices) < 4:
        return [trimesh.Trimesh()] * 3
    
    b = limb_mesh.bounds
    h = b[1][1] - b[0][1]
    c1 = b[1][1] - (h * 0.35)
    c2 = b[1][1] - (h * 0.70)
    
    p1 = trimesh.intersections.slice_mesh_plane(limb_mesh, [0, 1, 0], [0, c1, 0], cap=True)
    mid = trimesh.intersections.slice_mesh_plane(limb_mesh, [0, -1, 0], [0, c1, 0], cap=True)
    p2 = trimesh.intersections.slice_mesh_plane(mid, [0, 1, 0], [0, c2, 0], cap=True)
    p3 = trimesh.intersections.slice_mesh_plane(mid, [0, -1, 0], [0, c2, 0], cap=True)
    
    return [p1, p2, p3]
