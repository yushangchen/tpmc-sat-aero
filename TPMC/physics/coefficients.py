from __future__ import annotations


def compute_density(number_density: float, molecular_mass: float) -> float:
    return number_density * molecular_mass


def compute_dynamic_pressure(density: float, speed: float) -> float:
    return 0.5 * density * speed**2


def compute_drag_coefficient(
    drag_force: float,
    dynamic_pressure: float,
    reference_area: float
) -> float:
    return drag_force / (dynamic_pressure * reference_area)