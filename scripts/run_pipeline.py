import sys
import os
import argparse
import trimesh
from pipeline.preprocess import load_mesh
from pipeline.utils import normalize_mesh
from pipeline.segment import segment_r6_components

def main():
    parser = argparse.ArgumentParser(description="Convert Mesh to R6")
    parser.add_argument("input", help="Path to input mesh")
    parser.add_argument("output", help="Path to output GLB")
    parser.add_argument("--head_ratio", type=float, default=0.22, help="Head height percentage")
    parser.add_argument("--torso_ratio", type=float, default=0.45, help="Leg start height percentage")
    
    args = parser.parse_args()

    # Load and Preprocess
    mesh = load_mesh(args.input)
    mesh = normalize_mesh(mesh)

    # Segment using the custom ratios
    r6_parts = segment_r6_components(
        mesh, 
        head_height_ratio=args.head_ratio, 
        torso_height_ratio=args.torso_ratio
    )

    # Export Scene
    scene = trimesh.Scene()
    for part_name, submesh in r6_parts.items():
        scene.add_geometry(submesh, node_name=part_name)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    scene.export(args.output)
    
    print(f"Exported with Head Ratio: {args.head_ratio}, Torso Ratio: {args.torso_ratio}")

if __name__ == "__main__":
    main()
