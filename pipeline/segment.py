import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh):
    # 1. Get loose meshes and filter out tiny artifacts
    all_comps = mesh.split(only_watertight=False)
    components = [c for c in all_comps if c.area > (mesh.area * 0.0005)]
    
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    total_width = bounds_max[0] - bounds_min[0]
    center_x = (bounds_max[0] + bounds_min[0]) / 2

    # Define simple height-based zones for the initial sweep
    head_line = bounds_max[1] - (total_height * 0.22)  # Top 22%
    leg_line = bounds_min[1] + (total_height * 0.40)   # Bottom 40%
    
    parts = {name: [] for name in R6_NAMES}

    for comp in components:
        c_min, c_max = comp.bounds
        c_center = comp.centroid
        
        # --- CATEGORY 1: HEAD PIECES ---
        # If any part of the component is in the top zone
        if c_max[1] > head_line:
            parts["Head"].append(comp)
            continue

        # --- CATEGORY 2: LEG PIECES ---
        # If the center of the piece is in the bottom zone
        if c_center[1] < leg_line:
            if c_center[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
            continue

        # --- CATEGORY 3: MID-SECTION (Torso & Arms) ---
        # We look at the X-position (Horizontal)
        # If it's near the center spine, it's Torso. If it's far, it's an Arm.
        dist_from_center = abs(c_center[0] - center_x)
        
        if dist_from_center < (total_width * 0.18): # Central 36% of width
            parts["Torso"].append(comp)
        else:
            if c_center[0] < center_x:
                parts["LeftArm"].append(comp)
            else:
                parts["RightArm"].append(comp)

    # 4. FINAL MERGE
    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            final_r6[name] = trimesh.util.concatenate(parts[name])
        else:
            # Placeholder to prevent export crashes
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0.01,0,0],[0,0.01,0]], faces=[[0,1,2]])
            
    return final_r6
