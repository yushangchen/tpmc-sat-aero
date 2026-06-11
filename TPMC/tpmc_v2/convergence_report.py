from __future__ import annotations

from pathlib import Path
import csv
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ModuleNotFoundError:
    plt = None
    HAS_MATPLOTLIB = False


NUMERIC_GROUP_KEYS = [
    "target_alt_km",
    "yaw_deg",
    "pitch_deg",
    "roll_deg",
]

METRIC_KEYS = [
    "Cd",
    "Cy",
    "Cl",
    "Cmx",
    "Cmy",
    "Cmz",
    "F_drag",
    "F_side",
    "F_lift",
    "hit_ratio",
]


def _to_float_or_none(value):
    try:
        return float(value)
    except Exception:
        return None


def load_rows(csv_path: str | Path) -> list[dict]:
    rows = []
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return rows

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _group_key(row: dict) -> tuple:
    return (
        row.get("stl_path", ""),
        row.get("target_alt_km", ""),
        row.get("yaw_deg", ""),
        row.get("pitch_deg", ""),
        row.get("roll_deg", ""),
    )


def _group_label(row: dict) -> str:
    alt = row.get("target_alt_km", "NA")
    yaw = row.get("yaw_deg", "NA")
    pitch = row.get("pitch_deg", "NA")
    roll = row.get("roll_deg", "NA")
    return f"alt{alt}_yaw{yaw}_pitch{pitch}_roll{roll}"


def group_rows(rows: list[dict]) -> dict[tuple, list[dict]]:
    groups = defaultdict(list)
    for row in rows:
        key = _group_key(row)
        groups[key].append(row)

    for key in groups:
        groups[key].sort(key=lambda r: _to_float_or_none(r.get("n_particles")) or -1.0)

    return groups


def build_convergence_rows(rows: list[dict]) -> list[dict]:
    groups = group_rows(rows)
    out_rows: list[dict] = []

    for _, group in groups.items():
        if len(group) == 0:
            continue

        reference_row = max(
            group,
            key=lambda r: _to_float_or_none(r.get("n_particles")) or -1.0
        )
        ref_n_particles = _to_float_or_none(reference_row.get("n_particles"))

        for row in group:
            n_particles = _to_float_or_none(row.get("n_particles"))
            base_info = {
                "group_label": _group_label(row),
                "stl_path": row.get("stl_path", ""),
                "target_alt_km": row.get("target_alt_km", ""),
                "yaw_deg": row.get("yaw_deg", ""),
                "pitch_deg": row.get("pitch_deg", ""),
                "roll_deg": row.get("roll_deg", ""),
                "n_particles": n_particles,
                "reference_n_particles": ref_n_particles,
            }

            for metric in METRIC_KEYS:
                value = _to_float_or_none(row.get(metric))
                ref_value = _to_float_or_none(reference_row.get(metric))

                abs_error = None
                rel_error_percent = None

                if value is not None and ref_value is not None:
                    abs_error = abs(value - ref_value)
                    if abs(ref_value) > 1e-12:
                        rel_error_percent = abs_error / abs(ref_value) * 100.0
                    else:
                        rel_error_percent = None

                out_rows.append({
                    **base_info,
                    "metric": metric,
                    "value": value,
                    "reference_value": ref_value,
                    "abs_error": abs_error,
                    "rel_error_percent": rel_error_percent,
                })

    return out_rows


