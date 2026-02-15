import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh, head_height_ratio=0.22, torso_height_ratio=0.45):
    """
    head_height_ratio: Top % of body considered head (default 0.22)
    torso_height_ratio: Bottom % of body where legs begin (default 0.45)
    """
    # 1. Get loose meshes
    all_comps = mesh.split(only_watertight=False)
    components = [c for c in all_comps if c.area > (mesh.area * 0.0005)]
    
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    total_width = bounds_max[0] - bounds_min[0]
    center_x = (bounds_max[0] + bounds_min[0]) / 2

    # USE THE VARIABLES TO DEFINE THE CUT LINES
    # Higher torso_height_ratio = Shorter legs, Longer Torso
    # Lower torso_height_ratio = Longer legs, Shorter Torso
    head_line = bounds_max[1] - (total_height * head_height_ratio)
    leg_line = bounds_min[1] + (total_height * torso_height_ratio)
    
    parts = {name: [] for name in R6_NAMES}

    for comp in components:
        c_max = comp.bounds[1]
        c_center = comp.centroid
        
        # 1. HEAD CHECK
        if c_max[1] > head_line:
            parts["Head"].append(comp)
            continue

        # 2. LEG CHECK
        if c_center[1] < leg_line:
            if c_center[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
            continue

        # 3. MID-SECTION (Torso vs Arms)
        dist_from_center = abs(c_center[0] - center_x)
        if dist_from_center < (total_width * 0.2): # Central 40% of width
            parts["Torso"].append(comp)
        else:
            if c_center[0] < center_x:
                parts["LeftArm"].append(comp)
            else:
                parts["RightArm"].append(comp)

    # Final Merge
    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            final_r6[name] = trimesh.util.concatenate(parts[name])
        else:
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0.01,0,0],[0,0.01,0]], faces=[[0,1,2]])
            
    return final_r6
