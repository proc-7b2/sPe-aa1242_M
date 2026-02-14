import sys
import yaml
from pipeline.preprocess import load_mesh, clean_components
from pipeline.segment import segment_r15
from pipeline.split_r15 import split_mesh
from pipeline.export import export_scene
from pipeline.utils import normalize_mesh


def main(input_path, output_path):
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    mesh = load_mesh(input_path)
    mesh = normalize_mesh(mesh)

    if config["remove_small_components"]:
        mesh = clean_components(mesh)

    labels = segment_r15(mesh)
    submeshes = split_mesh(mesh, labels)

    export_scene(submeshes, output_path)


if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    main(input_path, output_path)

