from __future__ import annotations

from dataclasses import dataclass

from tpmc_v2.case_schema import TPMCCase


@dataclass(frozen=True)
class BenchmarkDefinition:
    key: str
    description: str
    case: TPMCCase


def build_cube_benchmark_suite() -> list[BenchmarkDefinition]:
    base_case = TPMCCase(
        name="cube_benchmark",
        stl_path=r"G:\我的雲端硬碟\TPMC\testcube.stl",
        atmosphere_config={
            "type": "nrlmsis_txt",
            "filepath": r"G:\我的雲端硬碟\TPMC\nrlmsis_output.txt",
        },
        target_alt_km=500.0,
        target_lat_deg=55.0,
        target_lon_deg=45.0,
        epoch="2026-05-12T00:00:00",
        scale_factor=0.001,
        face_map_csv=r"G:\我的雲端硬碟\TPMC\face_surface_map.csv",
        A_ref=1.0e-4,
        L_ref=1.0e-2,
        ref_point_body=(0.0, 0.0, 0.0),
        drag_axis_body=(1.0, 0.0, 0.0),
        side_axis_body=(0.0, 1.0, 0.0),
        lift_axis_body=(0.0, 0.0, 1.0),
        bulk_velocity_world=(7500.0, 0.0, 0.0),
        n_particles=50000,
        seed=42,
        tags=("benchmark", "cube"),
    )

    suite: list[BenchmarkDefinition] = []

    for alt in [300.0, 400.0, 500.0]:
        for yaw in [0.0, 45.0, 90.0]:
            key = f"cube_alt{alt:g}_yaw{yaw:g}"
            desc = f"Cube benchmark at altitude={alt:g} km, yaw={yaw:g} deg"
            case = base_case.clone(
                name=key,
                target_alt_km=alt,
                yaw_deg=yaw,
                pitch_deg=0.0,
                roll_deg=0.0,
            )
            suite.append(
                BenchmarkDefinition(
                    key=key,
                    description=desc,
                    case=case,
                )
            )

    return suite