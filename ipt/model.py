"""Annual power-sector scenario model for India, base year 2024 to 2050.

Structure (each year t):
  1. Demand (generation requirement) grows at a scenario-specific rate.
  2. Clean capacity evolves from explicit build paths (solar, wind, hydro,
     nuclear, bioenergy); generation = capacity factor x mid-year capacity.
  3. Gas generation declines linearly to zero by 2050; small "other" sources
     stay at their base-year level.
  4. Coal is the residual supplier: coal generation = demand - everything else.
     Coal capacity must be large enough to deliver that at a plant load factor
     ceiling; new coal is added when it is not.
  5. Emissions = generation x fuel emission factor (Ember, lifecycle basis).
  6. Investment = capacity additions x CEA unit costs, plus battery storage
     sized relative to solar + wind capacity, plus transmission & distribution
     as a ratio of generation capex (NITI method).

This is an accounting / scenario model, not an optimisation model: it does not
choose the least-cost mix, model hourly balancing, prices or retirements.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import assumptions as A

END_YEAR = 2050
CLEAN = ["solar", "wind", "hydro", "nuclear", "bio"]
TECH_ORDER = ["coal", "gas", "nuclear", "hydro", "bio", "wind", "solar", "other"]


@dataclass(frozen=True)
class Scenario:
    name: str
    label: str
    demand_growth: float          # annual growth of generation requirement
    nuclear_gw_2050: float
    bess_ratio_2050: float        # GW of batteries per GW of solar + wind in 2050
    vre_mode: str                 # "constant" or "ramp"
    solar_add: float = 0.0        # constant mode: GW/yr
    wind_add: float = 0.0
    ramp_slope: float = 0.0       # ramp mode: increase in annual VRE additions, GW/yr per year
    solar_share_of_adds: float = 0.78
    cf_improves: bool = True      # solar/wind fleet CF rises to NITI-implied 2050 level
    apply_build_limits: bool = False  # optionally cap annual additions at NITI Table 3.6 maxima (reported as a check by default)
    description: str = ""


def interp_cost(tech: str, year: int) -> float:
    """CEA capex (INR crore/MW, 2025 prices); flat before 2030, linear between benchmark years."""
    path = A.CAPEX_INR_CR_PER_MW[tech]
    yrs = sorted(path)
    return float(np.interp(year, yrs, [path[y] for y in yrs]))


def build_limit(tech: str, year: int) -> float:
    """NITI maximum annual additions (Table 3.6); no limit given before 2030."""
    limits = A.MAX_ANNUAL_ADDITIONS_GW[tech]
    decade = max((d for d in limits if d <= year), default=None)
    return float("inf") if decade is None else float(limits[decade])


def vre_cf(tech: str, k: int, n: int, cf0: float, improves: bool) -> float:
    if not improves:
        return cf0
    return cf0 + (A.niti_implied_cf()[tech] - cf0) * k / n


def coal_plf_ceiling(year: int, base_plf: float, base_year: int) -> float:
    """Glide from the observed base-year PLF to NITI's ~65% by 2030."""
    if year >= 2030:
        return A.COAL_PLF_INTERMEDIATE
    w = (year - base_year) / (2030 - base_year)
    return base_plf + w * (A.COAL_PLF_INTERMEDIATE - base_plf)


