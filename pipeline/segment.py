import numpy as np
import trimesh
from scipy.signal import argrelextrema

# R15 Part Names
R15_NAMES = [
    "Head", "UpperTorso", "LowerTorso",
    "LeftUpperArm", "LeftLowerArm", "LeftHand",
    "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
    "RightUpperLeg", "RightLowerLeg", "RightFoot"
]

def repair_mesh_part(mesh):
    """
    Cleans up sliced geometry to ensure it is watertight and valid.
    """
    if mesh.is_empty:
        return mesh
    
    # 1. Merge vertices to close micro-gaps from slicing
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    
    # 2. Basic cleanup
    mesh.remove_infinite_values()
    mesh.remove_unreferenced_vertices()
    
    # 3. Fill holes (Crucial for the 'caps' of the slices)
    # This ensures the cross-sections are solid faces, not hollow rings.
    try:
        mesh.fill_holes()
    except Exception:
        pass # Sometimes complex holes fail, but we proceed
        
    # 4. Recalculate normals for correct lighting
    mesh.fix_normals()
    
    return mesh

def slice_limb(limb_mesh):
    """
    Sub-slices an isolated limb (Arm or Leg) into Upper, Lower, and End (Hand/Foot).
    Uses standard R15 ratios: 40% Upper, 40% Lower, 20% Extremity.
    """
    if limb_mesh.is_empty:
        return [trimesh.Trimesh()] * 3
    
    bounds = limb_mesh.bounds
    y_min, y_max = bounds[0][1], bounds[1][1]
    height = y_max - y_min
    
    # Cut positions
    cut_upper = y_max - (height * 0.40)
    cut_lower = y_max - (height * 0.80)
    
    # 1. Upper Limb
    upper = trimesh.intersections.slice_mesh_plane(
        limb_mesh, [0, 1, 0], [0, cut_upper, 0], cap=True)
    
    # 2. Remainder (Lower + End)
    remainder = trimesh.intersections.slice_mesh_plane(
        limb_mesh, [0, -1, 0], [0, cut_upper, 0], cap=True)
    
    # 3. Lower Limb
    lower = trimesh.intersections.slice_mesh_plane(
        remainder, [0, 1, 0], [0, cut_lower, 0], cap=True)
        
    # 4. End (Hand/Foot)
    end_part = trimesh.intersections.slice_mesh_plane(
        remainder, [0, -1, 0], [0, cut_lower, 0], cap=True)
        
    return [upper, lower, end_part]

def analyze_core_shape(core_mesh):
    """
    Scans the 'Core' mesh (Body without arms) to find the Neck and Waist
    by looking for the thinnest points (local minima in cross-section area).
    """
    bounds = core_mesh.bounds
    z_min, z_max = bounds[0][1], bounds[1][1]
    height_step = (z_max - z_min) / 100.0 # 100 slices for resolution
    
    areas = []
    heights = []

    # 1. Scan loop
    for i in range(100):
        z = z_min + (i * height_step)
        # Get 2D slice
        slice_2d = core_mesh.section(plane_origin=[0, z, 0], plane_normal=[0, 1, 0])
        area = slice_2d.area if slice_2d is not None else 0
        areas.append(area)
        heights.append(z)

    areas = np.array(areas)
    heights = np.array(heights)

    # 2. Find local minima (valleys in the area graph)
    # order=5 means it compares to 5 neighbors on each side (smooths noise)
    minima_indices = argrelextrema(areas, np.less, order=5)[0]
    
    detected_neck = None
    detected_waist = None
    
    # Analyze minima from top to bottom
    for idx in reversed(minima_indices):
        h_ratio = (heights[idx] - z_min) / (z_max - z_min)
        
        # Neck Candidate: High up (Top 20-35%)
        if 0.60 < h_ratio < 0.90 and detected_neck is None:
            detected_neck = heights[idx]
            
        # Waist Candidate: Middle (30-55%)
        # Must be below the neck if we found one
        elif 0.30 < h_ratio < 0.60 and detected_waist is None:
            detected_waist = heights[idx]

    # --- FALLBACKS (If shape is too weird to detect) ---
    if detected_neck is None:
        detected_neck = z_max - ((z_max - z_min) * 0.25) # Default 25% from top
        print(f"  [Warn] Auto-Neck failed. Using default {detected_neck:.2f}")
    else:
        print(f"  [Auto] Neck detected at Y={detected_neck:.2f}")

    if detected_waist is None:
        # Default 45% from bottom (Standard R15 hip line)
        detected_waist = z_min + ((z_max - z_min) * 0.45) 
        print(f"  [Warn] Auto-Waist failed. Using default {detected_waist:.2f}")
    else:
        print(f"  [Auto] Waist detected at Y={detected_waist:.2f}")
        
    return detected_neck, detected_waist

