import argparse
import trimesh
import os
from pipeline.preprocess import load_mesh
from pipeline.utils import normalize_mesh
# Removed split_to_r15 from imports because it is now handled in Blender
from pipeline.segment import segment_r6_components

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to input character mesh")
    parser.add_argument("output_dir", help="Directory to save segmented R6 parts")
    parser.add_argument("--head_ratio", type=float, default=0.22)
    parser.add_argument("--torso_ratio", type=float, default=0.45)
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # 1. Load & Normalize
    print(f"Loading mesh: {args.input}")
    mesh = load_mesh(args.input)
    mesh = normalize_mesh(mesh)

    # 2. Segment to R6 (Grouping loose meshes into 6 parts)
    print("Segmenting into R6 components...")
    r6_parts = segment_r6_components(mesh, args.head_ratio, args.torso_ratio)

    # 3. Export each R6 part as an individual file for Blender
    # This is necessary so the Blender script can import them one by one
    print(f"Exporting R6 parts to: {args.output_dir}")
    for name, data in r6_parts.items():
        if data and not data.is_empty:
            # We save as OBJ to keep the process simple for the Blender import
            export_path = os.path.join(args.output_dir, f"{name}.obj")
            data.export(export_path)
            print(f" - Saved: {name}.obj")

    print("\nStep 1 Complete: R6 Grouping finished.")
    print("Next: Run the Blender script on this output directory to generate R15 parts.")

if __name__ == "__main__":
    main()
