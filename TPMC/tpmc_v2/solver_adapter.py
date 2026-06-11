from __future__ import annotations

import numpy as np

from main import build_surface_model, run_stl_case
from physics.reference import ReferenceConfig
from atmosphere.factory import build_atmosphere_provider
from tpmc_v2.case_schema import TPMCCase


def solve_case(case: TPMCCase) -> dict:
    surface_model = build_surface_model(case.face_map_csv)
    atmosphere_provider = build_atmosphere_provider(case.atmosphere_config)

    ref = ReferenceConfig(
        A_ref=case.A_ref,
        L_ref=case.L_ref,
        ref_point_body=np.array(case.ref_point_body, dtype=float),
        drag_axis_body=np.array(case.drag_axis_body, dtype=float),
        side_axis_body=np.array(case.side_axis_body, dtype=float),
        lift_axis_body=np.array(case.lift_axis_body, dtype=float),
    )

    result = run_stl_case(
        stl_path=case.stl_path,
        atmosphere_provider=atmosphere_provider,
        target_alt_km=case.target_alt_km,
        target_lat_deg=case.target_lat_deg,
        target_lon_deg=case.target_lon_deg,
        epoch=case.epoch,
        scale_factor=case.scale_factor,
        yaw_deg=case.yaw_deg,
        pitch_deg=case.pitch_deg,
        roll_deg=case.roll_deg,
        solver_mode=case.solver_mode,
        surface_model=surface_model,
        ref=ref,
        bulk_velocity_world=np.array(case.bulk_velocity_world, dtype=float),
        n_particles=case.n_particles,
        seed=case.seed,
    )

    result["case_name"] = case.name
    result["case_id"] = case.case_id
    result["tags"] = ";".join(case.tags)

    return result