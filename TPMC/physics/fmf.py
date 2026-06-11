from __future__ import annotations

import numpy as np

from physics.intersect import intersect_ray_with_mesh
from physics.gsi import GSIConfig, apply_gsi_model
from physics.tally import particle_force_contribution, particle_moment_contribution
from physics.surface_model import SurfaceModel
from physics.tracer import TraceResult


def trace_particle_fmf(
    ray_origin: np.ndarray,
    v_in0: np.ndarray,
    vertices: np.ndarray,
    faces: np.ndarray,
    normals: np.ndarray,
    molecular_mass: float,
    sample_weight: float,
    reference_point: np.ndarray,
    rng: np.random.Generator,
    gsi: GSIConfig | None = None,
    surface_model: SurfaceModel | None = None,
    eps_shift: float = 1e-9,
) -> TraceResult:
    """
    FMF v1:
    - trace only the first wall interaction
    - apply local GSI once
    - accumulate force/moment from that single interaction
    - do not continue secondary reflections
    """
    if surface_model is None and gsi is None:
        raise ValueError("Either gsi or surface_model must be provided.")

    if surface_model is not None:
        surface_model.validate()

    origin = np.asarray(ray_origin, dtype=float)
    v_in = np.asarray(v_in0, dtype=float)

    speed = np.linalg.norm(v_in)
    if speed <= 0.0:
        return TraceResult(
            total_force=np.zeros(3),
            total_moment=np.zeros(3),
            bounce_count=0,
            escaped=True,
        )

    ray_direction = v_in / speed

    result = intersect_ray_with_mesh(
        ray_origin=origin,
        ray_direction=ray_direction,
        vertices=vertices,
        faces=faces,
        t_min=eps_shift,
    )

    if not result.hit:
        return TraceResult(
            total_force=np.zeros(3),
            total_moment=np.zeros(3),
            bounce_count=0,
            escaped=True,
        )

    normal = normals[result.face_index]

    if surface_model is not None:
        gsi_local = surface_model.get_gsi(result.face_index)
    else:
        gsi_local = gsi

    v_out = apply_gsi_model(
        v_in=v_in,
        normal=normal,
        molecular_mass=molecular_mass,
        rng=rng,
        gsi=gsi_local,
    )

    force = particle_force_contribution(
        molecular_mass=molecular_mass,
        v_in=v_in,
        v_out=v_out,
        sample_weight=sample_weight,
    )

    moment = particle_moment_contribution(
        hit_point=result.point,
        force=force,
        reference_point=reference_point,
    )

    return TraceResult(
        total_force=force,
        total_moment=moment,
        bounce_count=1,
        escaped=True,
    )