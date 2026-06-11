from __future__ import annotations

from pathlib import Path
import csv
import numpy as np

from atmosphere.base import AtmosphereProvider, AtmosphereState


def _cm3_to_m3(x: float) -> float:
    return x * 1.0e6


def _gcm3_to_kgm3(x: float) -> float:
    return x * 1000.0


def _is_number_token(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False


class ManualAtmosphereProvider(AtmosphereProvider):
    provider_name = "manual"

    def __init__(
        self,
        rho_total_kg_m3: float,
        temperature_K: float,
        exospheric_temperature_K: float | None = None,
        lat_deg: float = 0.0,
        lon_deg: float = 0.0,
        species_number_density_m3: dict[str, float] | None = None,
    ):
        self.rho_total_kg_m3 = float(rho_total_kg_m3)
        self.temperature_K = float(temperature_K)
        self.exospheric_temperature_K = (
            float(exospheric_temperature_K)
            if exospheric_temperature_K is not None
            else float(temperature_K)
        )
        self.lat_deg = float(lat_deg)
        self.lon_deg = float(lon_deg)
        self.species_number_density_m3 = dict(species_number_density_m3 or {})

    def get_state(
        self,
        target_alt_km: float,
        lat_deg: float | None = None,
        lon_deg: float | None = None,
        epoch: str | None = None,
    ) -> AtmosphereState:
        return AtmosphereState(
            altitude_km=float(target_alt_km),
            lat_deg=self.lat_deg if lat_deg is None else float(lat_deg),
            lon_deg=self.lon_deg if lon_deg is None else float(lon_deg),
            temperature_K=self.temperature_K,
            exospheric_temperature_K=self.exospheric_temperature_K,
            rho_total_kg_m3=self.rho_total_kg_m3,
            species_number_density_m3=self.species_number_density_m3,
            source=self.provider_name,
            metadata={"epoch": epoch},
        )


class NRLMSISTxtProvider(AtmosphereProvider):
    provider_name = "nrlmsis_txt"

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.rows = self._load_rows(self.filepath)

    def _load_rows(self, filepath: Path) -> list[dict]:
        rows: list[dict] = []

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()

                if len(parts) < 21:
                    continue
                if not _is_number_token(parts[0]):
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
                    {
                        "year": year,
                        "month": month,
                        "day": day,
                        "doy": doy,
                        "hour": hour,
                        "alt_km": alt_km,
                        "lat_deg": lat_deg,
                        "lon_deg": lon_deg,
                        "temperature_K": T_K,
                        "exospheric_temperature_K": exoT_K,
                        "rho_total_kg_m3": _gcm3_to_kgm3(air_g_cm3),
                        "species_number_density_m3": species,
                        "f107": f107,
                        "f107a": f107a,
                        "apdaily": apdaily,
                    }
                )

        if not rows:
            raise ValueError(f"No valid NRLMSIS rows found in file: {filepath}")

        return rows

    def _select_nearest_row(
        self,
        target_alt_km: float,
        lat_deg: float | None = None,
        lon_deg: float | None = None,
    ) -> dict:
        best_row = None
        best_score = None

        for row in self.rows:
            score = abs(row["alt_km"] - float(target_alt_km))

            if lat_deg is not None:
                score += 1.0e-3 * abs(row["lat_deg"] - float(lat_deg))
            if lon_deg is not None:
                score += 1.0e-3 * abs(row["lon_deg"] - float(lon_deg))

            if best_score is None or score < best_score:
                best_score = score
                best_row = row

        return best_row

    def get_state(
        self,
        target_alt_km: float,
        lat_deg: float | None = None,
        lon_deg: float | None = None,
        epoch: str | None = None,
    ) -> AtmosphereState:
        row = self._select_nearest_row(
            target_alt_km=target_alt_km,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
        )

        return AtmosphereState(
            altitude_km=row["alt_km"],
            lat_deg=row["lat_deg"],
            lon_deg=row["lon_deg"],
            temperature_K=row["temperature_K"],
            exospheric_temperature_K=row["exospheric_temperature_K"],
            rho_total_kg_m3=row["rho_total_kg_m3"],
            species_number_density_m3=row["species_number_density_m3"],
            source=self.provider_name,
            metadata={
                "epoch": epoch,
                "year": row["year"],
                "month": row["month"],
                "day": row["day"],
                "doy": row["doy"],
                "hour": row["hour"],
                "f107": row["f107"],
                "f107a": row["f107a"],
                "apdaily": row["apdaily"],
                "filepath": str(self.filepath),
            },
        )


class TableCsvProvider(AtmosphereProvider):
    provider_name = "table_csv"

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.rows = self._load_rows(self.filepath)

    def _load_rows(self, filepath: Path) -> list[dict]:
        rows: list[dict] = []

        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            required = {"alt_km", "rho_total_kg_m3", "temperature_K"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError(
                    f"{filepath} must contain columns: {sorted(required)}"
                )

            for raw in reader:
                row = {
                    "alt_km": float(raw["alt_km"]),
                    "rho_total_kg_m3": float(raw["rho_total_kg_m3"]),
                    "temperature_K": float(raw["temperature_K"]),
                    "exospheric_temperature_K": float(
                        raw.get("exospheric_temperature_K", raw["temperature_K"])
                    ),
                    "lat_deg": float(raw.get("lat_deg", 0.0)),
                    "lon_deg": float(raw.get("lon_deg", 0.0)),
                    "species_number_density_m3": {
                        "O": float(raw.get("n_O", 0.0)),
                        "N2": float(raw.get("n_N2", 0.0)),
                        "O2": float(raw.get("n_O2", 0.0)),
                        "He": float(raw.get("n_He", 0.0)),
                        "Ar": float(raw.get("n_Ar", 0.0)),
                        "H": float(raw.get("n_H", 0.0)),
                        "N": float(raw.get("n_N", 0.0)),
                        "NO": float(raw.get("n_NO", 0.0)),
                    },
                }
                rows.append(row)

        if not rows:
            raise ValueError(f"No valid rows found in table CSV: {filepath}")

        return rows

    def _select_nearest_row(self, target_alt_km: float) -> dict:
        idx = int(np.argmin([abs(r["alt_km"] - float(target_alt_km)) for r in self.rows]))
        return self.rows[idx]

    def get_state(
        self,
        target_alt_km: float,
        lat_deg: float | None = None,
        lon_deg: float | None = None,
        epoch: str | None = None,
    ) -> AtmosphereState:
        row = self._select_nearest_row(target_alt_km)

        return AtmosphereState(
            altitude_km=row["alt_km"],
            lat_deg=row["lat_deg"] if lat_deg is None else float(lat_deg),
            lon_deg=row["lon_deg"] if lon_deg is None else float(lon_deg),
            temperature_K=row["temperature_K"],
            exospheric_temperature_K=row["exospheric_temperature_K"],
            rho_total_kg_m3=row["rho_total_kg_m3"],
            species_number_density_m3=row["species_number_density_m3"],
            source=self.provider_name,
            metadata={
                "epoch": epoch,
                "filepath": str(self.filepath),
            },
        )