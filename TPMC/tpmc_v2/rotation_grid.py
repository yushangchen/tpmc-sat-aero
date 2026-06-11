from __future__ import annotations

from itertools import product
from typing import Iterable

from tpmc_v2.case_schema import TPMCCase


def expand_rotation_cases(
    base_case: TPMCCase,
    yaw_list: Iterable[float],
    pitch_list: Iterable[float] = (0.0,),
    roll_list: Iterable[float] = (0.0,),
) -> list[TPMCCase]:
    cases: list[TPMCCase] = []

    for yaw, pitch, roll in product(yaw_list, pitch_list, roll_list):
        name = (
            f"{base_case.name}"
            f"_y{float(yaw):g}"
            f"_p{float(pitch):g}"
            f"_r{float(roll):g}"
        )
        cases.append(
            base_case.clone(
                name=name,
                yaw_deg=float(yaw),
                pitch_deg=float(pitch),
                roll_deg=float(roll),
            )
        )

    return cases


def expand_altitude_cases(
    base_case: TPMCCase,
    altitude_list_km: Iterable[float],
) -> list[TPMCCase]:
    cases: list[TPMCCase] = []

    for alt in altitude_list_km:
        name = f"{base_case.name}_alt{float(alt):g}km"
        cases.append(
            base_case.clone(
                name=name,
                target_alt_km=float(alt),
            )
        )

    return cases