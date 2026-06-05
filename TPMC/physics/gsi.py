from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
import numpy as np


K_B = 1.380649e-23  # J/K

GSIModelType = Literal["specular", "diffuse", "maxwell", "cll"]


def _as_array(v) -> np.ndarray:
    return np.asarray(v, dtype=float)


def _normalize(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < eps:
        raise ValueError("Cannot normalize near-zero vector.")
    return v / n


def _build_local_basis(normal: np.ndarray):
    """
    Build local orthonormal basis:
        n  : outward surface normal
        t1 : first tangent direction
        t2 : second tangent direction
    """
    n = _normalize(_as_array(normal))

    if abs(n[0]) < 0.9:
        helper = np.array([1.0, 0.0, 0.0])
    else:
        helper = np.array([0.0, 1.0, 0.0])

    t1 = np.cross(n, helper)
    t1 = _normalize(t1)
    t2 = np.cross(n, t1)
    t2 = _normalize(t2)

    return n, t1, t2


@dataclass
class GSIConfig:
    model: GSIModelType = "diffuse"

    # wall state
    wall_temperature: float = 300.0
    wall_velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))

    # Maxwell model parameter
    diffuse_fraction: float = 1.0

    # CLL model parameters
    alpha_n: float = 1.0
    alpha_t: float = 1.0

    def validate(self) -> None:
        if self.model not in ("specular", "diffuse", "maxwell", "cll"):
            raise ValueError(
                f"Unsupported GSI model: {self.model}. "
                f"Choose from 'specular', 'diffuse', 'maxwell', or 'cll'."
            )

        if self.wall_temperature <= 0.0:
            raise ValueError("wall_temperature must be positive.")

        if not (0.0 <= self.diffuse_fraction <= 1.0):
            raise ValueError("diffuse_fraction must be between 0 and 1.")

        if not (0.0 <= self.alpha_n <= 1.0):
            raise ValueError("alpha_n must be between 0 and 1.")

        if not (0.0 <= self.alpha_t <= 1.0):
            raise ValueError("alpha_t must be between 0 and 1.")

        self.wall_velocity = _as_array(self.wall_velocity)
        if self.wall_velocity.shape != (3,):
            raise ValueError("wall_velocity must be a 3-component vector.")


def reflect_specular(
    v_in: np.ndarray,
    normal: np.ndarray,
    wall_velocity: np.ndarray | None = None,
) -> np.ndarray:
    """
    Specular reflection in wall frame, then transform back to lab frame.
    """
    if wall_velocity is None:
        wall_velocity = np.zeros(3)

    wall_velocity = _as_array(wall_velocity)
    n, _, _ = _build_local_basis(normal)

    v_rel_in = _as_array(v_in) - wall_velocity
    vn_in = np.dot(v_rel_in, n)

    if vn_in >= 0.0:
        raise ValueError("Incoming velocity is not directed into the surface in wall frame.")

    v_rel_out = v_rel_in - 2.0 * vn_in * n
    return v_rel_out + wall_velocity


def reflect_diffuse(
    normal: np.ndarray,
    wall_temperature: float,
    molecular_mass: float,
    rng: np.random.Generator,
    wall_velocity: np.ndarray | None = None,
) -> np.ndarray:
    """
    Fully diffuse reflection from a stationary/moving wall.

    Tangential components:
        Gaussian with variance kT/m
    Normal component:
        flux-weighted half-range Maxwellian
    """
    if molecular_mass <= 0.0:
        raise ValueError("molecular_mass must be positive.")

    if wall_velocity is None:
        wall_velocity = np.zeros(3)

    wall_velocity = _as_array(wall_velocity)
    n, t1, t2 = _build_local_basis(normal)

    sigma_t = np.sqrt(K_B * wall_temperature / molecular_mass)
    c_th = np.sqrt(2.0 * K_B * wall_temperature / molecular_mass)

    vt1 = sigma_t * rng.normal()
    vt2 = sigma_t * rng.normal()

    r = max(rng.random(), 1e-16)
    vn = c_th * np.sqrt(-np.log(r))

    v_rel_out = vn * n + vt1 * t1 + vt2 * t2
    return v_rel_out + wall_velocity


