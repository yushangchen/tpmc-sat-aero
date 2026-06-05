from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import csv

from physics.gsi import GSIConfig


@dataclass
class SurfaceDefinition:
    name: str
    gsi: GSIConfig


@dataclass
class SurfaceModel:
    surfaces: dict[str, SurfaceDefinition]
    face_to_surface: dict[int, str] = field(default_factory=dict)
    default_surface: str = "default"

    def validate(self) -> None:
        if self.default_surface not in self.surfaces:
            raise ValueError(
                f"default_surface '{self.default_surface}' is not defined in surfaces."
            )

        for name, surf in self.surfaces.items():
            if surf.name != name:
                raise ValueError(
                    f"SurfaceDefinition name mismatch: key='{name}', surf.name='{surf.name}'"
                )
            surf.gsi.validate()

        for face_idx, surface_name in self.face_to_surface.items():
            if face_idx < 0:
                raise ValueError(f"Invalid face index: {face_idx}")
            if surface_name not in self.surfaces:
                raise ValueError(
                    f"Face {face_idx} maps to undefined surface '{surface_name}'."
                )

    def get_surface_name(self, face_index: int) -> str:
        return self.face_to_surface.get(face_index, self.default_surface)

    def get_surface(self, face_index: int) -> SurfaceDefinition:
        name = self.get_surface_name(face_index)
        return self.surfaces[name]

    def get_gsi(self, face_index: int) -> GSIConfig:
        return self.get_surface(face_index).gsi


def load_face_surface_csv(filepath: str | Path) -> dict[int, str]:
    """
    CSV format:
        face_index,surface_name
        0,x_minus
        1,x_minus
        2,y_plus
    """
    filepath = Path(filepath)
    mapping: dict[int, str] = {}

    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"face_index", "surface_name"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"{filepath} must contain columns: {sorted(required)}"
            )

        for row in reader:
            face_index = int(row["face_index"])
            surface_name = str(row["surface_name"]).strip()
            mapping[face_index] = surface_name

    return mapping