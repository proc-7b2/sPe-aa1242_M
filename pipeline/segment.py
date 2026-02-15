import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def segment_r6_components(mesh, head_height_ratio=0.22, torso_height_ratio=0.45):
    all_comps = mesh.split(only_watertight=False)
    components = [c for c in all_comps if c.area > (mesh.area * 0.0005)]
    
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    total_width = bounds_max[0] - bounds_min[0]
    center_x = (bounds_max[0] + bounds_min[0]) / 2

    # Ratios
    head_line = bounds_max[1] - (total_height * head_height_ratio)
    leg_line = bounds_min[1] + (total_height * torso_height_ratio)
    arm_zone_width = total_width * 0.18 

    parts = {name: [] for name in R6_NAMES}
    remaining_after_head = []

    # --- STEP 1: FIND THE "MAIN" HEAD ---
    # We find the largest component in the top zone to use as an anchor
    head_candidates = [c for c in components if c.bounds[1][1] > head_line]
    head_candidates.sort(key=lambda c: c.area, reverse=True)
    
    main_head = head_candidates[0] if head_candidates else None
    
    # --- STEP 2: ASSIGN COMPONENTS ---
    for comp in components:
        c_max = comp.bounds[1]
        c_center = comp.centroid
        dist_from_center = abs(c_center[0] - center_x)

        # 1. NEW HEAD LOGIC: "If it looks like a head piece OR is near the main head"
        is_head_by_height = c_max[1] > head_line
        
        # Distance check: If it's within 5% of the total height from the main head
        is_near_head = False
        if main_head:
            distance = trimesh.proximity.closest_point(main_head, [c_center])[1][0]
            if distance < (total_height * 0.05): 
                is_near_head = True

        if is_head_by_height or is_near_head:
            # But only if it's not way out in the arm area
            if dist_from_center < arm_zone_width:
                parts["Head"].append(comp)
                continue

        # 2. ARM CHECK (Horizontal Priority)
        if dist_from_center > arm_zone_width:
            if c_center[0] < center_x:
                parts["LeftArm"].append(comp)
            else:
                parts["RightArm"].append(comp)
            continue

        # 3. LEG CHECK
        if c_center[1] < leg_line:
            if c_center[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
            continue

        # 4. TORSO
        parts["Torso"].append(comp)

    # Final Merge
    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            final_r6[name] = trimesh.util.concatenate(parts[name])
        else:
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0,0.01,0],[0.01,0,0]], faces=[[0,1,2]])
            
    return final_r6
