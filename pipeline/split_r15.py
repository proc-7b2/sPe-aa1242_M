import numpy as np
import trimesh


def split_mesh(mesh, labels_dict):
    """
    labels_dict example:
    {
        "Head": array([12, 18, 42, ...]),
        "UpperTorso": array([...]),
        ...
    }
    """

    submeshes = {}

    for part_name, vertex_indices in labels_dict.items():

        if len(vertex_indices) == 0:
            continue

        # Convert indices → full vertex mask
        vertex_mask = np.zeros(mesh.vertices.shape[0], dtype=bool)
        vertex_mask[vertex_indices] = True

        # Convert vertex mask → face mask
        face_mask = vertex_mask[mesh.faces].all(axis=1)
        faces_idx = np.where(face_mask)[0]

        if len(faces_idx) == 0:
            continue

        sub = mesh.submesh([faces_idx], append=True, repair=False)
        submeshes[part_name] = sub

    return submeshes

def split_mesh(mesh, labels_dict):
    """
    labels_dict: {
        "Head": vertex_mask,
        "UpperTorso": vertex_mask,
        ...
    }
    """

    submeshes = {}

    for part_name, vertex_mask in labels_dict.items():

        # Safety check
        if len(vertex_mask) != mesh.vertices.shape[0]:
            raise ValueError(
                f"{part_name} mask length {len(vertex_mask)} "
                f"!= vertices {mesh.vertices.shape[0]}"
            )

        # Convert vertex mask → face mask
        face_mask = vertex_mask[mesh.faces].all(axis=1)
        faces_idx = np.where(face_mask)[0]

        if len(faces_idx) == 0:
            continue

        sub = mesh.submesh([faces_idx], append=True, repair=False)
        submeshes[part_name] = sub

    return submeshes

