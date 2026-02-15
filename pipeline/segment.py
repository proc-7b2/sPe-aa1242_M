import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh):
    # 1. Get loose meshes and filter out tiny "dust" particles
    all_components = mesh.split(only_watertight=False)
    components = [c for c in all_components if c.area > (mesh.area * 0.0001)]
    
    # 2. Global References
    bounds_min, bounds_max = mesh.bounds
    center_x = (bounds_max[0] + bounds_min[0]) / 2
    total_height = bounds_max[1] - bounds_min[1]
    
    parts = {name: [] for name in R6_NAMES}

    # 3. PRIORITY 1: FIND THE HEAD
    # The component that reaches the absolute highest point of the model
    components.sort(key=lambda c: c.bounds[1][1], reverse=True)
    head_piece = components.pop(0) # Take the highest one
    parts["Head"].append(head_piece)

    # 4. PRIORITY 2: FIND THE LEGS (Anything touching the floor)
    # Any component whose bottom is in the bottom 20% of the whole model
    remaining = []
    foot_line = bounds_min[1] + (total_height * 0.2)
    
    for comp in components:
        if comp.bounds[0][1] < foot_line:
            if comp.centroid[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
        else:
            remaining.append(comp)
    
    # 5. PRIORITY 3: FIND THE TORSO (The largest remaining central mass)
    remaining.sort(key=lambda c: c.area, reverse=True)
    
    torso_piece = None
    final_remaining = []
    
    for comp in remaining:
        # The first large piece we find near the center X is the Torso
        if torso_piece is None and abs(comp.centroid[0] - center_x) < (total_height * 0.15):
            torso_piece = comp
            parts["Torso"].append(comp)
        else:
            final_remaining.append(comp)

    # 6. PRIORITY 4: ARMS VS TORSO BITS
    # Now we check everything else against the Torso's width
    if torso_piece is not None:
        t_min_x, t_max_x = torso_piece.bounds[0][0], torso_piece.bounds[1][0]
        
        for comp in final_remaining:
            c_center_x = comp.centroid[0]
            
            # If the piece is outside the Torso's left/right edges, it's an Arm
            if c_center_x < t_min_x:
                parts["LeftArm"].append(comp)
            elif c_center_x > t_max_x:
                parts["RightArm"].append(comp)
            else:
                # If it's inside the torso width and not the head/legs, it's a torso detail
                # BUT if it's very high up, give it back to the head
                if comp.bounds[0][1] > torso_piece.centroid[1]:
                    parts["Head"].append(comp)
                else:
                    parts["Torso"].append(comp)
    
    # Clean up: Merge and return
    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            final_r6[name] = trimesh.util.concatenate(parts[name])
        else:
            # Create dummy if missing
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0,0.01,0],[0.01,0,0]], faces=[[0,1,2]])
            
    return final_r6
