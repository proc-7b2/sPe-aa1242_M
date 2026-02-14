import sys
import yaml
import os
import trimesh

from pipeline.preprocess import load_mesh, clean_components
from pipeline.segment import segment_r15
from pipeline.split_r15 import split_mesh
from pipeline.utils import normalize_mesh


def main(input_path, output_path):
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    mesh = load_mesh(input_path)
    mesh = normalize_mesh(mesh)

    # FIXED CONFIG ACCESS
    export_config = config.get("export", {})
    if export_config.get("remove_small_components", False):
        mesh = clean_components(mesh)

    # Segment mesh into R15 labels
    labels = segment_r15(mesh)

    # Split mesh into R15 named parts
    submeshes = split_mesh(mesh, labels)

    # Create scene and add each R15 part
    scene = trimesh.Scene()
    for part_name, submesh in submeshes.items():
        scene.add_geometry(submesh, node_name=part_name)

    # Make sure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Export single GLB
    scene.export(output_path)

    print(f"Exported R15 model to: {output_path}")


if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    main(input_path, output_path)
