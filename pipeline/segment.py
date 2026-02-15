import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def repair_mesh_part(mesh):
    """
    Cleans overlapping geometry and seals holes.
    If the mesh is too messy for standard filling, it uses a convex hull 
    per component to ensure a solid, sliceable volume.
    """
    if mesh.is_empty:
        return mesh
    
    # 1. Split into connected components to handle overlaps individually
    components = mesh.split(only_watertight=False)
    repaired_components = []

    for comp in components:
        # Standard repair
        comp.remove_infinite_values()
        comp.remove_unreferenced_vertices()
        comp.fill_holes()
        
        # If the part is still not watertight (has holes), 
        # we 'shrink-wrap' it using a convex hull. 
        # This is vital for loose faces (teeth, eyes, overlapping cloth).
        if not comp.is_watertight:
            repaired_components.append(comp.convex_hull)
        else:
            repaired_components.append(comp)

    # 2. Combine the solid parts back together
    if len(repaired_components) > 1:
        mesh = trimesh.util.concatenate(repaired_components)
    else:
        mesh = repaired_components[0]

    mesh.process(validate=True)
    return mesh

def segment_r6_components(mesh, head_height_ratio=0.22, torso_height_ratio=0.45):
    all_comps = mesh.split(only_watertight=False)
    # Ignore tiny floating artifacts
    components = [c for c in all_comps if c.area > (mesh.area * 0.0005)]
    
    bounds_min, bounds_max = mesh.bounds
    total_height = bounds_max[1] - bounds_min[1]
    total_width = bounds_max[0] - bounds_min[0]
    center_x = (bounds_min[0] + bounds_max[0]) / 2

    head_line = bounds_max[1] - (total_height * head_height_ratio)
    leg_line = bounds_min[1] + (total_height * torso_height_ratio)
    arm_zone_width = total_width * 0.18 

    parts = {name: [] for name in R6_NAMES}

    # Find Head Anchor (Largest piece in the top zone)
    head_candidates = [c for c in components if c.bounds[1][1] > head_line]
    head_candidates.sort(key=lambda c: c.area, reverse=True)
    main_head = head_candidates[0] if head_candidates else None
    
    for comp in components:
        c_max = comp.bounds[1]
        c_center = comp.centroid
        dist_from_center = abs(c_center[0] - center_x)

        # Head Assignment (Height + Proximity)
        is_near_head = False
        if main_head:
            dist = np.linalg.norm(c_center - main_head.centroid)
            if dist < (total_height * 0.1): 
                is_near_head = True

        if (c_max[1] > head_line or is_near_head) and dist_from_center < arm_zone_width:
            parts["Head"].append(comp)
            continue

        # Arm Assignment (Horizontal Priority)
        if dist_from_center > arm_zone_width:
            if c_center[0] < center_x:
                parts["LeftArm"].append(comp)
            else:
                parts["RightArm"].append(comp)
            continue

        # Leg Assignment (Vertical Priority)
        if c_center[1] < leg_line:
            if c_center[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
            continue

        # Remaining parts belong to Torso
        parts["Torso"].append(comp)

    # Final Merge and Repair
    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            combined = trimesh.util.concatenate(parts[name])
            final_r6[name] = repair_mesh_part(combined)
        else:
            # Prevent empty scene crashes
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0,0.01,0],[0.01,0,0]], faces=[[0,1,2]])
            
    return final_r6

def split_to_r15(r6_parts):
    """
    Slices R6 parts into R15 components. 
    Uses 'earcut' engine to cap the slices, ensuring joints are not hollow.
    """
    r15 = {"Head": r6_parts["Head"]}
    
    def safe_slice(mesh, origin, normal):
        if mesh.is_empty: 
            return mesh
        try:
            # Capping ensures the cut surface is a solid face
            return mesh.slice_plane(origin, normal, cap=True, engine='earcut')
        except Exception as e:
            # Fallback for complex geometry that earcut can't handle
            print(f"Slice warning: {e}. Falling back to open slice.")
            return mesh.slice_plane(origin, normal, cap=False)

    # Torso Split (Manual split at 40% height)
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
        
        # Upper Part
        r15[prefix + names[2]] = safe_slice(mesh, [0, c2, 0], [0, 1, 0])
        # Middle and Lower Parts
        mid_section = safe_slice(mesh, [0, c2, 0], [0, -1, 0])
        r15[prefix + names[1]] = safe_slice(mid_section, [0, c1, 0], [0, 1, 0])
        r15[prefix + names[0]] = safe_slice(mid_section, [0, c1, 0], [0, -1, 0])

    slice_limb(r6_parts["LeftArm"], "Left")
    slice_limb(r6_parts["RightArm"], "Right")
    slice_limb(r6_parts["LeftLeg"], "Left", True)
    slice_limb(r6_parts["RightLeg"], "Right", True)
    
    return r15
