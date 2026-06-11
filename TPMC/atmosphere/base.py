from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np

from physics.inflow import positive_normal_flux_speed


AMU = 1.66053906660e-27  # kg

SPECIES_MASS_KG = {
    "O": 16.0 * AMU,
    "N2": 28.0 * AMU,
    "O2": 32.0 * AMU,
    "He": 4.0 * AMU,
    "Ar": 40.0 * AMU,
    "H": 1.0 * AMU,
    "N": 14.0 * AMU,
    "NO": 30.0 * AMU,
}


@dataclass
class AtmosphereState:
    altitude_km: float
    lat_deg: float
    lon_deg: float

    temperature_K: float
    exospheric_temperature_K: float
    rho_total_kg_m3: float

    species_number_density_m3: dict[str, float]

    source: str = "unknown"
    metadata: dict | None = None


@dataclass
class SpeciesSample:
    name: str
    molecular_mass_kg: float
    number_density_m3: float
    mean_flux_speed_m_s: float
    flux_probability: float


class AtmosphereProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    def get_state(
        self,
        target_alt_km: float,
        lat_deg: float | None = None,
        lon_deg: float | None = None,
        epoch: str | None = None,
    ) -> AtmosphereState:
        raise NotImplementedError


def compute_species_flux_table(
    atm: AtmosphereState,
    bulk_velocity: np.ndarray,
    plane_normal: np.ndarray,
) -> list[SpeciesSample]:
    bulk_velocity = np.asarray(bulk_velocity, dtype=float)
    plane_normal = np.asarray(plane_normal, dtype=float)
    plane_normal = plane_normal / np.linalg.norm(plane_normal)

    samples: list[SpeciesSample] = []
    fluxes = []

    for name, n_i in atm.species_number_density_m3.items():
        if n_i <= 0.0:
            continue
        if name not in SPECIES_MASS_KG:
            continue

        m_i = SPECIES_MASS_KG[name]
        cbar_i = positive_normal_flux_speed(
            bulk_velocity=bulk_velocity,
            plane_normal=plane_normal,
            temperature=atm.temperature_K,
            molecular_mass=m_i,
        )
        flux_i = n_i * cbar_i
        fluxes.append(flux_i)

        samples.append(
            SpeciesSample(
                name=name,
                molecular_mass_kg=m_i,
                number_density_m3=n_i,
                mean_flux_speed_m_s=cbar_i,
                flux_probability=0.0,
            )
        )

    total_flux = float(np.sum(fluxes))
    if total_flux <= 0.0:
        raise ValueError("Total species incident flux is non-positive.")

    for i, flux_i in enumerate(fluxes):
        samples[i].flux_probability = flux_i / total_flux

    return samples


def compute_total_incident_flux(
    atm: AtmosphereState,
    bulk_velocity: np.ndarray,
    plane_normal: np.ndarray,
) -> float:
    table = compute_species_flux_table(atm, bulk_velocity, plane_normal)
    total_flux = 0.0
    for s in table:
        total_flux += s.number_density_m3 * s.mean_flux_speed_m_s
    return total_flux


def sample_species_from_state(
    atm: AtmosphereState,
    bulk_velocity: np.ndarray,
    plane_normal: np.ndarray,
    rng: np.random.Generator,
) -> SpeciesSample:
    table = compute_species_flux_table(atm, bulk_velocity, plane_normal)

    probs = np.array([s.flux_probability for s in table], dtype=float)
    probs = probs / probs.sum()

    idx = int(rng.choice(len(table), p=probs))
    return table[idx]