def build_group_summary(rows: list[dict]) -> list[dict]:
    groups = group_rows(rows)
    summary_rows: list[dict] = []

    for _, group in groups.items():
        if len(group) == 0:
            continue

        group_sorted = sorted(
            group,
            key=lambda r: _to_float_or_none(r.get("n_particles")) or -1.0
        )

        row_min = group_sorted[0]
        row_ref = group_sorted[-1]

        def rel_err(metric: str):
            v0 = _to_float_or_none(row_min.get(metric))
            vr = _to_float_or_none(row_ref.get(metric))
            if v0 is None or vr is None:
                return None
            if abs(vr) <= 1e-30:
                return None
            return abs(v0 - vr) / abs(vr) * 100.0

        summary_rows.append({
            "group_label": _group_label(row_ref),
            "stl_path": row_ref.get("stl_path", ""),
            "target_alt_km": row_ref.get("target_alt_km", ""),
            "yaw_deg": row_ref.get("yaw_deg", ""),
            "pitch_deg": row_ref.get("pitch_deg", ""),
            "roll_deg": row_ref.get("roll_deg", ""),
            "min_n_particles": _to_float_or_none(row_min.get("n_particles")),
            "reference_n_particles": _to_float_or_none(row_ref.get("n_particles")),
            "Cd_min": _to_float_or_none(row_min.get("Cd")),
            "Cd_ref": _to_float_or_none(row_ref.get("Cd")),
            "Cd_rel_error_percent": rel_err("Cd"),
            "Cy_rel_error_percent": rel_err("Cy"),
            "Cl_rel_error_percent": rel_err("Cl"),
            "Cmx_rel_error_percent": rel_err("Cmx"),
            "Cmy_rel_error_percent": rel_err("Cmy"),
            "Cmz_rel_error_percent": rel_err("Cmz"),
            "F_drag_rel_error_percent": rel_err("F_drag"),
            "hit_ratio_min": _to_float_or_none(row_min.get("hit_ratio")),
            "hit_ratio_ref": _to_float_or_none(row_ref.get("hit_ratio")),
        })

    summary_rows.sort(
        key=lambda r: (
            _to_float_or_none(r.get("target_alt_km")) or 0.0,
            _to_float_or_none(r.get("yaw_deg")) or 0.0,
        )
    )
    return summary_rows


def save_csv(rows: list[dict], filepath: str | Path):
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _filter_rows(rows: list[dict], **conditions) -> list[dict]:
    out = []
    for row in rows:
        keep = True
        for key, target in conditions.items():
            value = _to_float_or_none(row.get(key))
            if value is None or abs(value - float(target)) > 1e-12:
                keep = False
                break
        if keep:
            out.append(row)
    return out


def _group_by_key(rows: list[dict], key: str) -> dict[str, list[dict]]:
    groups = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, "NA"))].append(row)
    return groups


def _plot_metric_vs_particles(
    rows: list[dict],
    metric_key: str,
    out_path: str | Path,
    title: str,
):
    if not HAS_MATPLOTLIB:
        print(f"[SKIP PLOT] matplotlib not installed: {title}")
        return

    if not rows:
        print(f"[SKIP PLOT] no data: {title}")
        return

    groups = _group_by_key(rows, "yaw_deg")

    fig, ax = plt.subplots(figsize=(8, 5))
    plotted_any = False

    for yaw, group_rows in groups.items():
        pairs = []
        for row in group_rows:
            x = _to_float_or_none(row.get("n_particles"))
            y = _to_float_or_none(row.get(metric_key))
            if x is None or y is None:
                continue
            pairs.append((x, y))

        if not pairs:
            continue

        pairs.sort(key=lambda t: t[0])
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        ax.plot(xs, ys, marker="o", label=f"yaw={yaw}")
        plotted_any = True

    if not plotted_any:
        plt.close(fig)
        print(f"[SKIP PLOT] no valid numeric data: {title}")
        return

    ax.set_xscale("log")
    ax.set_xlabel("n_particles")
    ax.set_ylabel(metric_key)
    ax.set_title(title)
    ax.grid(True)
    ax.legend()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[PLOT SAVED] {out_path}")


def _plot_rel_error_vs_particles(
    convergence_rows: list[dict],
    metric_key: str,
    altitude_km: float,
    out_path: str | Path,
):
    if not HAS_MATPLOTLIB:
        print(f"[SKIP PLOT] matplotlib not installed: rel error {metric_key}")
        return

    rows = [
        r for r in convergence_rows
        if r.get("metric") == metric_key
        and (_to_float_or_none(r.get("target_alt_km")) is not None)
        and abs(_to_float_or_none(r.get("target_alt_km")) - altitude_km) <= 1e-12
    ]

    if not rows:
        print(f"[SKIP PLOT] no convergence data for alt={altitude_km}, metric={metric_key}")
        return

    groups = _group_by_key(rows, "yaw_deg")

    fig, ax = plt.subplots(figsize=(8, 5))
    plotted_any = False

    for yaw, group_rows in groups.items():
        pairs = []
        for row in group_rows:
            x = _to_float_or_none(row.get("n_particles"))
            y = _to_float_or_none(row.get("rel_error_percent"))
            if x is None or y is None:
                continue
            pairs.append((x, y))

        if not pairs:
            continue

        pairs.sort(key=lambda t: t[0])
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        ax.plot(xs, ys, marker="o", label=f"yaw={yaw}")
        plotted_any = True

    if not plotted_any:
        plt.close(fig)
        print(f"[SKIP PLOT] no valid rel error data for alt={altitude_km}, metric={metric_key}")
        return

    ax.set_xscale("log")
    ax.set_xlabel("n_particles")
    ax.set_ylabel("relative error [%]")
    ax.set_title(f"{metric_key} relative error vs n_particles @ alt={altitude_km:g} km")
    ax.grid(True)
    ax.legend()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[PLOT SAVED] {out_path}")


