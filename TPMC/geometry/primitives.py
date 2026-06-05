from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class Mesh:
    vertices: np.ndarray   # shape: (Nv, 3)
    faces: np.ndarray      # shape: (Nf, 3), indices into vertices
    centroids: np.ndarray  # shape: (Nf, 3)
    normals: np.ndarray    # shape: (Nf, 3), unit normals
    areas: np.ndarray      # shape: (Nf,)


def _compute_face_properties(vertices: np.ndarray, faces: np.ndarray):
    """
    Compute centroid, unit normal, and area for each triangular face.
    """
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]

    edge1 = v1 - v0
    edge2 = v2 - v0

    cross = np.cross(edge1, edge2)
    norm_cross = np.linalg.norm(cross, axis=1)

    # Triangle area = 0.5 * |edge1 x edge2|
    areas = 0.5 * norm_cross

    # Avoid division by zero
    if np.any(norm_cross == 0):
        raise ValueError("Degenerate triangle detected: zero area face exists.")

    normals = cross / norm_cross[:, None]
    centroids = (v0 + v1 + v2) / 3.0

    return centroids, normals, areas


def create_cube(side_length: float = 1.0, center=(0.0, 0.0, 0.0)) -> Mesh:
    """
    Create a cube mesh made of 12 triangles (2 triangles per face).

    Parameters
    ----------
    side_length : float
        Side length of the cube.
    center : tuple[float, float, float]
        Center position of the cube.

    Returns
    -------
    Mesh
        Mesh object containing vertices, faces, centroids, normals, and areas.
    """
    if side_length <= 0:
        raise ValueError("side_length must be positive.")

    cx, cy, cz = center
    h = side_length / 2.0

    # 8 cube vertices
    vertices = np.array([
        [cx - h, cy - h, cz - h],  # 0
        [cx + h, cy - h, cz - h],  # 1
        [cx + h, cy + h, cz - h],  # 2
        [cx - h, cy + h, cz - h],  # 3
        [cx - h, cy - h, cz + h],  # 4
        [cx + h, cy - h, cz + h],  # 5
        [cx + h, cy + h, cz + h],  # 6
        [cx - h, cy + h, cz + h],  # 7
    ], dtype=float)

    # 12 triangular faces
    # We choose the vertex order so the outward normal follows the right-hand rule.
    faces = np.array([
        # bottom face (z = -h)
        [0, 2, 1],
        [0, 3, 2],

        # top face (z = +h)
        [4, 5, 6],
        [4, 6, 7],

        # front face (y = -h)
        [0, 1, 5],
        [0, 5, 4],

        # back face (y = +h)
        [3, 7, 6],
        [3, 6, 2],

        # left face (x = -h)
        [0, 4, 7],
        [0, 7, 3],

        # right face (x = +h)
        [1, 2, 6],
        [1, 6, 5],
    ], dtype=int)

    centroids, normals, areas = _compute_face_properties(vertices, faces)

    return Mesh(
        vertices=vertices,
        faces=faces,
        centroids=centroids,
        normals=normals,
        areas=areas,
    )