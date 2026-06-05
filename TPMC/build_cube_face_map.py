from __future__ import annotations

from pathlib import Path
import csv
import numpy as np

from geometry.loader import load_stl_mesh


def classify_face_by_normal(normal: np.ndarray) -> str:
    n = np.asarray(normal, dtype=float)
    idx = int(np.argmax(np.abs(n)))
    sign = 1.0 if n[idx] >= 0.0 else -1.0

    if idx == 0:
        return "x_plus" if sign > 0 else "x_minus"
    if idx == 1:
        return "y_plus" if sign > 0 else "y_minus"
    if idx == 2:
        return "z_plus" if sign > 0 else "z_minus"

    raise RuntimeError("Unexpected normal classification.")


def main():
    stl_path = Path(r"G:\我的雲端硬碟\TPMC\testcube.stl")
    output_csv = Path(r"G:\我的雲端硬碟\TPMC\face_surface_map.csv")

    mesh = load_stl_mesh(stl_path)

    rows = []
    counts = {}

    for face_index, normal in enumerate(mesh.normals):
        surface_name = classify_face_by_normal(normal)
        rows.append({
            "face_index": face_index,
            "surface_name": surface_name,
        })
        counts[surface_name] = counts.get(surface_name, 0) + 1

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["face_index", "surface_name"])
        writer.writeheader()
        writer.writerows(rows)

    print("Cube face map written to:", output_csv)
    print("Surface counts:")
    for k in sorted(counts.keys()):
        print(f"  {k}: {counts[k]}")


if __name__ == "__main__":
    main()