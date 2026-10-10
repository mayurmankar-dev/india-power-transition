"""Every external assumption used by the model, with its source.

NITI = NITI Aayog (2026), "Scenarios Towards Viksit Bharat and Net Zero -
Sectoral Insights: Power (Vol. 7)". Page numbers are the printed page numbers.
CPS = Current Policy Scenario, NZS = Net Zero Scenario.
Ember = Ember (2026), India Electricity Data, yearly release (CC-BY-4.0).
"""

from __future__ import annotations

import pandas as pd

NITI = "NITI Aayog (2026), Scenarios Towards Viksit Bharat and Net Zero: Power"

# --- Demand -----------------------------------------------------------------
NITI_GEN_2025_TWH = 2000            # "~2,000 TWh in 2025" (NITI p.48)
NITI_GEN_2050_CPS_TWH = (7350 + 7700) / 2    # 7,350-7,700 TWh (NITI p.48), midpoint
NITI_GEN_2050_NZS_TWH = (9700 + 10200) / 2   # 9,700-10,200 TWh (NITI p.48), midpoint

# --- 2050 benchmarks (NITI Tables 4.1, 4.2, E.1) -----------------------------
COAL_SHARE_2050 = {"cps": (0.33 + 0.34) / 2, "nzs": (0.21 + 0.23) / 2}   # Table 4.2, p.49
TOTAL_CAP_2050_GW = {"cps": (2500 + 2800) / 2, "nzs": (3800 + 3830) / 2}  # Table E.1, p.xxii
NUCLEAR_CAP_SHARE_2050 = {"cps": 0.02, "nzs": 0.03}                       # Table 4.1, p.47
SOLAR_CAP_SHARE_2050 = {"cps": 0.58, "nzs": 0.64}                         # Table 4.1 midpoints
WIND_CAP_SHARE_2050 = {"cps": 0.165, "nzs": 0.195}                        # Table 4.1 midpoints
BESS_GW_2050 = {"cps": (420 + 520) / 2, "nzs": (900 + 1150) / 2}          # Table E.1
VRE_GW_2050 = {"cps": (1890 + 2200) / 2, "nzs": (3150 + 3200) / 2}        # Table E.1
SOLAR_GEN_SHARE_2050 = {"cps": 0.42, "nzs": (0.50 + 0.51) / 2}           # Table 4.2, p.49
WIND_GEN_SHARE_2050 = {"cps": 0.14, "nzs": (0.15 + 0.18) / 2}            # Table 4.2, p.49
GRID_EF_2050 = {"cps": 0.328, "nzs": 0.257}                               # kgCO2/kWh, Fig 4.9, p.56
INVESTMENT_2025_2050_TUSD = {                                             # Table 4.3, p.55
    "cps": {"generation": 1.77, "storage": 0.60, "t&d": 1.21, "total": 3.58},
    "nzs": {"generation": 2.40, "storage": 1.32, "t&d": 1.43, "total": 5.15},
}
NEW_COAL_BY_2045_CPS_GW = 240       # "almost 240 GW of new coal addition ... by 2045" (NITI p.56)
COAL_PLF_INTERMEDIATE = 0.65        # coal PLF "around 62-65%" in the intermediate period (NITI p.48)

# --- Supply-side assumptions --------------------------------------------------
HYDRO_GW_2070 = (140 + 155) / 2     # hydro incl. small hydro reaches 140-155 GW by 2070 (NITI p.45)
BIO_GW_2070 = (30 + 34) / 2         # biomass 30-34 GW by 2070 (NITI p.45)
MAX_ANNUAL_ADDITIONS_GW = {         # Table 3.6, p.36 (maximum annual additions)
    "solar": {2030: 50, 2040: 90, 2050: 120},
    "wind": {2030: 15, 2040: 30, 2050: 45},
}

# --- Costs: INR crore per MW, 2025 prices (CEA, reproduced in NITI Table 3.7, p.37)
CAPEX_INR_CR_PER_MW = {
    "coal":    {2030: 11.5, 2040: 11.5, 2050: 11.5},
    "gas":     {2030: 6.0,  2040: 6.0,  2050: 6.0},
    "bio":     {2030: 6.0,  2040: 5.9,  2050: 5.8},
    "wind":    {2030: 7.6,  2040: 7.0,  2050: 6.6},
    "solar":   {2030: 4.2,  2040: 4.0,  2050: 3.75},
    "hydro":   {2030: 11.3, 2040: 11.1, 2050: 11.1},   # run-of-river
    "nuclear": {2030: 14.0, 2040: 14.0, 2050: 14.0},
    "bess":    {2030: 7.2,  2040: 6.6,  2050: 5.6},
}
BESS_LIFE_YEARS = 12                # NITI assumes a 10-15 year life (p.36); midpoint, rounded
INR_PER_USD = 80                    # NITI p.54, footnote 12
# Transmission & distribution cost as a ratio of generation capex (NITI p.54):
# Generation : Transmission : Distribution = 4 : 2 : 1 for conventional plants and
# 4 : 3 : 1 for solar and wind.
TD_RATIO = {"conventional": 3 / 4, "vre": 4 / 4}

