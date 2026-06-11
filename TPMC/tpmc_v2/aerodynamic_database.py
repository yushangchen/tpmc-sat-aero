from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import csv
import json
import hashlib
from typing import Any


def _to_float_or_none(value: Any):
    try:
        return float(value)
    except Exception:
        return None


def _to_int_or_none(value: Any):
    try:
        return int(float(value))
    except Exception:
        return None


def _stable_short_hash(payload: dict[str, Any], n: int = 8) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:n]


def _load_csv_rows(filepath: str | Path) -> list[dict]:
    filepath = Path(filepath)
    if not filepath.exists():
        return []

    rows: list[dict] = []
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _save_csv(rows: list[dict], filepath: str | Path) -> None:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _save_json(payload: dict, filepath: str | Path) -> None:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _build_geometry_id(row: dict) -> str:
    stl_path = str(row.get("stl_path", "unknown"))
    A_ref = row.get("A_ref", "")
    L_ref = row.get("L_ref", "")

    stem = Path(stl_path).stem if stl_path else "unknown_geometry"
    h = _stable_short_hash(
        {
            "stl_path": stl_path,
            "A_ref": A_ref,
            "L_ref": L_ref,
        }
    )
    return f"{stem}_{h}"


def _build_surface_model_id(row: dict) -> str:
    default_surface_name = str(row.get("default_surface_name", "unknown"))
    surface_counts = str(row.get("surface_counts", ""))

    h = _stable_short_hash(
        {
            "default_surface_name": default_surface_name,
            "surface_counts": surface_counts,
        }
    )
    return f"{default_surface_name}_{h}"


def _build_atmosphere_id(row: dict) -> str:
    atmosphere_model = str(row.get("atmosphere_model", "unknown"))
    target_lat_deg = row.get("target_lat_deg", "")
    target_lon_deg = row.get("target_lon_deg", "")

    h = _stable_short_hash(
        {
            "atmosphere_model": atmosphere_model,
            "target_lat_deg": target_lat_deg,
            "target_lon_deg": target_lon_deg,
        }
    )
    return f"{atmosphere_model}_{h}"


def _group_key_for_preferred(row: dict) -> tuple:
    return (
        _build_geometry_id(row),
        _build_surface_model_id(row),
        _build_atmosphere_id(row),
        row.get("target_alt_km", ""),
        row.get("target_lat_deg", ""),
        row.get("target_lon_deg", ""),
        row.get("yaw_deg", ""),
        row.get("pitch_deg", ""),
        row.get("roll_deg", ""),
    )


def _build_convergence_index(summary_rows: list[dict]) -> dict[tuple, dict]:
    idx: dict[tuple, dict] = {}
    for row in summary_rows:
        key = (
            str(row.get("stl_path", "")),
            str(row.get("target_alt_km", "")),
            str(row.get("yaw_deg", "")),
            str(row.get("pitch_deg", "")),
            str(row.get("roll_deg", "")),
        )
        idx[key] = row
    return idx


def _quality_flag_from_cd_rel_error(cd_rel_error_percent: float | None) -> str:
    if cd_rel_error_percent is None:
        return "undefined"

    if cd_rel_error_percent <= 1.0:
        return "good"
    if cd_rel_error_percent <= 5.0:
        return "acceptable"
    return "check"