def segment_r15_components(mesh, head_ratio_override=None, torso_ratio_override=None):
    """
    Main pipeline function.
    1. Isolates Arms (Vertical cuts).
    2. Scans the Core (Head/Torso/Legs) for natural joints.
    3. Slices everything into 15 parts.
    """
    bounds_min, bounds_max = mesh.bounds
    total_width = bounds_max[0] - bounds_min[0]
    center_x = (bounds_min[0] + bounds_max[0]) / 2

    parts_geometry = {}

    # ---------------------------------------------------------
    # STEP 1: ISOLATE ARMS FIRST (The "Chibi" Fix)
    # ---------------------------------------------------------
    # We cut the arms off vertically before looking for hips/waist.
    # This prevents hands (which might be low) from being sliced by the leg cut.
    
    # Arm Offset: 18-22% from center is standard for T-pose/A-pose
    arm_x_offset = total_width * 0.20 
    
    # Left Arm Block
    l_arm_raw = trimesh.intersections.slice_mesh_plane(
        mesh, [-1, 0, 0], [center_x - arm_x_offset, 0, 0], cap=True)
    
    # Right Arm Block
    r_arm_raw = trimesh.intersections.slice_mesh_plane(
        mesh, [1, 0, 0], [center_x + arm_x_offset, 0, 0], cap=True)

    # Core Block (Everything else)
    core_mesh = trimesh.intersections.slice_mesh_plane(
        mesh, [1, 0, 0], [center_x - arm_x_offset, 0, 0], cap=True)
    core_mesh = trimesh.intersections.slice_mesh_plane(
        core_mesh, [-1, 0, 0], [center_x + arm_x_offset, 0, 0], cap=True)

    # ---------------------------------------------------------
    # STEP 2: ANALYZE CORE FOR NECK & WAIST
    # ---------------------------------------------------------
    if head_ratio_override and torso_ratio_override:
        # Use manual overrides if provided via CLI
        total_h = bounds_max[1] - bounds_min[1]
        neck_y = bounds_max[1] - (total_h * head_ratio_override)
        waist_y = bounds_min[1] + (total_h * torso_ratio_override)
        print(f"  [Manual] Using fixed ratios. Neck={neck_y:.2f}, Waist={waist_y:.2f}")
    else:
        # Run Smart Scan
        neck_y, waist_y = analyze_core_shape(core_mesh)

    # ---------------------------------------------------------
    # STEP 3: SLICE THE CORE (Head, Torso, Legs)
    # ---------------------------------------------------------
    
    # -- Head --
    parts_geometry["Head"] = trimesh.intersections.slice_mesh_plane(
        core_mesh, [0, 1, 0], [0, neck_y, 0], cap=True)

    # -- Legs Block (Below Waist) --
    legs_block = trimesh.intersections.slice_mesh_plane(
        core_mesh, [0, -1, 0], [0, waist_y, 0], cap=True)
    
    # Split Legs Left/Right
    l_leg_raw = trimesh.intersections.slice_mesh_plane(
        legs_block, [-1, 0, 0], [center_x, 0, 0], cap=True)
    r_leg_raw = trimesh.intersections.slice_mesh_plane(
        legs_block, [1, 0, 0], [center_x, 0, 0], cap=True)

    # -- Torso Block (Between Neck and Waist) --
    torso_block = trimesh.intersections.slice_mesh_plane(
        core_mesh, [0, -1, 0], [0, neck_y, 0], cap=True)
    torso_block = trimesh.intersections.slice_mesh_plane(
        torso_block, [0, 1, 0], [0, waist_y, 0], cap=True)
    
    # Split Torso into Upper/Lower (50/50 split of the torso block)
    tb_min, tb_max = torso_block.bounds[0][1], torso_block.bounds[1][1]
    torso_mid = tb_min + (tb_max - tb_min) * 0.5
    
    parts_geometry["UpperTorso"] = trimesh.intersections.slice_mesh_plane(
        torso_block, [0, 1, 0], [0, torso_mid, 0], cap=True)
    parts_geometry["LowerTorso"] = trimesh.intersections.slice_mesh_plane(
        torso_block, [0, -1, 0], [0, torso_mid, 0], cap=True)

    # ---------------------------------------------------------
    # STEP 4: SUB-SLICE LIMBS (Upper/Lower/Hand)
    # ---------------------------------------------------------
    # Arms
    parts_geometry["LeftUpperArm"], parts_geometry["LeftLowerArm"], parts_geometry["LeftHand"] = slice_limb(l_arm_raw)
    parts_geometry["RightUpperArm"], parts_geometry["RightLowerArm"], parts_geometry["RightHand"] = slice_limb(r_arm_raw)

    # Legs
    parts_geometry["LeftUpperLeg"], parts_geometry["LeftLowerLeg"], parts_geometry["LeftFoot"] = slice_limb(l_leg_raw)
    parts_geometry["RightUpperLeg"], parts_geometry["RightLowerLeg"], parts_geometry["RightFoot"] = slice_limb(r_leg_raw)

    # ---------------------------------------------------------
    # STEP 5: FINAL CLEANUP
    # ---------------------------------------------------------
    final_r15 = {}
    for name in R15_NAMES:
        raw_part = parts_geometry.get(name, trimesh.Trimesh())
        repaired = repair_mesh_part(raw_part)
        
        # Calculate volume/center for the pipeline
        repaired.metadata['volume'] = repaired.volume
        repaired.metadata['center'] = repaired.centroid
        
        final_r15[name] = repaired

    return final_r15
