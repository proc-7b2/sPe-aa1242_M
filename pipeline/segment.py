import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh):
    # 1. Get loose meshes
    components = mesh.split(only_watertight=False)
    
    # 2. Global Bounds
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    center_x = (bounds_max[0] + bounds_min[0]) / 2
    
    # Thresholds
    head_threshold = bounds_max[1] - (total_height * 0.15)
    foot_threshold = bounds_min[1] + (total_height * 0.15)
    arm_threshold_dist = (bounds_max[0] - bounds_min[0]) * 0.2 # 20% out from center

    parts = {name: [] for name in R6_NAMES}

    for comp in components:
        c_min, c_max = comp.bounds
        c_center = comp.centroid
        
        # --- LOGIC 1: THE HEAD ---
        # If the highest point of this piece is in the top 15%
        if c_max[1] > head_threshold:
            parts["Head"].append(comp)
            continue

        # --- LOGIC 2: THE LEGS ---
        # If the lowest point of this piece is near the bottom floor
        if c_min[1] < foot_threshold:
            if c_center[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
            continue

        # --- LOGIC 3: THE ARMS ---
        # If the component is far from the center X spine
        if abs(c_center[0] - center_x) > arm_threshold_dist:
            if c_center[0] < center_x:
                parts["LeftArm"].append(comp)
            else:
                parts["RightArm"].append(comp)
            continue

        # --- LOGIC 4: THE TORSO ---
        # If it hasn't been claimed by head, legs, or arms, it's Torso
        parts["Torso"].append(comp)

    # Clean up: Merge pieces and handle empty parts
    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            final_r6[name] = trimesh.util.concatenate(parts[name])
        else:
            # Create a tiny dummy triangle if part is missing to prevent export errors
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0,0.01,0],[0.01,0,0]], faces=[[0,1,2]])
            print(f"Warning: {name} was empty. Check thresholds.")
            
    return final_r6
