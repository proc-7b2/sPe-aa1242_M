import argparse
import trimesh
import os
from pipeline.preprocess import load_mesh
from pipeline.utils import normalize_mesh
from pipeline.segment import segment_r15_components # Now using R15 logic

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to input character mesh")
    parser.add_argument("output_file", help="Path to save the final GLB")
    parser.add_argument("--head_ratio", type=float, default=0.22)
    parser.add_argument("--torso_ratio", type=float, default=0.45) # Used for Upper/Lower Torso split
    args = parser.parse_args()

    # 1. Load & Normalize
    print(f"Loading mesh: {args.input}")
    mesh = load_mesh(args.input)
    mesh = normalize_mesh(mesh)

    # 2. Segment (Geometric Slicing)
    print("Slicing into R15 components...")
    # Note: Renamed variable to r15_parts to avoid confusion
    r15_parts = segment_r15_components(mesh, args.head_ratio, args.torso_ratio)

    # 3. Combine into a Scene for GLB Export
    scene = trimesh.Scene()
    
    print("\n--- Slice Data ---")
    for name, part_mesh in r15_parts.items():
        if not part_mesh.is_empty:
            # Assign random colors so you can see the segments easily in a 3D viewer
            part_mesh.visual.face_colors = trimesh.visual.random_color() 
            
            # This 'node_name' is what Blender/Roblox will use as the Object Name
            scene.add_geometry(part_mesh, node_name=name)
            
            # Accessing properties directly from the trimesh object
            vol = part_mesh.volume
            center = part_mesh.centroid
            print(f"Part: {name:15} | Volume: {vol:10.4f} | Center: {center}")

    # 4. Export as a single GLB file
    # GLB is great because it packs everything (geometry + names) into one binary file
    scene.export(args.output_file)
    print(f"\nPipeline Complete: Exported {args.output_file}")

if __name__ == "__main__":
    main()
