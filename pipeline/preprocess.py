import trimesh

def load_mesh(path):
    mesh = trimesh.load(path, force='mesh')
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(mesh.dump())
    return mesh


def clean_components(mesh, area_ratio=0.005):
    components = mesh.split(only_watertight=False)

    if len(components) == 1:
        return mesh

    total_area = mesh.area
    cleaned = []

    for comp in components:
        if comp.area / total_area > area_ratio:
            cleaned.append(comp)

    return trimesh.util.concatenate(cleaned)

