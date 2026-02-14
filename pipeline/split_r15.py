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



def split_mesh(mesh, labels):
    """
    labels: list of boolean arrays, one per R15 part
    Returns: dict of {R15_part_name: submesh}
    """
    submeshes = {}
    for i, label in enumerate(labels):
        sub = extract_submesh(mesh, label)
        if sub.faces.shape[0] > 0:  # skip empty
            part_name = R15_PARTS[i] if i < len(R15_PARTS) else f"Part{i}"
            submeshes[part_name] = sub
    return submeshes

