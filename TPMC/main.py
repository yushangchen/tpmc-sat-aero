from __future__ import annotations

import csv
from pathlib import Path
import numpy as np

from geometry.loader import load_stl_mesh, recenter_mesh, scale_mesh, compute_bounding_box
from geometry.transform import rotate_mesh
from physics.gsi import GSIConfig
from physics.source import create_source_plane, sample_points_on_plane
from physics.tracer import trace_particle
from physics.fmf import trace_particle_fmf
from physics.reference import (
    ReferenceConfig,
    body_to_world,
    project_force_axes,
    coefficient_force,
    coefficient_moment,
)
from physics.inflow import InflowConfig, sample_inflow_velocity
from physics.coefficients import compute_dynamic_pressure
from physics.surface_model import (
    SurfaceDefinition,
    SurfaceModel,
    load_face_surface_csv,
)

from atmosphere.base import (
    AtmosphereProvider,
    sample_species_from_state,
    compute_total_incident_flux,
)
from atmosphere.factory import build_atmosphere_provider


def build_surface_model(face_map_csv: str | None) -> SurfaceModel:
    face_to_surface = {}

    if face_map_csv is not None and Path(face_map_csv).exists():
        face_to_surface = load_face_surface_csv(face_map_csv)

    surfaces = {
        "default": SurfaceDefinition(
            name="default",
            gsi=GSIConfig(
                model="cll",
                wall_temperature=300.0,
                alpha_n=0.5,
                alpha_t=0.5,
            ),
        ),
        "body": SurfaceDefinition(
            name="body",
            gsi=GSIConfig(
                model="cll",
                wall_temperature=300.0,
                alpha_n=0.5,
                alpha_t=0.5,
            ),
        ),
        "solar_panel": SurfaceDefinition(
            name="solar_panel",
            gsi=GSIConfig(
                model="cll",
                wall_temperature=330.0,
                alpha_n=0.7,
                alpha_t=0.7,
            ),
        ),
        "antenna": SurfaceDefinition(
            name="antenna",
            gsi=GSIConfig(
                model="diffuse",
                wall_temperature=290.0,
            ),
        ),
        "drag_sail": SurfaceDefinition(
            name="drag_sail",
            gsi=GSIConfig(
                model="diffuse",
                wall_temperature=350.0,
            ),
        ),
        "ram_face": SurfaceDefinition(
            name="ram_face",
            gsi=GSIConfig(
                model="cll",
                wall_temperature=350.0,
                alpha_n=0.8,
                alpha_t=0.8,
            ),
        ),
        "wake_face": SurfaceDefinition(
            name="wake_face",
            gsi=GSIConfig(
                model="diffuse",
                wall_temperature=280.0,
            ),
        ),
        "side_y_plus": SurfaceDefinition(
            name="side_y_plus",
            gsi=GSIConfig(
                model="cll",
                wall_temperature=300.0,
                alpha_n=0.5,
                alpha_t=0.5,
            ),
        ),
        "side_y_minus": SurfaceDefinition(
            name="side_y_minus",
            gsi=GSIConfig(
                model="cll",
                wall_temperature=300.0,
                alpha_n=0.5,
                alpha_t=0.5,
            ),
        ),
        "top_face": SurfaceDefinition(
            name="top_face",
            gsi=GSIConfig(
                model="cll",
                wall_temperature=300.0,
                alpha_n=0.5,
                alpha_t=0.5,
            ),
        ),
        "bottom_face": SurfaceDefinition(
            name="bottom_face",
            gsi=GSIConfig(
                model="cll",
                wall_temperature=300.0,
                alpha_n=0.5,
                alpha_t=0.5,
            ),
        ),
    }

    surface_model = SurfaceModel(
        surfaces=surfaces,
        face_to_surface=face_to_surface,
        default_surface="body",
    )
    surface_model.validate()
    return surface_model


def count_surface_faces(n_faces: int, surface_model: SurfaceModel) -> dict[str, int]:
    counts = {}
    for face_index in range(n_faces):
        name = surface_model.get_surface_name(face_index)
        counts[name] = counts.get(name, 0) + 1
    return counts


