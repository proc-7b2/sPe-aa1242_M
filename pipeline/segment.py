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

def find_snap_height(mesh, target_y):
    """Finds the nearest vertex height to target_y to snap the cut to an edge loop."""
    if mesh.is_empty: return target_y
    vertices = mesh.vertices[:, 1]
    # Find the vertex height closest to our target split line
    idx = (np.abs(vertices - target_y)).argmin()
    return vertices[idx]


def split_to_r15(r6_parts):
    r15 = {"Head": r6_parts["Head"]}

    def smart_slice(mesh, target_y, normal):
        if mesh.is_empty: return mesh
        
        # 1. Snap the target_y to the nearest existing vertex loop
        # This prevents 'shredding' triangles and follows the geometry
        snapped_y = find_snap_height(mesh, target_y)
        
        try:
            # 2. Slice at the snapped height
            return mesh.slice_plane([0, snapped_y, 0], normal, cap=True, engine='earcut')
        except:
            return mesh.slice_plane([0, target_y, 0], normal, cap=False)

    # --- TORSO ---
    t = r6_parts["Torso"]
    t_min, t_max = t.bounds
    # Roblox UpperTorso is usually larger than LowerTorso
    ideal_torso_cut = t_min[1] + (t_max[1] - t_min[1]) * 0.4 
    
    r15["UpperTorso"] = smart_slice(t, ideal_torso_cut, [0, 1, 0])
    r15["LowerTorso"] = smart_slice(t, ideal_torso_cut, [0, -1, 0])

    # --- LIMBS ---
    def split_limb(mesh, prefix, is_leg=False):
        b_min, b_max = mesh.bounds
        h = b_max[1] - b_min[1]
        
        # R15 Limb proportions: Foot/Hand is small, Lower/Upper are roughly equal
        c1_ratio = 0.2 if is_leg else 0.15 # Foot/Hand cut
        c2_ratio = 0.6 # Knee/Elbow cut
        
        c1_y = b_min[1] + h * c1_ratio
        c2_y = b_min[1] + h * c2_ratio
        
        names = ["Foot", "LowerLeg", "UpperLeg"] if is_leg else ["Hand", "LowerArm", "UpperArm"]
        
        # Upper
        r15[prefix + names[2]] = smart_slice(mesh, c2_y, [0, 1, 0])
        
        # Middle
        mid_section = smart_slice(mesh, c2_y, [0, -1, 0])
        r15[prefix + names[1]] = smart_slice(mid_section, c1_y, [0, 1, 0])
        
        # Lower
        r15[prefix + names[0]] = smart_slice(mid_section, c1_y, [0, -1, 0])

    split_limb(r6_parts["LeftArm"], "Left")
    split_limb(r6_parts["RightArm"], "Right")
    split_limb(r6_parts["LeftLeg"], "Left", True)
    split_limb(r6_parts["RightLeg"], "Right", True)
    
    return r15
