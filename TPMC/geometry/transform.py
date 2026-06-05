from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from geometry.primitives import Mesh


def rotation_matrix_x(angle_deg: float) -> np.ndarray:
    a = np.deg2rad(angle_deg)
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [1.0, 0.0, 0.0],
        [0.0, c,   -s ],
        [0.0, s,    c ],
    ])


def rotation_matrix_y(angle_deg: float) -> np.ndarray:
    a = np.deg2rad(angle_deg)
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [ c, 0.0, s],
        [0.0, 1.0, 0.0],
        [-s, 0.0, c],
    ])


def rotation_matrix_z(angle_deg: float) -> np.ndarray:
    a = np.deg2rad(angle_deg)
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [c,  -s, 0.0],
        [s,   c, 0.0],
        [0.0, 0.0, 1.0],
    ])


def build_rotation_matrix(roll_deg: float, pitch_deg: float, yaw_deg: float) -> np.ndarray:
    """
    Rotation order:
        first roll about x,
        then pitch about y,
        then yaw about z

    Applied as:
        R = Rz @ Ry @ Rx
    """
    Rx = rotation_matrix_x(roll_deg)
    Ry = rotation_matrix_y(pitch_deg)
    Rz = rotation_matrix_z(yaw_deg)
    return Rz @ Ry @ Rx


def rotate_mesh(
    mesh: Mesh,
    roll_deg: float = 0.0,
    pitch_deg: float = 0.0,
    yaw_deg: float = 0.0,
    origin: np.ndarray | None = None
) -> Mesh:
    """
    Rotate mesh around a specified origin.
    If origin is None, use (0,0,0).
    """
    if origin is None:
        origin = np.zeros(3)

    R = build_rotation_matrix(roll_deg, pitch_deg, yaw_deg)

    vertices_shifted = mesh.vertices - origin[None, :]
    vertices_rotated = vertices_shifted @ R.T + origin[None, :]

    centroids_shifted = mesh.centroids - origin[None, :]
    centroids_rotated = centroids_shifted @ R.T + origin[None, :]

    normals_rotated = mesh.normals @ R.T

    return Mesh(
        vertices=vertices_rotated,
        faces=mesh.faces.copy(),
        centroids=centroids_rotated,
        normals=normals_rotated,
        areas=mesh.areas.copy(),
    )