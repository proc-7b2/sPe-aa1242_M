import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh):
    # 1. Get loose meshes
    all_comps = mesh.split(only_watertight=False)
    # Ignore tiny floating bits
    components = [c for c in all_comps if c.area > (mesh.area * 0.001)]
    
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    center_y = bounds_min[1] + (total_height * 0.5)
    center_x = (bounds_min[0] + bounds_max[0]) / 2

    # 2. FIND THE TORSO (The "True" Anchor)
    # We look for the largest piece whose center is in the middle 50% of the body
    candidates = []
    for c in components:
        # Is this piece in the "Torso Zone" (not the very top, not the very bottom)?
        if bounds_min[1] + (total_height * 0.25) < c.centroid[1] < bounds_max[1] - (total_height * 0.2):
            candidates.append(c)
    
    if not candidates:
        candidates = components # Fallback if model is weird

    # Sort candidates by area; the biggest one is our Torso
    candidates.sort(key=lambda c: c.area, reverse=True)
    torso_main = candidates[0]
    
    # 3. DEFINE BOUNDARIES BASED ON TORSO
    t_min, t_max = torso_main.bounds
    # Neck is the top of the torso mesh
    neck_line = t_max[1] - ( (t_max[1] - t_min[1]) * 0.1)
    # Waist is the bottom of the torso mesh
    waist_line = t_min[1] + ( (t_max[1] - t_min[1]) * 0.1)

    parts = {name: [] for name in R6_NAMES}

    for comp in components:
        c_center = comp.centroid
        c_bounds = comp.bounds

        # RULE 1: Above the Torso = HEAD
        if c_center[1] > neck_line:
            parts["Head"].append(comp)
            continue

        # RULE 2: Below the Torso = LEGS
        if c_center[1] < waist_line:
            if c_center[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
            continue

        # RULE 3: Side of the Torso = ARMS
        if c_center[0] < t_min[0]:
            parts["LeftArm"].append(comp)
        elif c_center[0] > t_max[0]:
            parts["RightArm"].append(comp)
            
        # RULE 4: Middle = TORSO
        else:
            parts["Torso"].append(comp)

    # Merge parts
    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            final_r6[name] = trimesh.util.concatenate(parts[name])
        else:
            # Create dummy to prevent crash
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0,0.01,0],[0.01,0,0]], faces=[[0,1,2]])
            
    return final_r6