def run_stl_case(
    stl_path: str,
    atmosphere_provider: AtmosphereProvider,
    target_alt_km: float,
    target_lat_deg: float,
    target_lon_deg: float,
    epoch: str | None,
    scale_factor: float,
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float,
    solver_mode: str,
    surface_model: SurfaceModel,
    ref: ReferenceConfig,
    bulk_velocity_world: np.ndarray,
    n_particles: int,
    seed: int = 42,
):
    ref.validate()
    surface_model.validate()

    solver_mode = str(solver_mode).lower()
    if solver_mode not in ("tpmc", "fmf"):
        raise ValueError(f"Unsupported solver_mode: {solver_mode}")

    atm = atmosphere_provider.get_state(
        target_alt_km=target_alt_km,
        lat_deg=target_lat_deg,
        lon_deg=target_lon_deg,
        epoch=epoch,
    )

    mesh0 = load_stl_mesh(stl_path)
    mesh0 = scale_mesh(mesh0, scale_factor)
    mesh0 = recenter_mesh(mesh0, target_center=(0.0, 0.0, 0.0))

    mesh = rotate_mesh(
        mesh0,
        roll_deg=roll_deg,
        pitch_deg=pitch_deg,
        yaw_deg=yaw_deg,
        origin=np.array([0.0, 0.0, 0.0]),
    )

    n_faces = len(mesh.faces)
    for face_idx in surface_model.face_to_surface.keys():
        if face_idx >= n_faces:
            raise ValueError(
                f"face_surface_map contains face_index={face_idx}, "
                f"but mesh only has {n_faces} faces."
            )

    surface_counts = count_surface_faces(n_faces, surface_model)

    _, _, bbox_size, _ = compute_bounding_box(mesh.vertices)
    char_length = float(np.max(bbox_size))

    bulk_velocity_world = np.asarray(bulk_velocity_world, dtype=float)
    flow_direction = bulk_velocity_world / np.linalg.norm(bulk_velocity_world)
    V_inf = float(np.linalg.norm(bulk_velocity_world))

    ref_point = body_to_world(
        ref.ref_point_body,
        roll_deg=roll_deg,
        pitch_deg=pitch_deg,
        yaw_deg=yaw_deg,
    )

    margin = 1.0 * char_length
    padding = 0.25 * char_length

    plane = create_source_plane(
        vertices=mesh.vertices,
        flow_direction=flow_direction,
        margin=margin,
        padding=padding,
    )

    rng = np.random.default_rng(seed)
    origins = sample_points_on_plane(plane, n_particles, rng)

    total_flux = compute_total_incident_flux(
        atm=atm,
        bulk_velocity=bulk_velocity_world,
        plane_normal=flow_direction,
    )
    sample_weight = total_flux * plane.area / n_particles

    total_force = np.zeros(3)
    total_moment = np.zeros(3)
    hit_count = 0
    total_bounces = 0

    max_bounces = 10
    eps_shift = max(1e-12, 1e-6 * char_length)

    for origin in origins:
        species = sample_species_from_state(
            atm=atm,
            bulk_velocity=bulk_velocity_world,
            plane_normal=flow_direction,
            rng=rng,
        )

        inflow = InflowConfig(
            bulk_velocity=bulk_velocity_world,
            temperature=atm.temperature_K,
            molecular_mass=species.molecular_mass_kg,
            model="flux_half_range",
            use_thermal_spread=True,
        )

        v_in0 = sample_inflow_velocity(
            inflow=inflow,
            plane_normal=flow_direction,
            rng=rng,
        )

        if solver_mode == "tpmc":  # or "fmf"
            trace = trace_particle(
                ray_origin=origin,
                v_in0=v_in0,
                vertices=mesh.vertices,
                faces=mesh.faces,
                normals=mesh.normals,
                molecular_mass=species.molecular_mass_kg,
                sample_weight=sample_weight,
                reference_point=ref_point,
                rng=rng,
                surface_model=surface_model,
                max_bounces=max_bounces,
                eps_shift=eps_shift,
            )
        else:
            trace = trace_particle_fmf(
                ray_origin=origin,
                v_in0=v_in0,
                vertices=mesh.vertices,
                faces=mesh.faces,
                normals=mesh.normals,
                molecular_mass=species.molecular_mass_kg,
                sample_weight=sample_weight,
                reference_point=ref_point,
                rng=rng,
                surface_model=surface_model,
                eps_shift=eps_shift,
            )

        if trace.bounce_count == 0:
            continue

        hit_count += 1
        total_bounces += trace.bounce_count
        total_force += trace.total_force
        total_moment += trace.total_moment

    rho_inf = atm.rho_total_kg_m3
    q_inf = compute_dynamic_pressure(rho_inf, V_inf)

    A_ref = ref.A_ref
    L_ref = ref.L_ref

    F_drag, F_side, F_lift = project_force_axes(
        total_force_world=total_force,
        roll_deg=roll_deg,
        pitch_deg=pitch_deg,
        yaw_deg=yaw_deg,
        ref=ref,
    )

    Cd = coefficient_force(F_drag, q_inf, A_ref)
    Cy = coefficient_force(F_side, q_inf, A_ref)
    Cl = coefficient_force(F_lift, q_inf, A_ref)

    Cmx = coefficient_moment(float(total_moment[0]), q_inf, A_ref, L_ref)
    Cmy = coefficient_moment(float(total_moment[1]), q_inf, A_ref, L_ref)
    Cmz = coefficient_moment(float(total_moment[2]), q_inf, A_ref, L_ref)

    return {
        "stl_path": str(stl_path),
        "solver_mode": solver_mode,
        "atmosphere_model": atmosphere_provider.provider_name,
        "target_alt_km": float(target_alt_km),
        "target_lat_deg": float(target_lat_deg),
        "target_lon_deg": float(target_lon_deg),
        "selected_alt_km": float(atm.altitude_km),
        "selected_lat_deg": float(atm.lat_deg),
        "selected_lon_deg": float(atm.lon_deg),

        "scale_factor": scale_factor,
        "yaw_deg": yaw_deg,
        "pitch_deg": pitch_deg,
        "roll_deg": roll_deg,
        "n_particles": n_particles,

        "default_surface_name": surface_model.default_surface,
        "surface_counts": str(surface_counts),

        "hit_count": hit_count,
        "hit_ratio": hit_count / n_particles,
        "total_bounces": total_bounces,
        "avg_bounces_per_hit": (total_bounces / hit_count) if hit_count > 0 else 0.0,
        "max_bounces": max_bounces,
        "eps_shift": eps_shift,

        "bbox_x": float(bbox_size[0]),
        "bbox_y": float(bbox_size[1]),
        "bbox_z": float(bbox_size[2]),
        "char_length": char_length,
        "source_area": float(plane.area),
        "sample_weight": float(sample_weight),

        "Fx": float(total_force[0]),
        "Fy": float(total_force[1]),
        "Fz": float(total_force[2]),
        "Mx": float(total_moment[0]),
        "My": float(total_moment[1]),
        "Mz": float(total_moment[2]),

        "rho_inf": float(rho_inf),
        "T_inf": float(atm.temperature_K),
        "exoT_inf": float(atm.exospheric_temperature_K),
        "q_inf": float(q_inf),
        "A_ref": float(A_ref),
        "L_ref": float(L_ref),

        "F_drag": float(F_drag),
        "F_side": float(F_side),
        "F_lift": float(F_lift),

        "Cd": float(Cd),
        "Cy": float(Cy),
        "Cl": float(Cl),

        "Cmx": float(Cmx),
        "Cmy": float(Cmy),
        "Cmz": float(Cmz),

        "n_O": float(atm.species_number_density_m3.get("O", 0.0)),
        "n_N2": float(atm.species_number_density_m3.get("N2", 0.0)),
        "n_O2": float(atm.species_number_density_m3.get("O2", 0.0)),
        "n_He": float(atm.species_number_density_m3.get("He", 0.0)),
        "n_Ar": float(atm.species_number_density_m3.get("Ar", 0.0)),
        "n_H": float(atm.species_number_density_m3.get("H", 0.0)),
        "n_N": float(atm.species_number_density_m3.get("N", 0.0)),
        "atm_source": atm.source,
    }


