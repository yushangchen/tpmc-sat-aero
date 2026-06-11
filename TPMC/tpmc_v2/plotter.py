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


def _filter_rows(rows: list[dict], filters: dict[str, float] | None = None) -> list[dict]:
    if not filters:
        return rows

    out = []
    for row in rows:
        keep = True
        for k, v in filters.items():
            x = _to_float_or_none(row.get(k))
            if x is None or abs(x - float(v)) > 1e-12:
                keep = False
                break
        if keep:
            out.append(row)
    return out


def _group_rows(rows: list[dict], group_key: str) -> dict[str, list[dict]]:
    groups = defaultdict(list)
    for row in rows:
        groups[str(row.get(group_key, "NA"))].append(row)
    return groups


def plot_xy_grouped(
    rows: list[dict],
    x_key: str,
    y_key: str,
    group_key: str,
    out_path: str | Path,
    title: str,
    filters: dict[str, float] | None = None,
):
    if not HAS_MATPLOTLIB:
        print(f"[SKIP PLOT] matplotlib not installed: {title}")
        return

    rows = _filter_rows(rows, filters)
    if not rows:
        print(f"[SKIP PLOT] no data: {title}")
        return

    groups = _group_rows(rows, group_key)

    fig, ax = plt.subplots(figsize=(8, 5))

    plotted_any = False
    for group_name, group_rows in groups.items():
        pairs = []
        for row in group_rows:
            x = _to_float_or_none(row.get(x_key))
            y = _to_float_or_none(row.get(y_key))
            if x is None or y is None:
                continue
            pairs.append((x, y))

        if not pairs:
            continue

        pairs.sort(key=lambda t: t[0])
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        ax.plot(xs, ys, marker="o", label=f"{group_key}={group_name}")
        plotted_any = True

    if not plotted_any:
        plt.close(fig)
        print(f"[SKIP PLOT] no valid numeric data: {title}")
        return

    ax.set_xlabel(x_key)
    ax.set_ylabel(y_key)
    ax.set_title(title)
    ax.grid(True)
    ax.legend()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"[PLOT SAVED] {out_path}")


def generate_standard_plots(
    batch_csv_path: str | Path,
    output_dir: str | Path = "runs_v2/plots",
):
    rows = load_rows(batch_csv_path)

    if not rows:
        print("[SKIP PLOT] batch_results.csv not found or empty.")
        return

    output_dir = Path(output_dir)

    plot_xy_grouped(
        rows=rows,
        x_key="yaw_deg",
        y_key="Cd",
        group_key="target_alt_km",
        out_path=output_dir / "cd_vs_yaw.png",
        title="Cd vs yaw",
        filters={"pitch_deg": 0.0, "roll_deg": 0.0},
    )

    plot_xy_grouped(
        rows=rows,
        x_key="target_alt_km",
        y_key="Cd",
        group_key="yaw_deg",
        out_path=output_dir / "cd_vs_altitude.png",
        title="Cd vs altitude",
        filters={"pitch_deg": 0.0, "roll_deg": 0.0},
    )

    plot_xy_grouped(
        rows=rows,
        x_key="yaw_deg",
        y_key="F_drag",
        group_key="target_alt_km",
        out_path=output_dir / "drag_vs_yaw.png",
        title="F_drag vs yaw",
        filters={"pitch_deg": 0.0, "roll_deg": 0.0},
    )

    plot_xy_grouped(
        rows=rows,
        x_key="n_particles",
        y_key="hit_ratio",
        group_key="target_alt_km",
        out_path=output_dir / "hitratio_vs_particles.png",
        title="hit_ratio vs n_particles",
    )