def _canonicalize_row(
    row: dict,
    convergence_index: dict[tuple, dict],
    is_preferred: bool,
) -> dict:
    geometry_id = _build_geometry_id(row)
    surface_model_id = _build_surface_model_id(row)
    atmosphere_id = _build_atmosphere_id(row)

    conv_key = (
        str(row.get("stl_path", "")),
        str(row.get("target_alt_km", "")),
        str(row.get("yaw_deg", "")),
        str(row.get("pitch_deg", "")),
        str(row.get("roll_deg", "")),
    )
    conv = convergence_index.get(conv_key, {})

    cd_rel_error_percent = _to_float_or_none(conv.get("Cd_rel_error_percent"))
    quality_flag = _quality_flag_from_cd_rel_error(cd_rel_error_percent)

    out = {
        "case_name": row.get("case_name", ""),
        "case_id": row.get("case_id", ""),

        "geometry_id": geometry_id,
        "surface_model_id": surface_model_id,
        "atmosphere_id": atmosphere_id,

        "stl_path": row.get("stl_path", ""),
        "default_surface_name": row.get("default_surface_name", ""),
        "surface_counts": row.get("surface_counts", ""),
        "atmosphere_model": row.get("atmosphere_model", ""),
        "atm_source": row.get("atm_source", ""),

        "target_alt_km": _to_float_or_none(row.get("target_alt_km")),
        "target_lat_deg": _to_float_or_none(row.get("target_lat_deg")),
        "target_lon_deg": _to_float_or_none(row.get("target_lon_deg")),
        "selected_alt_km": _to_float_or_none(row.get("selected_alt_km")),
        "selected_lat_deg": _to_float_or_none(row.get("selected_lat_deg")),
        "selected_lon_deg": _to_float_or_none(row.get("selected_lon_deg")),

        "yaw_deg": _to_float_or_none(row.get("yaw_deg")),
        "pitch_deg": _to_float_or_none(row.get("pitch_deg")),
        "roll_deg": _to_float_or_none(row.get("roll_deg")),

        "A_ref": _to_float_or_none(row.get("A_ref")),
        "L_ref": _to_float_or_none(row.get("L_ref")),
        "scale_factor": _to_float_or_none(row.get("scale_factor")),

        "n_particles": _to_int_or_none(row.get("n_particles")),
        "hit_count": _to_int_or_none(row.get("hit_count")),
        "hit_ratio": _to_float_or_none(row.get("hit_ratio")),
        "total_bounces": _to_int_or_none(row.get("total_bounces")),
        "avg_bounces_per_hit": _to_float_or_none(row.get("avg_bounces_per_hit")),

        "rho_inf": _to_float_or_none(row.get("rho_inf")),
        "T_inf": _to_float_or_none(row.get("T_inf")),
        "exoT_inf": _to_float_or_none(row.get("exoT_inf")),
        "q_inf": _to_float_or_none(row.get("q_inf")),

        "Cd": _to_float_or_none(row.get("Cd")),
        "Cy": _to_float_or_none(row.get("Cy")),
        "Cl": _to_float_or_none(row.get("Cl")),
        "Cmx": _to_float_or_none(row.get("Cmx")),
        "Cmy": _to_float_or_none(row.get("Cmy")),
        "Cmz": _to_float_or_none(row.get("Cmz")),

        "F_drag": _to_float_or_none(row.get("F_drag")),
        "F_side": _to_float_or_none(row.get("F_side")),
        "F_lift": _to_float_or_none(row.get("F_lift")),

        "Fx": _to_float_or_none(row.get("Fx")),
        "Fy": _to_float_or_none(row.get("Fy")),
        "Fz": _to_float_or_none(row.get("Fz")),
        "Mx": _to_float_or_none(row.get("Mx")),
        "My": _to_float_or_none(row.get("My")),
        "Mz": _to_float_or_none(row.get("Mz")),

        "n_O": _to_float_or_none(row.get("n_O")),
        "n_N2": _to_float_or_none(row.get("n_N2")),
        "n_O2": _to_float_or_none(row.get("n_O2")),
        "n_He": _to_float_or_none(row.get("n_He")),
        "n_Ar": _to_float_or_none(row.get("n_Ar")),
        "n_H": _to_float_or_none(row.get("n_H")),
        "n_N": _to_float_or_none(row.get("n_N")),

        "reference_n_particles": _to_int_or_none(conv.get("reference_n_particles")),
        "Cd_rel_error_percent": cd_rel_error_percent,
        "Cy_rel_error_percent": _to_float_or_none(conv.get("Cy_rel_error_percent")),
        "Cl_rel_error_percent": _to_float_or_none(conv.get("Cl_rel_error_percent")),
        "Cmx_rel_error_percent": _to_float_or_none(conv.get("Cmx_rel_error_percent")),
        "Cmy_rel_error_percent": _to_float_or_none(conv.get("Cmy_rel_error_percent")),
        "Cmz_rel_error_percent": _to_float_or_none(conv.get("Cmz_rel_error_percent")),
        "F_drag_rel_error_percent": _to_float_or_none(conv.get("F_drag_rel_error_percent")),

        "quality_flag": quality_flag,
        "is_preferred": int(bool(is_preferred)),
        "tags": row.get("tags", ""),
    }

    return out


