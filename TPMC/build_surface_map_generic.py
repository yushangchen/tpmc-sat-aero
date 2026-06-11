from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from geometry.loader import load_stl_mesh


def normalize(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n <= 0.0:
        return v.copy()
    return v / n


def compute_face_centroids(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    tri = vertices[faces]
    return tri.mean(axis=1)


def compute_face_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    tri = vertices[faces]
    e1 = tri[:, 1, :] - tri[:, 0, :]
    e2 = tri[:, 2, :] - tri[:, 0, :]
    normals = np.cross(e1, e2)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    valid = norms[:, 0] > 0.0
    normals_out = np.zeros_like(normals)
    normals_out[valid] = normals[valid] / norms[valid]
    return normals_out


def compute_face_areas(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    tri = vertices[faces]
    e1 = tri[:, 1, :] - tri[:, 0, :]
    e2 = tri[:, 2, :] - tri[:, 0, :]
    return 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)


def axis_to_vector(text: str) -> np.ndarray:
    mapping = {
        "+x": np.array([1.0, 0.0, 0.0]),
        "-x": np.array([-1.0, 0.0, 0.0]),
        "+y": np.array([0.0, 1.0, 0.0]),
        "-y": np.array([0.0, -1.0, 0.0]),
        "+z": np.array([0.0, 0.0, 1.0]),
        "-z": np.array([0.0, 0.0, -1.0]),
    }
    if text not in mapping:
        raise ValueError(f"Unsupported axis direction: {text}")
    return mapping[text]


def parse_direction(direction: Any) -> np.ndarray:
    if isinstance(direction, str):
        return axis_to_vector(direction)
    if isinstance(direction, (list, tuple)) and len(direction) == 3:
        return normalize(np.array(direction, dtype=float))
    raise ValueError(f"Invalid direction: {direction}")


def angle_deg_between(a: np.ndarray, b: np.ndarray) -> float:
    a = normalize(a)
    b = normalize(b)
    dot = float(np.clip(np.dot(a, b), -1.0, 1.0))
    return float(np.degrees(np.arccos(dot)))


def check_normal_cone(normal: np.ndarray, rule_cfg: dict) -> bool:
    if "normal_cone" not in rule_cfg:
        return True

    cfg = rule_cfg["normal_cone"]
    direction = parse_direction(cfg["direction"])
    max_angle_deg = float(cfg.get("max_angle_deg", 15.0))
    angle = angle_deg_between(normal, direction)
    return angle <= max_angle_deg


def check_dominant_axis(normal: np.ndarray, rule_cfg: dict) -> bool:
    if "dominant_axis" not in rule_cfg:
        return True

    cfg = rule_cfg["dominant_axis"]
    expected = str(cfg["axis"]).lower()
    min_abs_component = float(cfg.get("min_abs_component", 0.8))

    idx = int(np.argmax(np.abs(normal)))
    actual_axis = ["x", "y", "z"][idx]
    actual_abs = abs(float(normal[idx]))

    if actual_axis != expected:
        return False
    if actual_abs < min_abs_component:
        return False

    if "sign" in cfg:
        sign = str(cfg["sign"]).lower()
        if sign not in ("plus", "minus"):
            raise ValueError(f"dominant_axis.sign must be plus/minus, got {sign}")
        if sign == "plus" and normal[idx] <= 0.0:
            return False
        if sign == "minus" and normal[idx] >= 0.0:
            return False

    return True


def check_centroid_box(centroid: np.ndarray, rule_cfg: dict) -> bool:
    if "centroid_box" not in rule_cfg:
        return True

    cfg = rule_cfg["centroid_box"]
    box_min = cfg.get("min", None)
    box_max = cfg.get("max", None)

    c = np.asarray(centroid, dtype=float)

    if box_min is not None:
        box_min = np.array(
            [-np.inf if v is None else float(v) for v in box_min],
            dtype=float,
        )
        if np.any(c < box_min):
            return False

    if box_max is not None:
        box_max = np.array(
            [np.inf if v is None else float(v) for v in box_max],
            dtype=float,
        )
        if np.any(c > box_max):
            return False

    return True


def check_halfspaces(centroid: np.ndarray, rule_cfg: dict) -> bool:
    if "halfspaces" not in rule_cfg:
        return True

    c = np.asarray(centroid, dtype=float)
    axis_map = {"x": 0, "y": 1, "z": 2}

    for cond in rule_cfg["halfspaces"]:
        axis = str(cond["axis"]).lower()
        op = str(cond["op"])
        value = float(cond["value"])

        if axis not in axis_map:
            raise ValueError(f"Unsupported halfspace axis: {axis}")

        x = float(c[axis_map[axis]])

        if op == ">":
            ok = x > value
        elif op == ">=":
            ok = x >= value
        elif op == "<":
            ok = x < value
        elif op == "<=":
            ok = x <= value
        else:
            raise ValueError(f"Unsupported halfspace operator: {op}")

        if not ok:
            return False

    return True


def check_area_range(area: float, rule_cfg: dict) -> bool:
    if "area_range" not in rule_cfg:
        return True

    cfg = rule_cfg["area_range"]
    area_min = cfg.get("min", None)
    area_max = cfg.get("max", None)

    if area_min is not None and area < float(area_min):
        return False
    if area_max is not None and area > float(area_max):
        return False

    return True


def matches_rule(
    centroid: np.ndarray,
    normal: np.ndarray,
    area: float,
    rule_cfg: dict,
) -> bool:
    return (
        check_normal_cone(normal, rule_cfg)
        and check_dominant_axis(normal, rule_cfg)
        and check_centroid_box(centroid, rule_cfg)
        and check_halfspaces(centroid, rule_cfg)
        and check_area_range(area, rule_cfg)
    )


def assign_surface(
    centroid: np.ndarray,
    normal: np.ndarray,
    area: float,
    rules: list[dict],
    default_surface: str,
) -> tuple[str, str]:
    for i, rule in enumerate(rules):
        if matches_rule(centroid, normal, area, rule):
            return str(rule["surface_name"]), f"rule_{i}"
    return default_surface, "default"


def save_face_surface_csv(rows: list[dict], filepath: str | Path) -> None:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["face_index", "surface_name"])
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "face_index": row["face_index"],
                "surface_name": row["surface_name"],
            })


