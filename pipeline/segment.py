import numpy as np
import trimesh

# R15 Part Names
R15_NAMES = [
    "Head", "UpperTorso", "LowerTorso",
    "LeftUpperArm", "LeftLowerArm", "LeftHand",
    "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
    "RightUpperLeg", "RightLowerLeg", "RightFoot"
]

def slice_limb(limb_mesh, is_leg=False):
    """Sub-slices an R6 limb into Upper, Lower, and End (Hand/Foot) parts."""
    if limb_mesh.is_empty:
        return [trimesh.Trimesh()] * 3
    
    l_min, l_max = limb_mesh.bounds[0][1], limb_mesh.bounds[1][1]
    l_height = l_max - l_min
    
    # Ratios for sub-limb slicing (Approximate for R15)
    # Upper: Top 40%, Lower: Middle 40%, Foot/Hand: Bottom 20%
    cut1 = l_max - (l_height * 0.4)
    cut2 = l_max - (l_height * 0.8)
    
    upper = trimesh.intersections.slice_mesh_plane(limb_mesh, [0, 1, 0], [0, cut1, 0], cap=True)
    mid_section = trimesh.intersections.slice_mesh_plane(limb_mesh, [0, -1, 0], [0, cut1, 0], cap=True)
    lower = trimesh.intersections.slice_mesh_plane(mid_section, [0, 1, 0], [0, cut2, 0], cap=True)
    end_part = trimesh.intersections.slice_mesh_plane(mid_section, [0, -1, 0], [0, cut2, 0], cap=True)
    
    return [upper, lower, end_part]

def segment_r15_components(mesh, head_ratio=0.35, torso_ratio=0.5):
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    total_width = bounds_max[0] - bounds_min[0]
    center_x = (bounds_min[0] + bounds_max[0]) / 2

    # 1️⃣ DYNAMIC RATIO ADJUSTMENTS
    # Your head is huge, so we need a larger head_ratio to capture just the head.
    head_y = bounds_max[1] - (total_height * head_ratio)
    
    # We lower the hip line to give the torso more "breathing room"
    hip_y = bounds_min[1] + (total_height * 0.35) 

    # We widen the arm cut to make sure we don't grab the "shoulders" 
    # of the torso or the "thighs" of the legs.
    arm_x_offset = total_width * 0.22 

    final_parts = {}

    # 2️⃣ STEP 1: REMOVE ARMS FIRST (Protects hands from leg cuts)
    left_arm_raw = trimesh.intersections.slice_mesh_plane(
        mesh, [-1, 0, 0], [center_x - arm_x_offset, 0, 0], cap=True)
    right_arm_raw = trimesh.intersections.slice_mesh_plane(
        mesh, [1, 0, 0], [center_x + arm_x_offset, 0, 0], cap=True)
    
    final_parts["LeftUpperArm"], final_parts["LeftLowerArm"], final_parts["LeftHand"] = slice_limb(left_arm_raw)
    final_parts["RightUpperArm"], final_parts["RightLowerArm"], final_parts["RightHand"] = slice_limb(right_arm_raw)

    # 3️⃣ STEP 2: ISOLATE THE CORE (Head + Torso + Legs)
    # This core no longer has arms, so slicing Y is now safe!
    core = trimesh.intersections.slice_mesh_plane(mesh, [1, 0, 0], [center_x - arm_x_offset, 0, 0], cap=True)
    core = trimesh.intersections.slice_mesh_plane(core, [-1, 0, 0], [center_x + arm_x_offset, 0, 0], cap=True)

    # 4️⃣ STEP 3: SLICE CORE BY HEIGHT
    # Head
    final_parts["Head"] = trimesh.intersections.slice_mesh_plane(core, [0, 1, 0], [0, head_y, 0], cap=True)

    # Legs
    legs_band = trimesh.intersections.slice_mesh_plane(core, [0, -1, 0], [0, hip_y, 0], cap=True)
    final_parts["LeftUpperLeg"], final_parts["LeftLowerLeg"], final_parts["LeftFoot"] = slice_limb(
        trimesh.intersections.slice_mesh_plane(legs_band, [-1, 0, 0], [center_x, 0, 0], cap=True)
    )
    final_parts["RightUpperLeg"], final_parts["RightLowerLeg"], final_parts["RightFoot"] = slice_limb(
        trimesh.intersections.slice_mesh_plane(legs_band, [1, 0, 0], [center_x, 0, 0], cap=True)
    )

    # Torso (The remainder of the core)
    torso_full = trimesh.intersections.slice_mesh_plane(core, [0, -1, 0], [0, head_y, 0], cap=True)
    torso_full = trimesh.intersections.slice_mesh_plane(torso_full, [0, 1, 0], [0, hip_y, 0], cap=True)
    
    t_min, t_max = torso_full.bounds[0][1], torso_full.bounds[1][1]
    t_split_y = t_min + (t_max - t_min) * 0.5
    final_parts["UpperTorso"] = trimesh.intersections.slice_mesh_plane(torso_full, [0, 1, 0], [0, t_split_y, 0], cap=True)
    final_parts["LowerTorso"] = trimesh.intersections.slice_mesh_plane(torso_full, [0, -1, 0], [0, t_split_y, 0], cap=True)

    return final_parts
