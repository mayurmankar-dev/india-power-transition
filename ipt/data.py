"""Load and summarise Ember's India yearly electricity data (national totals)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "ember_india_yearly.csv"

# Map Ember fuel names to model technologies
FUEL_MAP = {
    "Coal": "coal", "Gas": "gas", "Other Fossil": "other_fossil",
    "Solar": "solar", "Wind": "wind", "Hydro": "hydro", "Nuclear": "nuclear",
    "Bioenergy": "bio", "Other Renewables": "other_re",
}


def load_national(path: Path = RAW) -> dict[str, pd.DataFrame]:
    """Return national capacity (GW), generation (TWh) and emissions (MtCO2) by fuel and year."""
    df = pd.read_csv(path)
    nat = df[(df["State type"] == "total") & (df["Subcategory"] == "Fuel")]

    def pivot(category: str, unit: str, scale: float) -> pd.DataFrame:
        sub = nat[(nat["Category"] == category) & (nat["Unit"] == unit)]
        p = sub.pivot_table(index="Year", columns="Variable", values="Value") / scale
        return p.rename(columns=FUEL_MAP).fillna(0.0)

    return {
        "capacity_gw": pivot("Capacity", "MW", 1e3),
        "generation_twh": pivot("Electricity generation", "GWh", 1e3),
        "emissions_mt": pivot("Power sector emissions", "ktCO2", 1e3),
    }


def base_year_parameters(data: dict[str, pd.DataFrame], cf_years=(2022, 2024)) -> dict:
    """Capacity factors (mid-year capacity basis, averaged over cf_years) and emission factors."""
    cap, gen, em = data["capacity_gw"], data["generation_twh"], data["emissions_mt"]
    mid = (cap + cap.shift(1)) / 2                 # generation in a year comes from mid-year capacity
    cf = gen / (mid * 8.76)                        # TWh / (GW * 8.76) = capacity factor
    lo, hi = cf_years
    cf_avg = cf.loc[lo:hi].mean()
    ef = (em / gen.replace(0, float("nan"))).loc[hi]   # tCO2/MWh = MtCO2/TWh; Ember lifecycle factors
    base = int(cap.index.max())
    return {
        "base_year": base,
        "capacity_gw": cap.loc[base].to_dict(),
        "generation_twh": gen.loc[base].to_dict(),
        "capacity_factor": {k: float(cf_avg[k]) for k in ["solar", "wind", "hydro", "nuclear", "bio"]},
        "emission_factor": {k: float(v) for k, v in ef.fillna(0).items()},
        "additions_gw": cap.diff().loc[base].to_dict(),
        "avg_additions_gw": cap.diff().loc[lo:hi].mean().to_dict(),
        "total_generation_twh": float(gen.loc[base].sum()),
        "total_emissions_mt": float(em.loc[base].sum()),
    }