def write_markdown_report(summary_rows: list[dict], filepath: str | Path):
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if not summary_rows:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Convergence Report\n\nNo data available.\n")
        return

    worst_cd = sorted(
        [r for r in summary_rows if r.get("Cd_rel_error_percent") is not None],
        key=lambda r: r["Cd_rel_error_percent"],
        reverse=True,
    )[:10]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# TPMC Convergence Report\n\n")
        f.write("Reference for each group is the case with the largest `n_particles`.\n\n")
        f.write(f"Total groups: **{len(summary_rows)}**\n\n")

        f.write("## Worst 10 groups by Cd relative error\n\n")
        f.write("| altitude [km] | yaw [deg] | min n_particles | ref n_particles | Cd rel error [%] |\n")
        f.write("|---:|---:|---:|---:|---:|\n")
        for row in worst_cd:
            f.write(
                f"| {row.get('target_alt_km')} "
                f"| {row.get('yaw_deg')} "
                f"| {row.get('min_n_particles')} "
                f"| {row.get('reference_n_particles')} "
                f"| {row.get('Cd_rel_error_percent'):.6f} |\n"
            )

        f.write("\n## Notes\n\n")
        f.write("- Large `Cy`, `Cl`, `Cmx`, `Cmy`, `Cmz` relative errors at low magnitude may still be Monte Carlo noise.\n")
        f.write("- `Cd` and `F_drag` are usually the most physically informative convergence indicators for the current cube benchmark.\n")


def generate_convergence_reports(
    batch_csv_path: str | Path,
    output_dir: str | Path = "runs_v2/reports",
):
    output_dir = Path(output_dir)
    rows = load_rows(batch_csv_path)

    if not rows:
        print("[SKIP REPORT] batch_results.csv not found or empty.")
        return

    convergence_rows = build_convergence_rows(rows)
    summary_rows = build_group_summary(rows)

    save_csv(convergence_rows, output_dir / "convergence_long.csv")
    save_csv(summary_rows, output_dir / "convergence_group_summary.csv")
    write_markdown_report(summary_rows, output_dir / "convergence_report.md")

    print(f"[REPORT SAVED] {output_dir / 'convergence_long.csv'}")
    print(f"[REPORT SAVED] {output_dir / 'convergence_group_summary.csv'}")
    print(f"[REPORT SAVED] {output_dir / 'convergence_report.md'}")

    altitudes = sorted({
        _to_float_or_none(r.get("target_alt_km"))
        for r in rows
        if _to_float_or_none(r.get("target_alt_km")) is not None
    })

    for alt in altitudes:
        alt_rows = _filter_rows(rows, target_alt_km=alt, pitch_deg=0.0, roll_deg=0.0)

        _plot_metric_vs_particles(
            rows=alt_rows,
            metric_key="Cd",
            out_path=output_dir / f"cd_vs_nparticles_alt{alt:g}.png",
            title=f"Cd vs n_particles @ alt={alt:g} km",
        )

        _plot_metric_vs_particles(
            rows=alt_rows,
            metric_key="hit_ratio",
            out_path=output_dir / f"hitratio_vs_nparticles_alt{alt:g}.png",
            title=f"hit_ratio vs n_particles @ alt={alt:g} km",
        )

        _plot_rel_error_vs_particles(
            convergence_rows=convergence_rows,
            metric_key="Cd",
            altitude_km=alt,
            out_path=output_dir / f"cd_relerr_vs_nparticles_alt{alt:g}.png",
        )

        _plot_rel_error_vs_particles(
            convergence_rows=convergence_rows,
            metric_key="F_drag",
            altitude_km=alt,
            out_path=output_dir / f"fdrag_relerr_vs_nparticles_alt{alt:g}.png",
        )