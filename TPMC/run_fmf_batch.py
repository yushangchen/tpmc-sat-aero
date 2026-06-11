from __future__ import annotations

from tpmc_v2.case_schema import TPMCCase
from tpmc_v2.case_manager import BatchCaseManager
from tpmc_v2.plotter import generate_standard_plots
from tpmc_v2.convergence_report import generate_convergence_reports
from tpmc_v2.aerodynamic_database import export_aerodynamic_database


def build_cases() -> list[TPMCCase]:
    base_case = TPMCCase(
        name="cube_fmf",
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
        solver_mode="fmf",
        A_ref=1.0e-4,
        L_ref=1.0e-2,
        ref_point_body=(0.0, 0.0, 0.0),
        drag_axis_body=(1.0, 0.0, 0.0),
        side_axis_body=(0.0, 1.0, 0.0),
        lift_axis_body=(0.0, 0.0, 1.0),
        bulk_velocity_world=(7500.0, 0.0, 0.0),
        n_particles=50000,
        seed=42,
        tags=("v3", "cube", "fmf"),
    )

    altitude_list = [300.0, 400.0, 500.0]
    yaw_list = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
    particle_list = [10000, 50000, 100000]

    cases: list[TPMCCase] = []

    for alt in altitude_list:
        for yaw in yaw_list:
            for n_particles in particle_list:
                case_name = f"cube_fmf_alt{alt:g}_yaw{yaw:g}_np{n_particles}"
                case = base_case.clone(
                    name=case_name,
                    target_alt_km=alt,
                    yaw_deg=yaw,
                    pitch_deg=0.0,
                    roll_deg=0.0,
                    n_particles=n_particles,
                    tags=("v3", "cube", "fmf", "grid"),
                )
                cases.append(case)

    return cases


def main():
    cases = build_cases()

    manager = BatchCaseManager(work_dir="runs_fmf_v1")

    results = manager.run(
        cases=cases,
        max_workers=4,
        resume=True,
    )

    print()
    print(f"FMF batch finished. New completed cases: {len(results)}")

    try:
        generate_standard_plots(
            batch_csv_path="runs_fmf_v1/batch_results.csv",
            output_dir="runs_fmf_v1/plots",
        )
    except Exception as e:
        print(f"[WARN] standard plotting failed, but batch results are kept: {e}")

    try:
        generate_convergence_reports(
            batch_csv_path="runs_fmf_v1/batch_results.csv",
            output_dir="runs_fmf_v1/reports",
        )
    except Exception as e:
        print(f"[WARN] convergence report failed, but batch results are kept: {e}")

    try:
        db_result = export_aerodynamic_database(
            batch_csv_path="runs_fmf_v1/batch_results.csv",
            convergence_summary_csv_path="runs_fmf_v1/reports/convergence_group_summary.csv",
            output_dir="runs_fmf_v1/database",
        )
        print("[DATABASE SAVED] all_rows_csv      :", db_result["all_rows_csv"])
        print("[DATABASE SAVED] preferred_rows_csv:", db_result["preferred_rows_csv"])
        print("[DATABASE SAVED] meta_json         :", db_result["meta_json"])
    except Exception as e:
        print(f"[WARN] aerodynamic database export failed, but batch results are kept: {e}")


if __name__ == "__main__":
    main()