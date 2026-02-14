import numpy as np
import trimesh

def extract_submesh(mesh: trimesh.Trimesh, vertex_mask: np.ndarray) -> trimesh.Trimesh:
    """
    Extract submesh based on vertex mask.
    vertex_mask: boolean array of length mesh.vertices
    """

    if len(vertex_mask) != mesh.vertices.shape[0]:
        raise ValueError("vertex_mask length does not match number of vertices")

    # A face belongs to the part if ALL its vertices belong
    face_mask = vertex_mask[mesh.faces].all(axis=1)

    faces_idx = np.where(face_mask)[0]

    if len(faces_idx) == 0:
        return trimesh.Trimesh(vertices=np.array([]), faces=np.array([]))

    return mesh.submesh([faces_idx], append=True, repair=False)



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

