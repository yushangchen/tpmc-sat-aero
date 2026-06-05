from __future__ import annotations

import numpy as np


K_B = 1.380649e-23  # J/K


def reflect_specular(v_in: np.ndarray, normal: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n_norm = np.linalg.norm(normal)
    if n_norm < eps:
        raise ValueError("Surface normal has near-zero magnitude.")

    n = normal / n_norm
    vn = np.dot(v_in, n)

    if vn >= 0:
        raise ValueError("Incoming velocity is not directed into the surface (v_in · n >= 0).")

    v_out = v_in - 2.0 * vn * n
    return v_out


def _build_local_basis(normal: np.ndarray, eps: float = 1e-12):
    n_norm = np.linalg.norm(normal)
    if n_norm < eps:
        raise ValueError("Surface normal has near-zero magnitude.")

    n = normal / n_norm

    if abs(n[0]) < 0.9:
        helper = np.array([1.0, 0.0, 0.0])
    else:
        helper = np.array([0.0, 1.0, 0.0])

    t1 = np.cross(n, helper)
    t1_norm = np.linalg.norm(t1)
    if t1_norm < eps:
        raise ValueError("Failed to construct tangent basis.")
    t1 = t1 / t1_norm

    t2 = np.cross(n, t1)
    t2 = t2 / np.linalg.norm(t2)

    return n, t1, t2


def reflect_diffuse(
    normal: np.ndarray,
    wall_temperature: float,
    molecular_mass: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Diffuse reflection using half-range Maxwellian emission from wall.

    Outgoing velocity is sampled in the wall frame:
    - tangential components ~ Normal(0, sigma^2)
    - normal component > 0 with flux-weighted distribution
    """
    if wall_temperature <= 0:
        raise ValueError("wall_temperature must be positive.")
    if molecular_mass <= 0:
        raise ValueError("molecular_mass must be positive.")

    n, t1, t2 = _build_local_basis(normal)

    sigma = np.sqrt(K_B * wall_temperature / molecular_mass)

    vt1 = sigma * rng.normal()
    vt2 = sigma * rng.normal()

    # flux-weighted half-range Maxwellian normal component
    r = rng.random()
    vn = np.sqrt(-2.0 * sigma**2 * np.log(max(r, 1e-16)))

    v_out = vn * n + vt1 * t1 + vt2 * t2
    return v_out


def reflect_mixed(
    v_in: np.ndarray,
    normal: np.ndarray,
    wall_temperature: float,
    molecular_mass: float,
    diffuse_fraction: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Mixed diffuse/specular reflection.
    diffuse_fraction = 0 -> purely specular
    diffuse_fraction = 1 -> purely diffuse
    """
    if not (0.0 <= diffuse_fraction <= 1.0):
        raise ValueError("diffuse_fraction must be between 0 and 1.")

    if rng.random() < diffuse_fraction:
        return reflect_diffuse(
            normal=normal,
            wall_temperature=wall_temperature,
            molecular_mass=molecular_mass,
            rng=rng,
        )
    else:
        return reflect_specular(v_in, normal)