def simulate(sc: Scenario, base: dict) -> pd.DataFrame:
    by = base["base_year"]
    cap0, gen0 = base["capacity_gw"], base["generation_twh"]
    cf, ef = base["capacity_factor"], base["emission_factor"]
    years = range(by, END_YEAR + 1)
    n_to_2070 = 2070 - by
    n_to_2050 = END_YEAR - by

    other_gen = gen0.get("other_fossil", 0) + gen0.get("other_re", 0)
    other_ef = ((gen0.get("other_fossil", 0) * ef.get("other_fossil", 0)
                 + gen0.get("other_re", 0) * ef.get("other_re", 0)) / other_gen) if other_gen else 0
    # Coal PLF is measured on end-of-year capacity throughout (base year: 1,328 TWh / 219 GW = 69%)
    base_coal_plf = gen0["coal"] / (8.76 * cap0["coal"])

    cap = {k: cap0[k] for k in ["coal", "gas", "solar", "wind", "hydro", "nuclear", "bio"]}
    bess_hist: dict[int, float] = {}
    bess_cap = 0.0
    rows = []
    for t in years:
        k = t - by
        if t == by:
            row = {"year": t, "demand": base["total_generation_twh"]}
            for tech in ["coal", "gas", "solar", "wind", "hydro", "nuclear", "bio"]:
                row[f"gen_{tech}"] = gen0[tech]
                row[f"cap_{tech}"] = cap0[tech]
                row[f"add_{tech}"] = base["additions_gw"][tech]
            row["gen_other"] = other_gen
            row["curtailed"] = 0.0
            row["coal_plf"] = base_coal_plf
            row["cap_bess"] = 0.0
            row["add_bess"] = 0.0
            row["build_limited"] = False
            row["cf_solar"], row["cf_wind"] = cf["solar"], cf["wind"]
            rows.append(row)
            continue

        prev = dict(cap)
        # --- capacity build -------------------------------------------------
        if sc.vre_mode == "constant":
            add_solar, add_wind = sc.solar_add, sc.wind_add
        else:
            base_vre_add = base["additions_gw"]["solar"] + base["additions_gw"]["wind"]
            total = base_vre_add + sc.ramp_slope * k
            add_solar, add_wind = sc.solar_share_of_adds * total, (1 - sc.solar_share_of_adds) * total
        limited = False
        if sc.apply_build_limits:
            ls, lw = build_limit("solar", t), build_limit("wind", t)
            limited = add_solar > ls or add_wind > lw
            add_solar, add_wind = min(add_solar, ls), min(add_wind, lw)
        adds = {
            "solar": add_solar,
            "wind": add_wind,
            "hydro": (A.HYDRO_GW_2070 - cap0["hydro"]) / n_to_2070,
            "bio": (A.BIO_GW_2070 - cap0["bio"]) / n_to_2070,
            "nuclear": (sc.nuclear_gw_2050 - cap0["nuclear"]) / n_to_2050,
        }
        for tech, a in adds.items():
            cap[tech] = prev[tech] + a

        # --- generation -----------------------------------------------------
        demand = base["total_generation_twh"] * (1 + sc.demand_growth) ** k
        cf_t = dict(cf)
        for tech in ("solar", "wind"):
            cf_t[tech] = vre_cf(tech, k, n_to_2050, cf[tech], sc.cf_improves)
        gen = {tech: cf_t[tech] * 8.76 * (prev[tech] + cap[tech]) / 2 for tech in CLEAN}
        gen["gas"] = gen0["gas"] * max(0.0, 1 - k / n_to_2050)
        residual = demand - sum(gen.values()) - other_gen
        curtailed = max(0.0, -residual)
        if curtailed > 0:  # more clean power than needed: curtail solar and wind pro rata
            vre = gen["solar"] + gen["wind"]
            for tech in ("solar", "wind"):
                gen[tech] -= curtailed * gen[tech] / vre
        gen["coal"] = max(0.0, residual)

        # --- coal capacity requirement (no retirements modelled) ------------
        plf = coal_plf_ceiling(t, base_coal_plf, by)
        need = gen["coal"] / (8.76 * plf)
        adds["coal"] = max(0.0, need - prev["coal"])
        cap["coal"] = prev["coal"] + adds["coal"]
        adds["gas"] = 0.0

        # --- battery storage ------------------------------------------------
        ratio = sc.bess_ratio_2050 * k / n_to_2050
        bess_target = ratio * (cap["solar"] + cap["wind"])
        new_bess = max(0.0, bess_target - bess_cap)
        replacement = bess_hist.get(t - A.BESS_LIFE_YEARS, 0.0)
        bess_cap = max(bess_cap, bess_target)
        bess_hist[t] = new_bess

        row = {"year": t, "demand": demand, "gen_other": other_gen, "curtailed": curtailed,
               "coal_plf": gen["coal"] / (8.76 * cap["coal"]),
               "cap_bess": bess_cap, "add_bess": new_bess + replacement,
               "build_limited": limited, "cf_solar": cf_t["solar"], "cf_wind": cf_t["wind"]}
        for tech in ["coal", "gas", "solar", "wind", "hydro", "nuclear", "bio"]:
            row[f"gen_{tech}"] = gen[tech]
            row[f"cap_{tech}"] = cap[tech]
            row[f"add_{tech}"] = adds.get(tech, 0.0)
        rows.append(row)

    df = pd.DataFrame(rows).set_index("year")
    return add_derived(df, base, other_ef)


