from __future__ import annotations

from tpmc_v2.aerodynamic_database import export_aerodynamic_database


def main():
    result = export_aerodynamic_database(
        batch_csv_path="runs_v2/batch_results.csv",
        convergence_summary_csv_path="runs_v2/reports/convergence_group_summary.csv",
        output_dir="runs_v2/database",
    )

    print("=== Aerodynamic Database Export ===")
    print("all_rows_csv       :", result["all_rows_csv"])
    print("preferred_rows_csv :", result["preferred_rows_csv"])
    print("meta_json          :", result["meta_json"])
    print("n_all_rows         :", result["n_all_rows"])
    print("n_preferred_rows   :", result["n_preferred_rows"])


if __name__ == "__main__":
    main()