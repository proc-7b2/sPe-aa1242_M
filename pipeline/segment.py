import numpy as np
import trimesh

# Defining the R6 parts first as requested
R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh):
    """
    Identifies loose meshes and assigns them to R6 categories 
    without cutting any triangles.
    """
    # 1. Split the mesh into its natural 'loose' components
    components = mesh.split(only_watertight=False)
    
    # 2. Get global stats for spatial reference
    min_bound, max_bound = mesh.bounds
    center_x = mesh.centroid[0]
    total_height = max_bound[1] - min_bound[1]
    
    # Storage for our R6 parts
    parts = {name: [] for name in R6_NAMES}
    
    for comp in components:
        # Get the center of this specific loose mesh
        c = comp.centroid
        
        # LOGIC: Categorize based on where the component's center is
        # Head: The component(s) centered in the top 25% of the model
        if c[1] > max_bound[1] - (total_height * 0.25):
            parts["Head"].append(comp)
            
        # Legs: Components centered in the bottom 40%, split by X-axis
        elif c[1] < min_bound[1] + (total_height * 0.4):
            if c[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
        
        # Middle Section: Torso and Arms
        else:
            width = max_bound[0] - min_bound[0]
            # Torso: Is the component centered near the middle X?
            if abs(c[0] - center_x) < (width * 0.2):
                parts["Torso"].append(comp)
            # Arms: Side components
            elif c[0] < center_x:
                parts["LeftArm"].append(comp)
            else:
                parts["RightArm"].append(comp)

    # Merge any multiple components found for a single part (e.g., eyes + head)
    final_r6 = {}
    for name, comps in parts.items():
        if comps:
            final_r6[name] = trimesh.util.concatenate(comps)
            
    return final_r6
