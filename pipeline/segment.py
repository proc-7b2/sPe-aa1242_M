import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def repair_mesh_part(mesh):
    if mesh.is_empty:
        return mesh
    
    # Basic cleanup
    mesh.remove_infinite_values()
    mesh.remove_unreferenced_vertices()
    
    # Try to make it manifold
    mesh.process(validate=True) 
    mesh.fill_holes()
    
    return mesh

def segment_r6_components(mesh, head_height_ratio=0.22, torso_height_ratio=0.45):
    all_comps = mesh.split(only_watertight=False)
    components = [c for c in all_comps if c.area > (mesh.area * 0.0005)]
    
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    total_width = bounds_max[0] - bounds_min[0]
    center_x = (bounds_max[0] + bounds_min[0]) / 2

    head_line = bounds_max[1] - (total_height * head_height_ratio)
    leg_line = bounds_min[1] + (total_height * torso_height_ratio)
    arm_zone_width = total_width * 0.18 

    parts = {name: [] for name in R6_NAMES}

    # Find Head Anchor
    head_candidates = [c for c in components if c.bounds[1][1] > head_line]
    head_candidates.sort(key=lambda c: c.area, reverse=True)
    main_head = head_candidates[0] if head_candidates else None
    
    for comp in components:
        c_max = comp.bounds[1]
        c_center = comp.centroid
        dist_from_center = abs(c_center[0] - center_x)

        is_near_head = False
        if main_head:
            dist = np.linalg.norm(c_center - main_head.centroid)
            if dist < (total_height * 0.1): is_near_head = True

        if (c_max[1] > head_line or is_near_head) and dist_from_center < arm_zone_width:
            parts["Head"].append(comp)
            continue

        if dist_from_center > arm_zone_width:
            if c_center[0] < center_x: parts["LeftArm"].append(comp)
            else: parts["RightArm"].append(comp)
            continue

        if c_center[1] < leg_line:
            if c_center[0] < center_x: parts["LeftLeg"].append(comp)
            else: parts["RightLeg"].append(comp)
            continue

        parts["Torso"].append(comp)

    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            combined = trimesh.util.concatenate(parts[name])
            final_r6[name] = repair_mesh_part(combined)
        else:
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0,0.01,0],[0.01,0,0]], faces=[[0,1,2]])
            
    return final_r6

def split_to_r15(r6_parts):
    r15 = {"Head": r6_parts["Head"]}
    
    def safe_slice(mesh, origin, normal):
        if mesh.is_empty: return mesh
        try:
            # Force engine='earcut' to ensure it uses the library we just installed
            return mesh.slice_plane(origin, normal, cap=True, engine='earcut')
        except Exception as e:
            print(f"Slice warning: {e}. Falling back to non-capped slice.")
            return mesh.slice_plane(origin, normal, cap=False)

    # Torso Split
    t = r6_parts["Torso"]
    t_min, t_max = t.bounds
    split_y = t_min[1] + (t_max[1] - t_min[1]) * 0.4
    r15["UpperTorso"] = safe_slice(t, [0, split_y, 0], [0, 1, 0])
    r15["LowerTorso"] = safe_slice(t, [0, split_y, 0], [0, -1, 0])

    def slice_limb(mesh, prefix, is_leg=False):
        b_min, b_max = mesh.bounds
        h = b_max[1] - b_min[1]
        c1, c2 = b_min[1] + h*0.33, b_min[1] + h*0.66
        names = ["Foot", "LowerLeg", "UpperLeg"] if is_leg else ["Hand", "LowerArm", "UpperArm"]
        
        r15[prefix + names[2]] = safe_slice(mesh, [0, c2, 0], [0, 1, 0])
        mid = safe_slice(mesh, [0, c2, 0], [0, -1, 0])
        r15[prefix + names[1]] = safe_slice(mid, [0, c1, 0], [0, 1, 0])
        r15[prefix + names[0]] = safe_slice(mid, [0, c1, 0], [0, -1, 0])

    slice_limb(r6_parts["LeftArm"], "Left")
    slice_limb(r6_parts["RightArm"], "Right")
    slice_limb(r6_parts["LeftLeg"], "Left", True)
    slice_limb(r6_parts["RightLeg"], "Right", True)
    
    return r15
