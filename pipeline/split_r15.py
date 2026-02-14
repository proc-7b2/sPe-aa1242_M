def split_mesh(mesh, labels):
    submeshes = []
    for label in labels:
        sub = extract_submesh(mesh, label)
        # Only keep submeshes that have faces
        if sub.faces.shape[0] > 0:
            submeshes.append(sub)
    return submeshes