def save_debug_csv(rows: list[dict], filepath: str | Path) -> None:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "face_index",
        "surface_name",
        "matched_by",
        "centroid_x",
        "centroid_y",
        "centroid_z",
        "normal_x",
        "normal_y",
        "normal_z",
        "area",
    ]

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    config_path = Path(r"G:\我的雲端硬碟\TPMC\surface_map_config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stl_path = Path(cfg["stl_path"])
    output_csv = Path(cfg.get("output_csv", stl_path.with_name("face_surface_map.csv")))
    debug_csv = Path(cfg.get("debug_csv", stl_path.with_name("face_surface_debug.csv")))

    scale_factor = float(cfg.get("scale_factor", 1.0))
    recenter_to_origin = bool(cfg.get("recenter_to_origin", True))
    default_surface = str(cfg.get("default_surface", "default"))
    rules = list(cfg.get("rules", []))

    mesh = load_stl_mesh(stl_path)

    vertices = np.asarray(mesh.vertices, dtype=float).copy()
    faces = np.asarray(mesh.faces, dtype=int).copy()

    vertices *= scale_factor

    if recenter_to_origin:
        bbox_min = vertices.min(axis=0)
        bbox_max = vertices.max(axis=0)
        center = 0.5 * (bbox_min + bbox_max)
        vertices -= center

    centroids = compute_face_centroids(vertices, faces)
    normals = compute_face_normals(vertices, faces)
    areas = compute_face_areas(vertices, faces)

    rows: list[dict] = []
    summary_count: dict[str, int] = {}
    summary_area: dict[str, float] = {}

    for face_index in range(len(faces)):
        centroid = centroids[face_index]
        normal = normals[face_index]
        area = float(areas[face_index])

        surface_name, matched_by = assign_surface(
            centroid=centroid,
            normal=normal,
            area=area,
            rules=rules,
            default_surface=default_surface,
        )

        row = {
            "face_index": int(face_index),
            "surface_name": surface_name,
            "matched_by": matched_by,
            "centroid_x": float(centroid[0]),
            "centroid_y": float(centroid[1]),
            "centroid_z": float(centroid[2]),
            "normal_x": float(normal[0]),
            "normal_y": float(normal[1]),
            "normal_z": float(normal[2]),
            "area": area,
        }
        rows.append(row)

        summary_count[surface_name] = summary_count.get(surface_name, 0) + 1
        summary_area[surface_name] = summary_area.get(surface_name, 0.0) + area

    save_face_surface_csv(rows, output_csv)
    save_debug_csv(rows, debug_csv)

    print("Surface map written to:", output_csv)
    print("Debug map written to  :", debug_csv)
    print()

    print("=== Surface summary (count) ===")
    for key in sorted(summary_count.keys()):
        print(f"{key:20s} : {summary_count[key]}")

    print()
    print("=== Surface summary (area) ===")
    for key in sorted(summary_area.keys()):
        print(f"{key:20s} : {summary_area[key]:.6e}")


if __name__ == "__main__":
    main()