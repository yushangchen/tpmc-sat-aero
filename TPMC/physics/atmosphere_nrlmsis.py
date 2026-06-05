from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
    year: int
    month: int
    day: int
    doy: int
    hour: float
    alt_km: float
    lat_deg: float
    lon_deg: float

    temperature_K: float
    exospheric_temperature_K: float
    rho_total_kg_m3: float

    species_number_density_m3: dict[str, float]

    f107: float
    f107a: float
    apdaily: float


@dataclass
class SpeciesSample:
    name: str
    molecular_mass_kg: float
    number_density_m3: float
    mean_flux_speed_m_s: float
    flux_probability: float


def _is_number_token(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False


def _cm3_to_m3(x: float) -> float:
    return x * 1.0e6


def _gcm3_to_kgm3(x: float) -> float:
    return x * 1000.0


def load_nrlmsis_ascii(filepath: str | Path) -> list[AtmosphereState]:
    """
    Load official NRLMSIS text output like:

    Year Mon Day DOY hour Heit(km) Lat Lon Oden(cm-3) N2den(cm-3) O2den(cm-3)
    air(gm/cm3) T(K) exoT(K) Heden(cm-3) Arden(cm-3) Hden(cm-3) Nden(cm-3)
    F107 F107a apdaily ap0-3 ap3-6 ap6-9 ap9-12 ap12-33 ap33-59
    """
    filepath = Path(filepath)
    rows: list[AtmosphereState] = []

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()

            # Skip headers / notes
            if len(parts) < 18:
                continue
            if not _is_number_token(parts[0]):
                continue

            # Expected data row length: 27 columns
            # We only need the first 21
            if len(parts) < 21:
                continue

            year = int(float(parts[0]))
            month = int(float(parts[1]))
            day = int(float(parts[2]))
            doy = int(float(parts[3]))
            hour = float(parts[4])

            alt_km = float(parts[5])
            lat_deg = float(parts[6])
            lon_deg = float(parts[7])

            Oden_cm3 = float(parts[8])
            N2den_cm3 = float(parts[9])
            O2den_cm3 = float(parts[10])
            air_g_cm3 = float(parts[11])
            T_K = float(parts[12])
            exoT_K = float(parts[13])
            Heden_cm3 = float(parts[14])
            Arden_cm3 = float(parts[15])
            Hden_cm3 = float(parts[16])
            Nden_cm3 = float(parts[17])

            f107 = float(parts[18])
            f107a = float(parts[19])
            apdaily = float(parts[20])

            species = {
                "O": _cm3_to_m3(Oden_cm3),
                "N2": _cm3_to_m3(N2den_cm3),
                "O2": _cm3_to_m3(O2den_cm3),
                "He": _cm3_to_m3(Heden_cm3),
                "Ar": _cm3_to_m3(Arden_cm3),
                "H": _cm3_to_m3(Hden_cm3),
                "N": _cm3_to_m3(Nden_cm3),
            }

            rows.append(
                AtmosphereState(
                    year=year,
                    month=month,
                    day=day,
                    doy=doy,
                    hour=hour,
                    alt_km=alt_km,
                    lat_deg=lat_deg,
                    lon_deg=lon_deg,
                    temperature_K=T_K,
                    exospheric_temperature_K=exoT_K,
                    rho_total_kg_m3=_gcm3_to_kgm3(air_g_cm3),
                    species_number_density_m3=species,
                    f107=f107,
                    f107a=f107a,
                    apdaily=apdaily,
                )
            )

    if not rows:
        raise ValueError(f"No valid NRLMSIS rows found in file: {filepath}")

    return rows


def get_nearest_state(rows: list[AtmosphereState], target_alt_km: float) -> AtmosphereState:
    idx = int(np.argmin([abs(r.alt_km - target_alt_km) for r in rows]))
    return rows[idx]


def get_nearest_state_from_file(filepath: str | Path, target_alt_km: float) -> AtmosphereState:
    rows = load_nrlmsis_ascii(filepath)
    return get_nearest_state(rows, target_alt_km)


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