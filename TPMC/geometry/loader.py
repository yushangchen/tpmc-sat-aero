from __future__ import annotations

from pathlib import Path
import numpy as np
import trimesh

from geometry.primitives import Mesh


def load_stl_mesh(filepath: str | Path) -> Mesh:
    """
    Load an STL file and convert it to our Mesh structure.
    """
    filepath = Path(filepath)

    # 官方現在更建議用 load_mesh
    tm = trimesh.load_mesh(filepath, process=True, validate=True)

    if tm.vertices is None or tm.faces is None:
        raise ValueError(f"Failed to load mesh from: {filepath}")

    if len(tm.faces) == 0:
        raise ValueError(f"Mesh has no faces: {filepath}")

    # 相容新版 trimesh 的清理方式
    tm.update_faces(tm.unique_faces())
    tm.remove_unreferenced_vertices()

    vertices = np.asarray(tm.vertices, dtype=float)
    faces = np.asarray(tm.faces, dtype=int)
    centroids = np.asarray(tm.triangles_center, dtype=float)
    normals = np.asarray(tm.face_normals, dtype=float)
    areas = np.asarray(tm.area_faces, dtype=float)

    return Mesh(
        vertices=vertices,
        faces=faces,
        centroids=centroids,
        normals=normals,
        areas=areas,
    )


def compute_bounding_box(vertices: np.ndarray):
    vmin = vertices.min(axis=0)
    vmax = vertices.max(axis=0)
    size = vmax - vmin
    center = 0.5 * (vmin + vmax)
    return vmin, vmax, size, center


def recenter_mesh(mesh: Mesh, target_center=(0.0, 0.0, 0.0)) -> Mesh:
    _, _, _, bbox_center = compute_bounding_box(mesh.vertices)
    target_center = np.asarray(target_center, dtype=float)
    shift = target_center - bbox_center

    return Mesh(
        vertices=mesh.vertices + shift,
        faces=mesh.faces.copy(),
        centroids=mesh.centroids + shift,
        normals=mesh.normals.copy(),
        areas=mesh.areas.copy(),
    )


def scale_mesh(mesh: Mesh, scale: float) -> Mesh:
    if scale <= 0:
        raise ValueError("scale must be positive.")

    return Mesh(
        vertices=mesh.vertices * scale,
        faces=mesh.faces.copy(),
        centroids=mesh.centroids * scale,
        normals=mesh.normals.copy(),
        areas=mesh.areas * (scale ** 2),
    )