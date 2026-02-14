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

    labels = {}

    face_centroids = mesh.triangles_center

    for name in R15_NAMES:
        labels[name] = []

    for i, c in enumerate(face_centroids):
        x, y, z = c

        if y > head_cut:
            labels["Head"].append(i)

        elif y > torso_upper_cut:
            labels["UpperTorso"].append(i)

        elif y > torso_lower_cut:
            labels["LowerTorso"].append(i)

        elif y < leg_cut:
            if x < center_x:
                labels["LeftUpperLeg"].append(i)
            else:
                labels["RightUpperLeg"].append(i)

        else:
            if x < center_x:
                labels["LeftUpperArm"].append(i)
            else:
                labels["RightUpperArm"].append(i)

    return labels

