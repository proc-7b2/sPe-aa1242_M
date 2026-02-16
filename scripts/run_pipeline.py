import argparse
import trimesh
import os
from pipeline.preprocess import load_mesh
from pipeline.utils import normalize_mesh
from pipeline.segment import segment_r6_components

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to input character mesh")
    parser.add_argument("output_file", help="Path to save the final GLB")
    parser.add_argument("--head_ratio", type=float, default=0.22)
    parser.add_argument("--torso_ratio", type=float, default=0.45)
    args = parser.parse_args()

    # 1. Load & Normalize
    print(f"Loading mesh: {args.input}")
    mesh = load_mesh(args.input)
    mesh = normalize_mesh(mesh)

    # 2. Segment (Geometric Slicing)
    print("Slicing into R6 components...")
    r6_parts = segment_r6_components(mesh, args.head_ratio, args.torso_ratio)

    # 3. Combine into a Scene for GLB Export
    # We create a Scene so that each part remains a separate named submesh
    scene = trimesh.Scene()
    
    print("\n--- Slice Data ---")
    for name, part_mesh in r6_parts.items():
        if not part_mesh.is_empty:
            # Assign names to submeshes for the GLB
            part_mesh.visual.face_colors = trimesh.visual.random_color() 
            scene.add_geometry(part_mesh, node_name=name)
            
            vol = part_mesh.metadata.get('volume', 0)
            print(f"Part: {name:10} | Volume: {vol:10.4f} | Center: {part_mesh.centroid}")

    # 4. Export as a single GLB file
    scene.export(args.output_file)
    print(f"\nPipeline Complete: Exported {args.output_file}")

if __name__ == "__main__":
    main()