def add_derived(df: pd.DataFrame, base: dict, other_ef: float) -> pd.DataFrame:
    ef = base["emission_factor"]
    techs = ["coal", "gas", "solar", "wind", "hydro", "nuclear", "bio"]
    df["gen_total"] = df[[f"gen_{t}" for t in techs]].sum(axis=1) + df["gen_other"]
    df["coal_share"] = df["gen_coal"] / df["gen_total"]
    df["vre_share"] = (df["gen_solar"] + df["gen_wind"]) / df["gen_total"]
    df["nonfossil_share"] = 1 - (df["gen_coal"] + df["gen_gas"]) / df["gen_total"]
    df["cap_nonfossil"] = df[[f"cap_{t}" for t in CLEAN]].sum(axis=1)
    df["emissions_mt"] = sum(df[f"gen_{t}"] * ef.get(t, 0) for t in techs) + df["gen_other"] * other_ef
    df["intensity_g_per_kwh"] = 1000 * df["emissions_mt"] / df["gen_total"]

    # Investment, INR crore -> USD billion (2025 prices): GW * (INR cr/MW) * 1000 MW/GW * 1e7 INR/cr / 80 / 1e9
    to_usd_bn = 1000 * 1e7 / A.INR_PER_USD / 1e9
    inv_gen_vre = inv_gen_conv = inv_bess = 0.0
    out = {"inv_gen_vre": [], "inv_gen_conv": [], "inv_bess": []}
    for t, r in df.iterrows():
        if t == df.index.min():
            for key in out:
                out[key].append(0.0)
            continue
        vre = sum(r[f"add_{x}"] * interp_cost(x, t) for x in ("solar", "wind"))
        conv = sum(r[f"add_{x}"] * interp_cost(x, t) for x in ("coal", "hydro", "nuclear", "bio"))
        out["inv_gen_vre"].append(vre * to_usd_bn)
        out["inv_gen_conv"].append(conv * to_usd_bn)
        out["inv_bess"].append(r["add_bess"] * interp_cost("bess", t) * to_usd_bn)
    for key, vals in out.items():
        df[key] = vals
    df["inv_generation"] = df["inv_gen_vre"] + df["inv_gen_conv"]
    df["inv_td"] = df["inv_gen_vre"] * A.TD_RATIO["vre"] + df["inv_gen_conv"] * A.TD_RATIO["conventional"]
    df["inv_storage"] = df["inv_bess"]
    df["inv_total"] = df["inv_generation"] + df["inv_storage"] + df["inv_td"]
    return df


def calibrate_ramp(sc: Scenario, base: dict, target_coal_share: float, lo=-2.0, hi=20.0, tol=1e-6) -> Scenario:
    """Find the ramp slope at which the 2050 coal generation share hits the target."""
    from dataclasses import replace

    def share(s):
        return simulate(replace(sc, ramp_slope=s), base).loc[END_YEAR, "coal_share"]

    if not (share(lo) > target_coal_share > share(hi)):
        raise ValueError(f"{sc.name}: 2050 coal share target {target_coal_share:.3f} is not reachable "
                         f"(range {share(hi):.3f}-{share(lo):.3f}) under the build limits")
    for _ in range(100):
        mid = (lo + hi) / 2
        if share(mid) > target_coal_share:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return replace(sc, ramp_slope=(lo + hi) / 2)
