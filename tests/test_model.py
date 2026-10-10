import math

import pytest

from ipt import assumptions as A
from ipt.data import load_national, base_year_parameters
from ipt.model import simulate, interp_cost
from ipt.scenarios import build


@pytest.fixture(scope="module")
def base():
    return base_year_parameters(load_national())


@pytest.fixture(scope="module")
def results(base):
    return {sc.name: simulate(sc, base) for sc in build(base)}


def test_base_year_matches_ember(base, results):
    """2024 rows reproduce Ember's national totals (1,804 TWh, 1,121 MtCO2)."""
    df = results["current_policy"]
    assert math.isclose(df.loc[2024, "gen_total"], base["total_generation_twh"], rel_tol=1e-9)
    assert math.isclose(df.loc[2024, "emissions_mt"], base["total_emissions_mt"], rel_tol=1e-3)


def test_supply_meets_demand_every_year(results):
    for name, df in results.items():
        gap = (df.loc[2025:, "gen_total"] - df.loc[2025:, "demand"]).abs().max()
        assert gap < 1e-6, name


def test_calibration_hits_niti_coal_shares(results):
    assert math.isclose(results["current_policy"].loc[2050, "coal_share"], A.COAL_SHARE_2050["cps"], abs_tol=1e-4)
    assert math.isclose(results["accelerated"].loc[2050, "coal_share"], A.COAL_SHARE_2050["nzs"], abs_tol=1e-4)
    assert math.isclose(results["nz_demand"].loc[2050, "coal_share"], A.COAL_SHARE_2050["nzs"], abs_tol=1e-4)


def test_coal_capacity_never_falls_and_plf_respects_ceiling(results):
    for name, df in results.items():
        assert (df["cap_coal"].diff().dropna() >= -1e-9).all(), name
        assert (df.loc[2030:, "coal_plf"] <= A.COAL_PLF_INTERMEDIATE + 1e-6).all(), name


def test_investment_is_non_negative(results):
    for name, df in results.items():
        assert (df[["inv_generation", "inv_storage", "inv_td"]] >= 0).all().all(), name


def test_niti_implied_capacity_factors():
    cf = A.niti_implied_cf()
    assert 0.23 < cf["solar"] < 0.24
    assert 0.25 < cf["wind"] < 0.28


def test_cost_interpolation():
    assert interp_cost("solar", 2025) == 4.2          # flat before 2030
    assert math.isclose(interp_cost("solar", 2035), 4.1)  # midway 2030-2040
    assert interp_cost("bess", 2050) == 5.6


def test_ordering_of_scenarios(results):
    """More renewables -> less coal and lower cumulative emissions at the same demand."""
    cum = {k: v.loc[2025:2050, "emissions_mt"].sum() for k, v in results.items()}
    assert cum["slower"] > cum["current_policy"] > cum["accelerated"]
