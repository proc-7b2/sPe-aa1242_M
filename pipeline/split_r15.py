import trimesh
import numpy as np

def split_mesh(mesh, labels):
    """
    Split a mesh into submeshes using vertex indices from labels.

    Parameters
    ----------
    mesh : trimesh.Trimesh
        The original mesh to split.
    labels : dict
        Dictionary of part_name -> list of vertex indices.

    Returns
    -------
    dict
        Dictionary of part_name -> trimesh.Trimesh submesh.
    """

    submeshes = {}

    for part_name, vertex_indices in labels.items():
        if not vertex_indices:
            continue  # skip empty parts

        # Ensure indices are within mesh vertex range
        vertex_indices = [i for i in vertex_indices if i < len(mesh.vertices)]
        if not vertex_indices:
            continue

        # Create a mask for which vertices to include
        vertex_mask = np.zeros(len(mesh.vertices), dtype=bool)
        vertex_mask[vertex_indices] = True

        # Get the faces that have all vertices in this part
        face_mask = np.all(vertex_mask[mesh.faces], axis=1)
        if not np.any(face_mask):
            # fallback: include faces with at least one vertex in part
            face_mask = np.any(vertex_mask[mesh.faces], axis=1)

        # Extract the submesh
        submesh = mesh.submesh([face_mask], append=True, repair=False)

        # Store with part name
        submeshes[part_name] = submesh

    return submeshes
