import numpy as np
import trimesh


# Official Roblox R15 part names
R15_PARTS = [
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


def split_mesh(mesh, labels):
    """
    Splits a mesh into R15 parts based on per-vertex labels.

    Parameters:
        mesh (trimesh.Trimesh)
        labels (np.ndarray or list) -> length must equal number of vertices
                                        each entry = part name string

    Returns:
        dict[str, trimesh.Trimesh]
    """

    if len(labels) != len(mesh.vertices):
        raise ValueError(
            f"Label count {len(labels)} != vertex count {len(mesh.vertices)}"
        )

    labels = np.array(labels)

    submeshes = {}

    for part_name in R15_PARTS:

        # Find vertices belonging to this part
        vertex_indices = np.where(labels == part_name)[0]

        if len(vertex_indices) == 0:
            print(f"[Warning] No vertices found for {part_name}")
            continue

        # Create boolean mask for vertices
        vertex_mask = np.zeros(len(mesh.vertices), dtype=bool)
        vertex_mask[vertex_indices] = True

        # Select faces where ALL vertices belong to this part
        face_mask = vertex_mask[mesh.faces].all(axis=1)

        if not np.any(face_mask):
            print(f"[Warning] No faces found for {part_name}")
            continue

        # Extract submesh
        submesh = mesh.submesh([face_mask], append=True, repair=False)

        if submesh is None or len(submesh.vertices) == 0:
            print(f"[Warning] Empty mesh for {part_name}")
            continue

        submeshes[part_name] = submesh

    print(f"Successfully split into {len(submeshes)} parts.")
    return submeshes
