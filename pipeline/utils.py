import numpy as np

def normalize_mesh(mesh):
    # center mesh at origin
    mesh.vertices -= mesh.bounding_box.centroid
    return mesh


def get_height_bounds(mesh):
    min_y = mesh.bounds[0][1]
    max_y = mesh.bounds[1][1]
    return min_y, max_y


def compute_height_ratio(mesh):
    min_y, max_y = get_height_bounds(mesh)
    return max_y - min_y

