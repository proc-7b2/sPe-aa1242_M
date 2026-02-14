import trimesh

def export_scene(submeshes, output_path):
    scene = trimesh.Scene()

    for name, mesh in submeshes.items():
        scene.add_geometry(mesh, node_name=name)

    scene.export(output_path)

