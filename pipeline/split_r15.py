# pipeline/split_r15.py
import trimesh
import numpy as np

def extract_submesh(mesh: trimesh.Trimesh, face_mask: np.ndarray) -> trimesh.Trimesh:
    """
    Extract a submesh of the input mesh where the faces correspond to the given mask.
    face_mask: boolean array with length equal to mesh.faces.shape[0]
    """
    if mesh.faces.shape[0] != len(face_mask):
        raise ValueError("face_mask length does not match number of faces")
    
    faces_idx = np.where(face_mask)[0]
    if len(faces_idx) == 0:
        # return empty mesh
        return trimesh.Trimesh(vertices=np.array([]), faces=np.array([]))
    
    # append=True keeps a single mesh instead of a list
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

