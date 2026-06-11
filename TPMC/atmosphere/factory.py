from __future__ import annotations

from atmosphere.providers import (
    ManualAtmosphereProvider,
    NRLMSISTxtProvider,
    TableCsvProvider,
)


def build_atmosphere_provider(config: dict):
    provider_type = str(config["type"]).lower()

    if provider_type == "manual":
        return ManualAtmosphereProvider(
            rho_total_kg_m3=config["rho_total_kg_m3"],
            temperature_K=config["temperature_K"],
            exospheric_temperature_K=config.get("exospheric_temperature_K", None),
            lat_deg=config.get("lat_deg", 0.0),
            lon_deg=config.get("lon_deg", 0.0),
            species_number_density_m3=config.get("species_number_density_m3", {}),
        )

    if provider_type == "nrlmsis_txt":
        return NRLMSISTxtProvider(
            filepath=config["filepath"],
        )

    if provider_type == "table_csv":
        return TableCsvProvider(
            filepath=config["filepath"],
        )

    raise ValueError(f"Unsupported atmosphere provider type: {provider_type}")