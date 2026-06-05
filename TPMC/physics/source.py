from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class SourcePlane:
    center: np.ndarray
    normal: np.ndarray
    axis1: np.ndarray
    axis2: np.ndarray
    half_width: float
    half_height: float
    area: float


def _normalize(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < eps:
        raise ValueError("Cannot normalize near-zero vector.")
    return v / n


def _build_plane_basis(normal: np.ndarray):
    """
    Build two orthonormal in-plane axes axis1, axis2
    such that {axis1, axis2, normal} forms an orthonormal basis.
    """
    n = _normalize(normal)

    if abs(n[0]) < 0.9:
        helper = np.array([1.0, 0.0, 0.0])
    else:
        helper = np.array([0.0, 1.0, 0.0])

    axis1 = np.cross(n, helper)
    axis1 = _normalize(axis1)

    axis2 = np.cross(n, axis1)
    axis2 = _normalize(axis2)

    return axis1, axis2


def create_source_plane(
    vertices: np.ndarray,
    flow_direction: np.ndarray,
    margin: float = 1.0,
    padding: float = 0.5
) -> SourcePlane:
    """
    Create a rectangular source plane upstream of the mesh.

    Parameters
    ----------
    vertices : np.ndarray, shape (Nv, 3)
        Mesh vertices.
    flow_direction : np.ndarray, shape (3,)
        Particle travel direction toward the body.
    margin : float
        Upstream distance before the minimum projection of the body.
    padding : float
        Extra plane half-size padding around the projected body bounds.

    Returns
    -------
    SourcePlane
    """
    u = _normalize(flow_direction)
    axis1, axis2 = _build_plane_basis(u)

    s = vertices @ u
    a = vertices @ axis1
    b = vertices @ axis2

    s_plane = np.min(s) - margin
    a_center = 0.5 * (np.min(a) + np.max(a))
    b_center = 0.5 * (np.min(b) + np.max(b))

    half_width = 0.5 * (np.max(a) - np.min(a)) + padding
    half_height = 0.5 * (np.max(b) - np.min(b)) + padding

    center = s_plane * u + a_center * axis1 + b_center * axis2
    area = 4.0 * half_width * half_height

    return SourcePlane(
        center=center,
        normal=u,
        axis1=axis1,
        axis2=axis2,
        half_width=half_width,
        half_height=half_height,
        area=area
    )


def sample_points_on_plane(
    plane: SourcePlane,
    n_samples: int,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Uniformly sample points on the source plane.
    """
    xi = rng.uniform(-plane.half_width, plane.half_width, size=n_samples)
    eta = rng.uniform(-plane.half_height, plane.half_height, size=n_samples)

    points = (
        plane.center[None, :]
        + xi[:, None] * plane.axis1[None, :]
        + eta[:, None] * plane.axis2[None, :]
    )

    return points