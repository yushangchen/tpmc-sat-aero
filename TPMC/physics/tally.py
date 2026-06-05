from __future__ import annotations

import numpy as np


def particle_force_contribution(
    molecular_mass: float,
    v_in: np.ndarray,
    v_out: np.ndarray,
    sample_weight: float
) -> np.ndarray:
    return -sample_weight * molecular_mass * (v_out - v_in)


def particle_moment_contribution(
    hit_point: np.ndarray,
    force: np.ndarray,
    reference_point: np.ndarray
) -> np.ndarray:
    r = hit_point - reference_point
    return np.cross(r, force)