import sys
import os
import trimesh
from pipeline.preprocess import load_mesh
from pipeline.utils import normalize_mesh
from pipeline.segment import segment_r6_components

def main(input_path, output_path):
    # Load and center (Crucial for X-axis Left/Right detection)
    mesh = load_mesh(input_path)
    mesh = normalize_mesh(mesh)

    # NEW: Segment by loose mesh components into R6
    r6_parts = segment_r6_components(mesh)

    # Create scene with correct R6 naming
    scene = trimesh.Scene()
    for part_name, submesh in r6_parts.items():
        scene.add_geometry(submesh, node_name=part_name)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    scene.export(output_path)
    
    print(f"Successfully exported clean R6 model: {output_path}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
