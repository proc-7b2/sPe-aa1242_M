import numpy as np
import trimesh

R6_NAMES = ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]

def repair_mesh_part(mesh):
    """
    CLEANUP & HOLE FIX:
    - Removes duplicate vertices (doubles)
    - Fills holes
    - Decimates to simplify geometry (keeps UVs)
    """
    if mesh.is_empty:
        return mesh
    
    # 1. Remove Doubles (Small distance to keep detail)
    # This is the trimesh equivalent of your Blender remove_doubles
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    
    # 2. Fill Holes
    mesh.fill_holes()
    
    # 3. Clean up internal/junk geometry
    mesh.remove_infinite_values()
    mesh.remove_unreferenced_vertices()

    # 4. "Safe" Decimation
    # This reduces triangle count while trying to preserve UVs.
    # We only decimate if the mesh is very dense (over 5000 faces per part)
    if len(mesh.faces) > 5000:
        # 0.8 keeps 80% of the geometry.
        mesh = mesh.simplify_quadratic_decimation(int(len(mesh.faces) * 0.8))

    # 5. Shading Fix
    mesh.fix_normals()
    
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
            if dist < (total_height * 0.1): 
                is_near_head = True

        if (c_max[1] > head_line or is_near_head) and dist_from_center < arm_zone_width:
            parts["Head"].append(comp)
            continue

        if dist_from_center > arm_zone_width:
            if c_center[0] < center_x:
                parts["LeftArm"].append(comp)
            else:
                parts["RightArm"].append(comp)
            continue

        if c_center[1] < leg_line:
            if c_center[0] < center_x:
                parts["LeftLeg"].append(comp)
            else:
                parts["RightLeg"].append(comp)
            continue

        parts["Torso"].append(comp)

    final_r6 = {}
    for name in R6_NAMES:
        if parts[name]:
            combined = trimesh.util.concatenate(parts[name])
            # Process with UV-Safe repair
            final_r6[name] = repair_mesh_part(combined)
        else:
            final_r6[name] = trimesh.Trimesh(vertices=[[0,0,0],[0,0.01,0],[0.01,0,0]], faces=[[0,1,2]])
            
    return final_r6

def split_to_r15(r6_parts):
    r15 = {}
    
    def smart_split(mesh, split_plane_y, prefix, part_names):
        """
        Splits an R6 part into R15 segments by checking loose components 
        before resorting to a hard slice.
        """
        if mesh.is_empty:
            return
            
        # 1. Split the mesh into its loose components (e.g., shirt, body, buttons)
        loose_parts = mesh.split(only_watertight=False)
        
        above_parts = []
        below_parts = []
        to_be_sliced = []

        for p in loose_parts:
            p_min, p_max = p.bounds
            # If the entire part is above the line
            if p_min[1] > split_plane_y:
                above_parts.append(p)
            # If the entire part is below the line
            elif p_max[1] < split_plane_y:
                below_parts.append(p)
            # If the part spans across the line, it must be sliced
            else:
                to_be_sliced.append(p)

        # 2. Slice only the parts that actually cross the line
        for p in to_be_sliced:
            # We use the nearest vertex logic implicitly by slicing at the plane
            # but we could also snap 'split_plane_y' to the nearest vertex height
            top = p.slice_plane([0, split_plane_y, 0], [0, 1, 0], cap=True, engine='earcut')
            bottom = p.slice_plane([0, split_plane_y, 0], [0, -1, 0], cap=True, engine='earcut')
            above_parts.append(top)
            below_parts.append(bottom)

        # 3. Re-combine
        r15[prefix + part_names[0]] = trimesh.util.concatenate(above_parts)
        r15[prefix + part_names[1]] = trimesh.util.concatenate(below_parts)

    # --- Execution ---
    # Torso Split
    t = r6_parts["Torso"]
    t_min, t_max = t.bounds
    split_y = t_min[1] + (t_max[1] - t_min[1]) * 0.4
    smart_split(t, split_y, "", ["UpperTorso", "LowerTorso"])

    # Limb Split Logic (3-way)
    def smart_limb_split(mesh, prefix, is_leg=False):
        b_min, b_max = mesh.bounds
        h = b_max[1] - b_min[1]
        c1, c2 = b_min[1] + h*0.33, b_min[1] + h*0.66
        names = ["Foot", "LowerLeg", "UpperLeg"] if is_leg else ["Hand", "LowerArm", "UpperArm"]
        
        # This is a nested split: first split at c2, then split the bottom at c1
        loose = mesh.split(only_watertight=False)
        
        upper = [p for p in loose if p.bounds[0][1] > c2]
        mid_low = [p for p in loose if p.bounds[1][1] <= c2]
        cross = [p for p in loose if p.bounds[0][1] <= c2 and p.bounds[1][1] > c2]
        
        # ... apply slice_plane only to 'cross' parts ...
        # (Combined logic follows the same pattern as Torso)

    # (Limb calls)
    # ...
    
    r15["Head"] = r6_parts["Head"]
    return r15
