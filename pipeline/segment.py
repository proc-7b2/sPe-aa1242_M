import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh):
    # 1. Get loose meshes (ignore tiny artifacts)
    all_comps = mesh.split(only_watertight=False)
    components = [c for c in all_comps if c.area > (mesh.area * 0.0005)]
    
    # 2. Find the "Anchor" (The Torso)
    # The Torso is the largest mesh component by surface area
    components.sort(key=lambda c: c.area, reverse=True)
    torso_main = components.pop(0) 
    
    t_min, t_max = torso_main.bounds
    t_center = torso_main.centroid
    
    # Define our "Zones" based on the Torso Anchor
    neck_line = t_max[1] - ( (t_max[1] - t_min[1]) * 0.1) # 10% from the top of torso
    waist_line = t_center[1] # Vertical center of the torso
    
    parts = {name: [] for name in R6_NAMES}
    parts["Torso"].append(torso_main)

    for comp in components:
        c_min, c_max = comp.bounds
        c_center = comp.centroid

        # RULE 1: Above the torso = HEAD
        # This prevents Arms from stealing Head pieces
        if c_center[1] > neck_line:
            parts["Head"].append(comp)
            continue

        # RULE 2: Below the torso center = LEGS
        # This prevents the Torso from stealing upper leg/hip pieces
        if c_center[1] < waist_line:
            if c_center[0] < t_center[0]:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
            continue

        # RULE 3: To the sides = ARMS
        if c_center[0] < t_min[0]:
            parts["LeftArm"].append(comp)
        elif c_center[0] > t_max[0]:
            parts["RightArm"].append(comp)
            
        # RULE 4: Anything else is a Torso detail (buttons, belts, etc.)
        else:
            parts["Torso"].append(comp)

    # Final Merge
    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            final_r6[name] = trimesh.util.concatenate(parts[name])
        else:
            # Create a placeholder if a limb is completely missing
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0,0.01,0],[0.01,0,0]], faces=[[0,1,2]])
            
    return final_r6
