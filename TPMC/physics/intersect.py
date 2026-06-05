from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class IntersectionResult:
    hit: bool
    face_index: int
    t: float
    point: np.ndarray


def ray_triangle_intersect(
    ray_origin: np.ndarray,
    ray_direction: np.ndarray,
    v0: np.ndarray,
    v1: np.ndarray,
    v2: np.ndarray,
    eps: float = 1e-12,
    t_min: float = 1e-12,
):
    """
    Möller–Trumbore ray-triangle intersection.
    """
    edge1 = v1 - v0
    edge2 = v2 - v0

    h = np.cross(ray_direction, edge2)
    a = np.dot(edge1, h)

    if -eps < a < eps:
        return False, None, None

    f = 1.0 / a
    s = ray_origin - v0
    u = f * np.dot(s, h)

    if u < 0.0 or u > 1.0:
        return False, None, None

    q = np.cross(s, edge1)
    v = f * np.dot(ray_direction, q)

    if v < 0.0 or (u + v) > 1.0:
        return False, None, None

    t = f * np.dot(edge2, q)

    if t > t_min:
        point = ray_origin + t * ray_direction
        return True, t, point

    return False, None, None


def intersect_ray_with_mesh(
    ray_origin: np.ndarray,
    ray_direction: np.ndarray,
    vertices: np.ndarray,
    faces: np.ndarray,
    eps: float = 1e-12,
    t_min: float = 1e-12,
) -> IntersectionResult:
    """
    Intersect one ray with a triangle mesh and return the nearest hit.
    """
    closest_t = np.inf
    closest_face = -1
    closest_point = None

    for i, face in enumerate(faces):
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]

        hit, t, point = ray_triangle_intersect(
            ray_origin,
            ray_direction,
            v0,
            v1,
            v2,
            eps=eps,
            t_min=t_min,
        )

        if hit and t < closest_t:
            closest_t = t
            closest_face = i
            closest_point = point

    if closest_face == -1:
        return IntersectionResult(
            hit=False,
            face_index=-1,
            t=np.inf,
            point=np.full(3, np.nan),
        )

    return IntersectionResult(
        hit=True,
        face_index=closest_face,
        t=closest_t,
        point=closest_point,
    )