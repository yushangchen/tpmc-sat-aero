from __future__ import annotations

from dataclasses import dataclass, asdict, field
import hashlib
import json
from typing import Any


def _normalize_for_json(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return [_normalize_for_json(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize_for_json(v) for k, v in value.items()}
    return value


@dataclass(frozen=True)
class TPMCCase:
    name: str

    stl_path: str
    atmosphere_config: dict[str, Any]

    target_alt_km: float
    target_lat_deg: float = 0.0
    target_lon_deg: float = 0.0
    epoch: str | None = None

    scale_factor: float = 0.001

    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0

    solver_mode: str = "tpmc"   # "tpmc" or "fmf"

    face_map_csv: str | None = None

    A_ref: float = 1.0e-4
    L_ref: float = 1.0e-2

    ref_point_body: tuple[float, float, float] = (0.0, 0.0, 0.0)
    drag_axis_body: tuple[float, float, float] = (1.0, 0.0, 0.0)
    side_axis_body: tuple[float, float, float] = (0.0, 1.0, 0.0)
    lift_axis_body: tuple[float, float, float] = (0.0, 0.0, 1.0)

    bulk_velocity_world: tuple[float, float, float] = (7500.0, 0.0, 0.0)

    n_particles: int = 50000
    seed: int = 42

    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, Any]:
        return _normalize_for_json(asdict(self))

    def clone(self, **updates: Any) -> "TPMCCase":
        payload = self.to_payload()
        payload.update(updates)
        return TPMCCase(**payload)

    @property
    def case_id(self) -> str:
        payload = self.to_payload()
        payload.pop("name", None)
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]