# --- Historical grid emission factor (CEA CO2 Baseline Database, via NITI Annexure E, p.88)
CEA_GRID_EF = {  # FY, tCO2/MWh, weighted average incl. RE
    "2019-20": 0.713, "2020-21": 0.703, "2021-22": 0.715, "2022-23": 0.716,
    "2023-24": 0.727, "2024-25": 0.710,
}


def niti_implied_cf() -> dict[str, float]:
    """Fleet-average 2050 capacity factors implied by NITI's 2050 generation and capacity
    (generation share x total generation / (capacity share x total capacity x 8760 h)),
    averaged over the CPS and NZS. NITI's figures include captive plants in both
    numerator and denominator, so the ratio is not affected by scope."""
    out = {}
    for tech, gshare, cshare in (("solar", SOLAR_GEN_SHARE_2050, SOLAR_CAP_SHARE_2050),
                                 ("wind", WIND_GEN_SHARE_2050, WIND_CAP_SHARE_2050)):
        vals = []
        for k, gen in (("cps", NITI_GEN_2050_CPS_TWH), ("nzs", NITI_GEN_2050_NZS_TWH)):
            vals.append(gshare[k] * gen / (cshare[k] * TOTAL_CAP_2050_GW[k] * 8.76))
        out[tech] = sum(vals) / len(vals)
    return out


def table() -> pd.DataFrame:
    """Flat table of the assumptions for documentation (data/assumptions.csv)."""
    rows = [
        ("Generation 2025", NITI_GEN_2025_TWH, "TWh", f"{NITI}, p.48"),
        ("Generation 2050, CPS (midpoint)", NITI_GEN_2050_CPS_TWH, "TWh", f"{NITI}, p.48"),
        ("Generation 2050, NZS (midpoint)", NITI_GEN_2050_NZS_TWH, "TWh", f"{NITI}, p.48"),
        ("Coal generation share 2050, CPS (midpoint)", COAL_SHARE_2050["cps"], "share", f"{NITI}, Table 4.2, p.49"),
        ("Coal generation share 2050, NZS (midpoint)", COAL_SHARE_2050["nzs"], "share", f"{NITI}, Table 4.2, p.49"),
        ("Nuclear capacity share 2050, CPS", NUCLEAR_CAP_SHARE_2050["cps"], "share", f"{NITI}, Table 4.1, p.47"),
        ("Nuclear capacity share 2050, NZS", NUCLEAR_CAP_SHARE_2050["nzs"], "share", f"{NITI}, Table 4.1, p.47"),
        ("Total capacity 2050, CPS (midpoint)", TOTAL_CAP_2050_GW["cps"], "GW", f"{NITI}, Table E.1, p.xxii"),
        ("Total capacity 2050, NZS (midpoint)", TOTAL_CAP_2050_GW["nzs"], "GW", f"{NITI}, Table E.1, p.xxii"),
        ("BESS / VRE capacity ratio 2050, CPS", BESS_GW_2050["cps"] / VRE_GW_2050["cps"], "ratio", f"{NITI}, Table E.1, p.xxii"),
        ("BESS / VRE capacity ratio 2050, NZS", BESS_GW_2050["nzs"] / VRE_GW_2050["nzs"], "ratio", f"{NITI}, Table E.1, p.xxii"),
        ("Solar fleet capacity factor 2050 implied by NITI", niti_implied_cf()["solar"], "share", f"Derived from {NITI}, Tables 4.1, 4.2, E.1"),
        ("Wind fleet capacity factor 2050 implied by NITI", niti_implied_cf()["wind"], "share", f"Derived from {NITI}, Tables 4.1, 4.2, E.1"),
        ("Max solar additions 2030-39 / 2040-49", "50 / 90", "GW/yr", f"{NITI}, Table 3.6, p.36"),
        ("Max onshore wind additions 2030-39 / 2040-49", "15 / 30", "GW/yr", f"{NITI}, Table 3.6, p.36"),
        ("Hydro capacity 2070 (midpoint)", HYDRO_GW_2070, "GW", f"{NITI}, p.45"),
        ("Biomass capacity 2070 (midpoint)", BIO_GW_2070, "GW", f"{NITI}, p.45"),
        ("Coal plant load factor ceiling (from 2030)", COAL_PLF_INTERMEDIATE, "share", f"{NITI}, p.48"),
        ("BESS life", BESS_LIFE_YEARS, "years", f"{NITI}, p.36"),
        ("Exchange rate", INR_PER_USD, "INR/USD", f"{NITI}, p.54"),
        ("T&D capex / generation capex, conventional", TD_RATIO["conventional"], "ratio", f"{NITI}, p.54"),
        ("T&D capex / generation capex, solar & wind", TD_RATIO["vre"], "ratio", f"{NITI}, p.54"),
    ]
    for tech, path in CAPEX_INR_CR_PER_MW.items():
        for yr, v in path.items():
            rows.append((f"Capex {tech} {yr}", v, "INR crore/MW (2025 prices)", f"CEA via {NITI}, Table 3.7, p.37"))
    return pd.DataFrame(rows, columns=["parameter", "value", "unit", "source"])