def export_aerodynamic_database(
    batch_csv_path: str | Path,
    convergence_summary_csv_path: str | Path | None = None,
    output_dir: str | Path = "runs_v2/database",
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_rows = _load_csv_rows(batch_csv_path)
    if not batch_rows:
        raise ValueError(f"No batch rows found in: {batch_csv_path}")

    convergence_rows = (
        _load_csv_rows(convergence_summary_csv_path)
        if convergence_summary_csv_path is not None
        else []
    )
    convergence_index = _build_convergence_index(convergence_rows)

    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in batch_rows:
        grouped[_group_key_for_preferred(row)].append(row)

    preferred_row_ids: set[str] = set()
    preferred_source_rows: list[dict] = []

    for _, rows in grouped.items():
        rows_sorted = sorted(
            rows,
            key=lambda r: _to_int_or_none(r.get("n_particles")) or -1
        )
        preferred = rows_sorted[-1]
        preferred_source_rows.append(preferred)
        preferred_row_ids.add(str(preferred.get("case_id", "")))

    database_all_rows = []
    for row in batch_rows:
        database_all_rows.append(
            _canonicalize_row(
                row=row,
                convergence_index=convergence_index,
                is_preferred=(str(row.get("case_id", "")) in preferred_row_ids),
            )
        )

    database_preferred_rows = []
    for row in preferred_source_rows:
        database_preferred_rows.append(
            _canonicalize_row(
                row=row,
                convergence_index=convergence_index,
                is_preferred=True,
            )
        )

    database_preferred_rows.sort(
        key=lambda r: (
            r.get("target_alt_km") if r.get("target_alt_km") is not None else -1.0,
            r.get("yaw_deg") if r.get("yaw_deg") is not None else -1.0,
            r.get("pitch_deg") if r.get("pitch_deg") is not None else -1.0,
            r.get("roll_deg") if r.get("roll_deg") is not None else -1.0,
        )
    )

    database_all_csv = output_dir / "aero_database_all.csv"
    database_preferred_csv = output_dir / "aero_database_preferred.csv"
    meta_json = output_dir / "aero_database_meta.json"

    _save_csv(database_all_rows, database_all_csv)
    _save_csv(database_preferred_rows, database_preferred_csv)

    meta = {
        "n_all_rows": len(database_all_rows),
        "n_preferred_rows": len(database_preferred_rows),
        "geometry_ids": sorted({row["geometry_id"] for row in database_all_rows}),
        "surface_model_ids": sorted({row["surface_model_id"] for row in database_all_rows}),
        "atmosphere_ids": sorted({row["atmosphere_id"] for row in database_all_rows}),
        "altitudes_km": sorted({
            row["target_alt_km"] for row in database_all_rows
            if row["target_alt_km"] is not None
        }),
        "yaw_deg": sorted({
            row["yaw_deg"] for row in database_all_rows
            if row["yaw_deg"] is not None
        }),
        "pitch_deg": sorted({
            row["pitch_deg"] for row in database_all_rows
            if row["pitch_deg"] is not None
        }),
        "roll_deg": sorted({
            row["roll_deg"] for row in database_all_rows
            if row["roll_deg"] is not None
        }),
        "particle_levels": sorted({
            row["n_particles"] for row in database_all_rows
            if row["n_particles"] is not None
        }),
        "files": {
            "all_rows_csv": str(database_all_csv),
            "preferred_rows_csv": str(database_preferred_csv),
        },
    }
    _save_json(meta, meta_json)

    return {
        "all_rows_csv": str(database_all_csv),
        "preferred_rows_csv": str(database_preferred_csv),
        "meta_json": str(meta_json),
        "n_all_rows": len(database_all_rows),
        "n_preferred_rows": len(database_preferred_rows),
    }