import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh):
    """
    Advanced R6 segmentation using 'Core-First' logic to prevent
    torso/leg merging.
    """
    components = mesh.split(only_watertight=False)
    
    # 1. Setup Global References
    min_b, max_b = mesh.bounds
    center_x = mesh.centroid[0]
    full_height = max_b[1] - min_b[1]
    
    # 2. Identify the 'Core Torso' 
    # The Torso is typically the largest component near the center-top
    sorted_by_volume = sorted(components, key=lambda c: c.volume if c.is_watertight else c.area, reverse=True)
    
    # Potential Torso is the largest mesh that isn't at the very top (Head)
    torso_core = None
    for comp in sorted_by_volume:
        c = comp.centroid
        # If it's central and in the middle-upper half
        if abs(c[0] - center_x) < (full_height * 0.2) and c[1] > min_b[1] + (full_height * 0.4):
            torso_core = comp
            break
            
    # Reference points from our core Torso
    t_min, t_max = torso_core.bounds
    torso_bottom_edge = t_min[1] 
    
    parts = {name: [] for name in R6_NAMES}
    
    for comp in components:
        c = comp.centroid
        c_min, c_max = comp.bounds
        
        # HEAD: Highest components, or anything entirely above the torso core
        if c_min[1] > torso_core.centroid[1] and abs(c[0] - center_x) < (full_height * 0.2):
            parts["Head"].append(comp)
            
        # LEGS: Anything whose center is below the torso's bottom edge, 
        # OR anything whose lowest point is the bottom of the whole model.
        elif c[1] < torso_bottom_edge + (full_height * 0.05) or c_min[1] < min_b[1] + (full_height * 0.1):
            if c[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
                
        # ARMS: Anything significantly to the left/right of the Torso core
        elif c[0] < t_min[0]:
            parts["LeftArm"].append(comp)
        elif c[0] > t_max[0]:
            parts["RightArm"].append(comp)
            
        # TORSO: The core itself and any small bits (buttons, etc.) attached to it
        else:
            parts["Torso"].append(comp)

    # Concatenate results
    final_r6 = {}
    for name, comps in parts.items():
        if comps:
            final_r6[name] = trimesh.util.concatenate(comps)
        else:
            # Fallback for empty parts to prevent pipeline crash
            final_r6[name] = trimesh.Trimesh() 
            
    return final_r6
