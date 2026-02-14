import numpy as np

R15_NAMES = [
    "Head",
    "UpperTorso",
    "LowerTorso",
    "LeftUpperArm",
    "LeftLowerArm",
    "LeftHand",
    "RightUpperArm",
    "RightLowerArm",
    "RightHand",
    "LeftUpperLeg",
    "LeftLowerLeg",
    "LeftFoot",
    "RightUpperLeg",
    "RightLowerLeg",
    "RightFoot"
]

def segment_r15(mesh):
    vertices = mesh.vertices
    faces = mesh.faces

    min_y, max_y = mesh.bounds[:, 1]
    height = max_y - min_y

    head_cut = max_y - height * 0.18
    torso_upper_cut = max_y - height * 0.35
    torso_lower_cut = max_y - height * 0.55
    leg_cut = min_y + height * 0.4

    center_x = mesh.bounding_box.centroid[0]

    # Dictionary of part_name -> set of vertex indices
    labels = {name: set() for name in R15_NAMES}

    # Assign vertices based on face centroids
    face_centroids = mesh.triangles_center

    for face_idx, centroid in enumerate(face_centroids):
        x, y, z = centroid
        verts = faces[face_idx]  # indices of vertices in this face

        if y > head_cut:
            labels["Head"].update(verts)

        elif y > torso_upper_cut:
            labels["UpperTorso"].update(verts)

        elif y > torso_lower_cut:
            labels["LowerTorso"].update(verts)

        elif y < leg_cut:
            if x < center_x:
                labels["LeftUpperLeg"].update(verts)
            else:
                labels["RightUpperLeg"].update(verts)

        else:
            if x < center_x:
                labels["LeftUpperArm"].update(verts)
            else:
                labels["RightUpperArm"].update(verts)

    # Convert sets to sorted lists
    labels = {k: sorted(list(v)) for k, v in labels.items()}

    return labels
