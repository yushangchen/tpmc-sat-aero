from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


def _as_array(v) -> np.ndarray:
    return np.asarray(v, dtype=float)


def _normalize(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < eps:
        raise ValueError("Cannot normalize near-zero vector.")
    return v / n


@dataclass
class ReferenceConfig:
    # fixed reference quantities
    A_ref: float
    L_ref: float

    # moment reference point in BODY frame
    ref_point_body: np.ndarray = field(default_factory=lambda: np.zeros(3))

    # aerodynamic axes in BODY frame
    drag_axis_body: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0, 0.0]))
    side_axis_body: np.ndarray = field(default_factory=lambda: np.array([0.0, 1.0, 0.0]))
    lift_axis_body: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 1.0]))

    def validate(self) -> None:
        if self.A_ref <= 0.0:
            raise ValueError("A_ref must be positive.")
        if self.L_ref <= 0.0:
            raise ValueError("L_ref must be positive.")

        self.ref_point_body = _as_array(self.ref_point_body)
        self.drag_axis_body = _normalize(_as_array(self.drag_axis_body))
        self.side_axis_body = _normalize(_as_array(self.side_axis_body))
        self.lift_axis_body = _normalize(_as_array(self.lift_axis_body))

        if self.ref_point_body.shape != (3,):
            raise ValueError("ref_point_body must be a 3-component vector.")


def rotation_matrix_x(angle_deg: float) -> np.ndarray:
    a = np.deg2rad(angle_deg)
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [1.0, 0.0, 0.0],
        [0.0, c,   -s ],
        [0.0, s,    c ],
    ])


def rotation_matrix_y(angle_deg: float) -> np.ndarray:
    a = np.deg2rad(angle_deg)
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [ c, 0.0, s],
        [0.0, 1.0, 0.0],
        [-s, 0.0, c],
    ])


def rotation_matrix_z(angle_deg: float) -> np.ndarray:
    a = np.deg2rad(angle_deg)
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [c,  -s, 0.0],
        [s,   c, 0.0],
        [0.0, 0.0, 1.0],
    ])


def build_rotation_matrix(roll_deg: float, pitch_deg: float, yaw_deg: float) -> np.ndarray:
    Rx = rotation_matrix_x(roll_deg)
    Ry = rotation_matrix_y(pitch_deg)
    Rz = rotation_matrix_z(yaw_deg)
    return Rz @ Ry @ Rx


def body_to_world(vec_body: np.ndarray, roll_deg: float, pitch_deg: float, yaw_deg: float) -> np.ndarray:
    R = build_rotation_matrix(roll_deg, pitch_deg, yaw_deg)
    return R @ _as_array(vec_body)


def project_force_axes(
    total_force_world: np.ndarray,
    roll_deg: float,
    pitch_deg: float,
    yaw_deg: float,
    ref: ReferenceConfig,
):
    drag_axis_world = body_to_world(ref.drag_axis_body, roll_deg, pitch_deg, yaw_deg)
    side_axis_world = body_to_world(ref.side_axis_body, roll_deg, pitch_deg, yaw_deg)
    lift_axis_world = body_to_world(ref.lift_axis_body, roll_deg, pitch_deg, yaw_deg)

    F_drag = float(np.dot(total_force_world, drag_axis_world))
    F_side = float(np.dot(total_force_world, side_axis_world))
    F_lift = float(np.dot(total_force_world, lift_axis_world))

    return F_drag, F_side, F_lift


def coefficient_force(force_component: float, q_inf: float, A_ref: float) -> float:
    return force_component / (q_inf * A_ref)


def coefficient_moment(moment_component: float, q_inf: float, A_ref: float, L_ref: float) -> float:
    return moment_component / (q_inf * A_ref * L_ref)