def reflect_maxwell(
    v_in: np.ndarray,
    normal: np.ndarray,
    wall_temperature: float,
    molecular_mass: float,
    diffuse_fraction: float,
    rng: np.random.Generator,
    wall_velocity: np.ndarray | None = None,
) -> np.ndarray:
    """
    Maxwell gas-surface model:
    diffuse with probability diffuse_fraction,
    specular otherwise.
    """
    if rng.random() < diffuse_fraction:
        return reflect_diffuse(
            normal=normal,
            wall_temperature=wall_temperature,
            molecular_mass=molecular_mass,
            rng=rng,
            wall_velocity=wall_velocity,
        )

    return reflect_specular(
        v_in=v_in,
        normal=normal,
        wall_velocity=wall_velocity,
    )


def reflect_cll(
    v_in: np.ndarray,
    normal: np.ndarray,
    wall_temperature: float,
    molecular_mass: float,
    alpha_n: float,
    alpha_t: float,
    rng: np.random.Generator,
    wall_velocity: np.ndarray | None = None,
) -> np.ndarray:
    """
    Cercignani-Lampis-Lord (CLL) model.

    alpha_n : normal accommodation coefficient
    alpha_t : tangential accommodation coefficient

    Limits:
      alpha_n = alpha_t = 0  -> specular limit
      alpha_n = alpha_t = 1  -> diffuse-like limit
    """
    if molecular_mass <= 0.0:
        raise ValueError("molecular_mass must be positive.")

    if wall_velocity is None:
        wall_velocity = np.zeros(3)

    wall_velocity = _as_array(wall_velocity)
    n, t1, t2 = _build_local_basis(normal)

    v_rel_in = _as_array(v_in) - wall_velocity

    vn_in_signed = np.dot(v_rel_in, n)
    if vn_in_signed >= 0.0:
        raise ValueError("Incoming velocity is not directed into the surface in wall frame.")

    c_th = np.sqrt(2.0 * K_B * wall_temperature / molecular_mass)

    # dimensionless incoming components in wall frame
    c_in_n = -vn_in_signed / c_th
    c_in_t1 = np.dot(v_rel_in, t1) / c_th
    c_in_t2 = np.dot(v_rel_in, t2) / c_th

    # tangential components
    c_out_t1 = np.sqrt(1.0 - alpha_t) * c_in_t1 + np.sqrt(alpha_t / 2.0) * rng.normal()
    c_out_t2 = np.sqrt(1.0 - alpha_t) * c_in_t2 + np.sqrt(alpha_t / 2.0) * rng.normal()

    # normal component
    r1 = max(rng.random(), 1e-16)
    r2 = rng.random()

    rn = np.sqrt(-alpha_n * np.log(r1))
    theta = 2.0 * np.pi * r2

    c_out_n_sq = (
        (1.0 - alpha_n) * c_in_n**2
        + rn**2
        + 2.0 * np.sqrt(1.0 - alpha_n) * c_in_n * rn * np.cos(theta)
    )
    c_out_n = np.sqrt(max(c_out_n_sq, 0.0))

    v_rel_out = c_th * (c_out_n * n + c_out_t1 * t1 + c_out_t2 * t2)
    return v_rel_out + wall_velocity


def apply_gsi_model(
    v_in: np.ndarray,
    normal: np.ndarray,
    molecular_mass: float,
    rng: np.random.Generator,
    gsi: GSIConfig,
) -> np.ndarray:
    """
    Unified GSI dispatcher.
    """
    gsi.validate()

    if gsi.model == "specular":
        return reflect_specular(
            v_in=v_in,
            normal=normal,
            wall_velocity=gsi.wall_velocity,
        )

    if gsi.model == "diffuse":
        return reflect_diffuse(
            normal=normal,
            wall_temperature=gsi.wall_temperature,
            molecular_mass=molecular_mass,
            rng=rng,
            wall_velocity=gsi.wall_velocity,
        )

    if gsi.model == "maxwell":
        return reflect_maxwell(
            v_in=v_in,
            normal=normal,
            wall_temperature=gsi.wall_temperature,
            molecular_mass=molecular_mass,
            diffuse_fraction=gsi.diffuse_fraction,
            rng=rng,
            wall_velocity=gsi.wall_velocity,
        )

    if gsi.model == "cll":
        return reflect_cll(
            v_in=v_in,
            normal=normal,
            wall_temperature=gsi.wall_temperature,
            molecular_mass=molecular_mass,
            alpha_n=gsi.alpha_n,
            alpha_t=gsi.alpha_t,
            rng=rng,
            wall_velocity=gsi.wall_velocity,
        )

    raise RuntimeError("Unexpected GSI model branch reached.")