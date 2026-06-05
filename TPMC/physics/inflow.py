from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
import numpy as np
from scipy.special import erf


K_B = 1.380649e-23  # J/K

InflowModelType = Literal["beam", "drifting_maxwellian", "flux_half_range"]


def _as_array(v) -> np.ndarray:
    return np.asarray(v, dtype=float)


def _normalize(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < eps:
        raise ValueError("Cannot normalize near-zero vector.")
    return v / n


def _build_local_basis(normal: np.ndarray):
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
class InflowConfig:
    bulk_velocity: np.ndarray
    temperature: float
    molecular_mass: float
    model: InflowModelType = "flux_half_range"
    use_thermal_spread: bool = True

    def validate(self) -> None:
        self.bulk_velocity = _as_array(self.bulk_velocity)

        if self.bulk_velocity.shape != (3,):
            raise ValueError("bulk_velocity must be a 3-component vector.")

        if self.temperature <= 0.0:
            raise ValueError("temperature must be positive.")

        if self.molecular_mass <= 0.0:
            raise ValueError("molecular_mass must be positive.")

        if self.model not in ("beam", "drifting_maxwellian", "flux_half_range"):
            raise ValueError(
                "model must be 'beam', 'drifting_maxwellian', or 'flux_half_range'."
            )


def thermal_speed_std(temperature: float, molecular_mass: float) -> float:
    """
    Standard deviation of each Cartesian velocity component
    for a Maxwellian distribution.
    """
    return np.sqrt(K_B * temperature / molecular_mass)


def positive_normal_flux_speed(
    bulk_velocity: np.ndarray,
    plane_normal: np.ndarray,
    temperature: float,
    molecular_mass: float,
) -> float:
    """
    Mean positive normal speed through a plane:
        <v_n H(v_n)>
    for a drifting Maxwellian.
    """
    U = _as_array(bulk_velocity)
    n = _normalize(_as_array(plane_normal))

    U_n = float(np.dot(U, n))
    sigma = thermal_speed_std(temperature, molecular_mass)

    a = U_n / sigma
    Phi = 0.5 * (1.0 + erf(a / np.sqrt(2.0)))

    return float(
        sigma / np.sqrt(2.0 * np.pi) * np.exp(-0.5 * a * a)
        + U_n * Phi
    )


_flux_sampler_cache = {}


def _flux_cdf(v: np.ndarray, U_n: float, sigma: float) -> np.ndarray:
    """
    CDF of the flux-weighted positive normal velocity distribution:
        p(v_n) ∝ v_n exp(-(v_n - U_n)^2 / (2 sigma^2)),  v_n > 0
    """
    v = np.asarray(v, dtype=float)

    def antiderivative(x):
        z = (x - U_n) / sigma
        return (
            -sigma**2 * np.exp(-0.5 * z * z)
            + U_n * sigma * np.sqrt(np.pi / 2.0) * erf(z / np.sqrt(2.0))
        )

    I0 = antiderivative(0.0)
    Iv = antiderivative(v) - I0

    Iinf = (
        sigma**2 * np.exp(-0.5 * (U_n / sigma) ** 2)
        + U_n * sigma * np.sqrt(np.pi / 2.0) * (1.0 + erf(U_n / (np.sqrt(2.0) * sigma)))
    )

    cdf = Iv / Iinf
    return np.clip(cdf, 0.0, 1.0)


def _get_flux_sampler(U_n: float, sigma: float, n_grid: int = 20000):
    key = (round(U_n, 12), round(sigma, 12), n_grid)

    if key in _flux_sampler_cache:
        return _flux_sampler_cache[key]

    v_max = max(U_n + 8.0 * sigma, 8.0 * sigma)

    # extend until CDF is sufficiently close to 1
    while True:
        v_grid = np.linspace(0.0, v_max, n_grid)
        cdf_grid = _flux_cdf(v_grid, U_n, sigma)

        if cdf_grid[-1] > 1.0 - 1e-10:
            break

        v_max *= 1.5

    cdf_grid = np.maximum.accumulate(cdf_grid)
    cdf_grid[0] = 0.0
    cdf_grid[-1] = 1.0

    _flux_sampler_cache[key] = (v_grid, cdf_grid)
    return v_grid, cdf_grid


def _sample_flux_weighted_normal_velocity(
    U_n: float,
    sigma: float,
    rng: np.random.Generator,
) -> float:
    v_grid, cdf_grid = _get_flux_sampler(U_n, sigma)
    r = rng.random()
    return float(np.interp(r, cdf_grid, v_grid))


def sample_inflow_velocity(
    inflow: InflowConfig,
    plane_normal: np.ndarray,
    rng: np.random.Generator,
    max_tries: int = 1000,
) -> np.ndarray:
    """
    Sample one incoming molecular velocity.

    Models:
    - beam: fixed bulk velocity
    - drifting_maxwellian: Gaussian thermal fluctuation around bulk velocity,
      then reject until v·n > 0
    - flux_half_range: physically improved source-plane crossing distribution
    """
    inflow.validate()

    n, t1, t2 = _build_local_basis(plane_normal)
    U = inflow.bulk_velocity

    if inflow.model == "beam" or not inflow.use_thermal_spread:
        return U.copy()

    sigma = thermal_speed_std(inflow.temperature, inflow.molecular_mass)

    if inflow.model == "drifting_maxwellian":
        for _ in range(max_tries):
            thermal = sigma * rng.normal(size=3)
            v = U + thermal
            if np.dot(v, n) > 0.0:
                return v
        raise RuntimeError("Failed to sample valid drifting Maxwellian inflow velocity.")

    if inflow.model == "flux_half_range":
        U_n = float(np.dot(U, n))
        U_t1 = float(np.dot(U, t1))
        U_t2 = float(np.dot(U, t2))

        if U_n <= 0.0:
            raise ValueError("For flux_half_range, bulk flow must point toward the body (U·n > 0).")

        vt1 = U_t1 + sigma * rng.normal()
        vt2 = U_t2 + sigma * rng.normal()
        vn = _sample_flux_weighted_normal_velocity(U_n, sigma, rng)

        return vn * n + vt1 * t1 + vt2 * t2

    raise RuntimeError("Unexpected inflow model branch reached.")