def save_result_to_csv(result: dict, filename: str = "tpmc_stl_single_run.csv"):
    output_path = Path(__file__).resolve().parent / filename
    fieldnames = list(result.keys())

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(result)

    return output_path


def main():
    atmosphere_config = {
        "type": "nrlmsis_txt",
        "filepath": r"G:\我的雲端硬碟\TPMC\nrlmsis_output.txt",
    }

    stl_path = r"G:\我的雲端硬碟\TPMC\testcube.stl"
    face_map_csv = r"G:\我的雲端硬碟\TPMC\face_surface_map.csv"

    target_alt_km = 500.0
    target_lat_deg = 55.0
    target_lon_deg = 45.0
    epoch = "2026-05-12T00:00:00"

    scale_factor = 0.001
    yaw_deg = 0.0
    pitch_deg = 0.0
    roll_deg = 0.0
    solver_mode = "tpmc"   # "tpmc" or "fmf"
    n_particles = 50000
    seed = 42

    ref = ReferenceConfig(
        A_ref=1.0e-4,
        L_ref=1.0e-2,
        ref_point_body=np.array([0.0, 0.0, 0.0]),
        drag_axis_body=np.array([1.0, 0.0, 0.0]),
        side_axis_body=np.array([0.0, 1.0, 0.0]),
        lift_axis_body=np.array([0.0, 0.0, 1.0]),
    )

    bulk_velocity_world = np.array([7500.0, 0.0, 0.0])

    surface_model = build_surface_model(face_map_csv)
    atmosphere_provider = build_atmosphere_provider(atmosphere_config)

    result = run_stl_case(
        stl_path=stl_path,
        atmosphere_provider=atmosphere_provider,
        target_alt_km=target_alt_km,
        target_lat_deg=target_lat_deg,
        target_lon_deg=target_lon_deg,
        epoch=epoch,
        scale_factor=scale_factor,
        yaw_deg=yaw_deg,
        pitch_deg=pitch_deg,
        roll_deg=roll_deg,
        solver_mode=solver_mode,
        surface_model=surface_model,
        ref=ref,
        bulk_velocity_world=bulk_velocity_world,
        n_particles=n_particles,
        seed=seed,
    )

    print("=== STL Single Run ===")
    print("solver_mode        :", result["solver_mode"])
    print("stl_path           :", result["stl_path"])
    print("atmosphere_model   :", result["atmosphere_model"])
    print("target_alt_km      :", result["target_alt_km"])
    print("target_lat_deg     :", result["target_lat_deg"])
    print("target_lon_deg     :", result["target_lon_deg"])
    print("selected_alt_km    :", result["selected_alt_km"])
    print("selected_lat_deg   :", result["selected_lat_deg"])
    print("selected_lon_deg   :", result["selected_lon_deg"])
    print()

    print("default_surface    :", result["default_surface_name"])
    print("surface_counts     :", result["surface_counts"])
    print()

    print("scale_factor       :", result["scale_factor"])
    print("yaw / pitch / roll :", result["yaw_deg"], result["pitch_deg"], result["roll_deg"])
    print("n_particles        :", result["n_particles"])
    print("hit_count          :", result["hit_count"])
    print("hit_ratio          :", result["hit_ratio"])
    print("total_bounces      :", result["total_bounces"])
    print("avg bounces / hit  :", result["avg_bounces_per_hit"])
    print("max_bounces        :", result["max_bounces"])
    print("eps_shift [m]      :", result["eps_shift"])
    print()

    print("bbox_x [m]         :", result["bbox_x"])
    print("bbox_y [m]         :", result["bbox_y"])
    print("bbox_z [m]         :", result["bbox_z"])
    print("char_length [m]    :", result["char_length"])
    print("A_ref [m^2]        :", result["A_ref"])
    print("L_ref [m]          :", result["L_ref"])
    print("source_area [m^2]  :", result["source_area"])
    print()

    print("rho_inf [kg/m^3]   :", result["rho_inf"])
    print("T_inf [K]          :", result["T_inf"])
    print("exoT_inf [K]       :", result["exoT_inf"])
    print("q_inf [Pa]         :", result["q_inf"])
    print()

    print("n_O  [m^-3]        :", result["n_O"])
    print("n_N2 [m^-3]        :", result["n_N2"])
    print("n_O2 [m^-3]        :", result["n_O2"])
    print("n_He [m^-3]        :", result["n_He"])
    print("n_Ar [m^-3]        :", result["n_Ar"])
    print("n_H  [m^-3]        :", result["n_H"])
    print("n_N  [m^-3]        :", result["n_N"])
    print()

    print("Fx [N]             :", result["Fx"])
    print("Fy [N]             :", result["Fy"])
    print("Fz [N]             :", result["Fz"])
    print("Mx [N m]           :", result["Mx"])
    print("My [N m]           :", result["My"])
    print("Mz [N m]           :", result["Mz"])
    print()

    print("F_drag [N]         :", result["F_drag"])
    print("F_side [N]         :", result["F_side"])
    print("F_lift [N]         :", result["F_lift"])
    print()

    print("Cd                 :", result["Cd"])
    print("Cy                 :", result["Cy"])
    print("Cl                 :", result["Cl"])
    print("Cmx                :", result["Cmx"])
    print("Cmy                :", result["Cmy"])
    print("Cmz                :", result["Cmz"])

    csv_name = f"stl_single_run_{solver_mode}.csv"
    csv_path = save_result_to_csv(result, filename=csv_name)
    print()
    print(f"CSV saved to: {csv_path}")


if __name__ == "__main__":
    import sys
    print("DEBUG USING PYTHON:", sys.executable)
    main()