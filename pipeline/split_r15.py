def split_mesh(mesh, labels):
    submeshes = {}

    for name, face_ids in labels.items():
        if not face_ids:
            continue

        sub = mesh.submesh([face_ids], append=True)
        if len(sub) > 0:
            submeshes[name] = sub[0]

    return submeshes

