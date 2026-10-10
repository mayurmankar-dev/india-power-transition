"""Scenario definitions. Benchmarks come from NITI Aayog (2026); see assumptions.py."""

from __future__ import annotations

from . import assumptions as A
from .model import Scenario, calibrate_ramp


def demand_growth(niti_2050: float) -> float:
    """Annual growth implied by NITI's 2025 -> 2050 generation path, applied to our base year.

    Using NITI's growth rate rather than its levels keeps the scope consistent:
    NITI includes captive plants, whereas the Ember base data are utility-scale.
    """
    return (niti_2050 / A.NITI_GEN_2025_TWH) ** (1 / 25) - 1


def build(base: dict) -> list[Scenario]:
    g_cps = demand_growth(A.NITI_GEN_2050_CPS_TWH)
    g_nzs = demand_growth(A.NITI_GEN_2050_NZS_TWH)
    nuc = {k: A.NUCLEAR_CAP_SHARE_2050[k] * A.TOTAL_CAP_2050_GW[k] for k in ("cps", "nzs")}
    bess = {k: A.BESS_GW_2050[k] / A.VRE_GW_2050[k] for k in ("cps", "nzs")}
    solar_share = {k: A.SOLAR_CAP_SHARE_2050[k] / (A.SOLAR_CAP_SHARE_2050[k] + A.WIND_CAP_SHARE_2050[k])
                   for k in ("cps", "nzs")}
    avg = base["avg_additions_gw"]

    slower = Scenario(
        name="slower", label="Slower transition", demand_growth=g_cps,
        nuclear_gw_2050=nuc["cps"], bess_ratio_2050=bess["cps"], vre_mode="constant",
        solar_add=avg["solar"], wind_add=avg["wind"],
        description="Solar and wind additions stay at their 2022-24 average pace.",
    )
    cps = calibrate_ramp(Scenario(
        name="current_policy", label="Current policy", demand_growth=g_cps,
        nuclear_gw_2050=nuc["cps"], bess_ratio_2050=bess["cps"], vre_mode="ramp",
        solar_share_of_adds=solar_share["cps"],
        description="Solar and wind build-out calibrated to NITI's Current Policy Scenario 2050 coal share.",
    ), base, A.COAL_SHARE_2050["cps"])
    acc = calibrate_ramp(Scenario(
        name="accelerated", label="Accelerated renewables", demand_growth=g_cps,
        nuclear_gw_2050=nuc["nzs"], bess_ratio_2050=bess["nzs"], vre_mode="ramp",
        solar_share_of_adds=solar_share["nzs"],
        description="Build-out calibrated to NITI's Net Zero Scenario 2050 coal share, at current-policy demand.",
    ), base, A.COAL_SHARE_2050["nzs"])
    nz_demand = calibrate_ramp(Scenario(
        name="nz_demand", label="Sensitivity: net-zero electrification demand", demand_growth=g_nzs,
        nuclear_gw_2050=nuc["nzs"], bess_ratio_2050=bess["nzs"], vre_mode="ramp",
        solar_share_of_adds=solar_share["nzs"],
        description="Same 2050 coal share as Accelerated, but with NITI's higher Net Zero demand.",
    ), base, A.COAL_SHARE_2050["nzs"])
    return [slower, cps, acc, nz_demand]
