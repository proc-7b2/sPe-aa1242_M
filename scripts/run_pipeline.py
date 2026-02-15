import argparse
import trimesh
import os
from pipeline.preprocess import load_mesh
from pipeline.utils import normalize_mesh
from pipeline.segment import segment_r6_components, split_to_r15

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--head_ratio", type=float, default=0.22)
    parser.add_argument("--torso_ratio", type=float, default=0.45)
    args = parser.parse_args()

    # 1. Load & Normalize
    mesh = load_mesh(args.input)
    mesh = normalize_mesh(mesh)

    # 2. Segment to R6 (Grouping loose meshes)
    r6_parts = segment_r6_components(mesh, args.head_ratio, args.torso_ratio)

    # 3. Convert to R15 (Slicing the parts)
    r15_parts = split_to_r15(r6_parts)

    # 4. Export
    scene = trimesh.Scene()
    for name, data in r15_parts.items():
        if data and not data.is_empty:
            scene.add_geometry(data, node_name=name)

    scene.export(args.output)
    print(f"Successfully converted to R15: {args.output}")

if __name__ == "__main__":
    main()
