"""Run all scenarios, write results tables and figures.

Usage:  python run.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from ipt import assumptions as A
from ipt.data import load_national, base_year_parameters
from ipt.model import simulate, calibrate_ramp, build_limit
from ipt.scenarios import build

ROOT = Path(__file__).parent
RES, FIG, DATA = ROOT / "results", ROOT / "figures", ROOT / "data"

# Colours: generation sources (validated order for the stacked chart) and scenarios
SRC_COLORS = {"coal": "#e34948", "gas": "#6250d6", "nuclear": "#e87ba4", "bio": "#008300",
              "hydro": "#1baf7a", "wind": "#2a78d6", "solar": "#eda100"}
SRC_LABELS = {"coal": "Coal", "gas": "Gas", "nuclear": "Nuclear", "bio": "Bioenergy",
              "hydro": "Hydro", "wind": "Wind", "solar": "Solar"}
SC_STYLE = {"slower": ("#eb6834", "-"), "current_policy": ("#2a78d6", "-"),
            "accelerated": ("#1baf7a", "-"), "nz_demand": ("#1baf7a", "--")}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
HIGHLIGHT = [2030, 2035, 2040, 2045, 2050]


def style(ax, title, ylabel=None):
    ax.set_facecolor(SURF)
    ax.set_title(title, loc="left", fontsize=10.5, color=INK, fontweight="bold")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=INK2)
    ax.tick_params(colors=INK2, labelsize=8.5, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)


def new_fig(w, h, nrows=1, ncols=1, **kw):
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), dpi=160, **kw)
    fig.patch.set_facecolor(SURF)
    return fig, axes


def header(fig, title, subtitle, sub_y=0.955):
    fig.suptitle(title, x=0.01, y=0.995, ha="left", fontsize=12.5, color=INK, fontweight="bold")
    fig.text(0.01, sub_y, subtitle, fontsize=9, color=INK2, ha="left")


def run():
    for d in (RES, FIG, DATA / "processed"):
        d.mkdir(parents=True, exist_ok=True)
    data = load_national()
    base = base_year_parameters(data)
    scs = build(base)
    res = {sc.name: simulate(sc, base) for sc in scs}
    labels = {sc.name: sc.label for sc in scs}

    # Capacity-factor sensitivity: current policy with today's capacity factors
    cps = next(s for s in scs if s.name == "current_policy")
    from dataclasses import replace
    cps_flat = calibrate_ramp(replace(cps, name="cps_flat_cf", cf_improves=False), base, A.COAL_SHARE_2050["cps"])
    res_flat = simulate(cps_flat, base)

    # --- tables -----------------------------------------------------------
    A.table().to_csv(DATA / "assumptions.csv", index=False)
    hist = pd.concat({k: v for k, v in data.items()}, axis=1).round(3)
    hist.to_csv(DATA / "processed" / "ember_national_by_fuel.csv")
    for name, df in res.items():
        df.round(4).to_csv(RES / f"scenario_{name}.csv")

    rows = []
    for sc in scs:
        df = res[sc.name]
        over = [t for t in df.index if df.loc[t, "add_solar"] > build_limit("solar", t)
                or df.loc[t, "add_wind"] > build_limit("wind", t)]
        rows.append({
            "scenario": sc.label,
            "VRE additions 2030 (GW/yr)": df.loc[2030, ["add_solar", "add_wind"]].sum(),
            "VRE additions 2050 (GW/yr)": df.loc[2050, ["add_solar", "add_wind"]].sum(),
            "Non-fossil capacity 2030 (GW)": df.loc[2030, "cap_nonfossil"],
            "Solar capacity 2050 (GW)": df.loc[2050, "cap_solar"],
            "Wind capacity 2050 (GW)": df.loc[2050, "cap_wind"],
            "Coal generation 2050 (TWh)": df.loc[2050, "gen_coal"],
            "Coal share 2050": df.loc[2050, "coal_share"],
            "New coal 2025-2050 (GW)": df.loc[2025:2050, "add_coal"].sum(),
            "CO2 2050 (Mt)": df.loc[2050, "emissions_mt"],
            "Cumulative CO2 2025-2050 (Gt)": df.loc[2025:2050, "emissions_mt"].sum() / 1000,
            "Grid intensity 2050 (gCO2/kWh)": df.loc[2050, "intensity_g_per_kwh"],
            "Investment 2025-2050, generation (USD tn)": df.loc[2025:2050, "inv_generation"].sum() / 1000,
            "Investment 2025-2050, storage (USD tn)": df.loc[2025:2050, "inv_storage"].sum() / 1000,
            "Investment 2025-2050, T&D (USD tn)": df.loc[2025:2050, "inv_td"].sum() / 1000,
            "Investment 2025-2050, total (USD tn)": df.loc[2025:2050, "inv_total"].sum() / 1000,
            "Years above NITI build-rate limits": len(over),
            "First year above limits": min(over) if over else None,
        })
    summary = pd.DataFrame(rows).set_index("scenario")
    summary.round(3).to_csv(RES / "summary.csv")

    # Benchmarks against NITI
    # NITI grid factors are on CEA's basis (direct CO2, net generation); rescale to this model's
    # Ember lifecycle basis using the ratio of the two in the base year (621 vs 710 g/kWh).
    ember_base = 1000 * base["total_emissions_mt"] / base["total_generation_twh"]
    to_ember_basis = lambda ef: ef * 1000 * ember_base / (A.CEA_GRID_EF["2024-25"] * 1000)
    bench = pd.DataFrame([
        ("Solar capacity 2050 (GW)", res["current_policy"].loc[2050, "cap_solar"], A.SOLAR_CAP_SHARE_2050["cps"] * A.TOTAL_CAP_2050_GW["cps"],
         res["nz_demand"].loc[2050, "cap_solar"], A.SOLAR_CAP_SHARE_2050["nzs"] * A.TOTAL_CAP_2050_GW["nzs"]),
        ("Wind capacity 2050 (GW)", res["current_policy"].loc[2050, "cap_wind"], A.WIND_CAP_SHARE_2050["cps"] * A.TOTAL_CAP_2050_GW["cps"],
         res["nz_demand"].loc[2050, "cap_wind"], A.WIND_CAP_SHARE_2050["nzs"] * A.TOTAL_CAP_2050_GW["nzs"]),
        ("Battery storage 2050 (GW)", res["current_policy"].loc[2050, "cap_bess"], A.BESS_GW_2050["cps"],
         res["nz_demand"].loc[2050, "cap_bess"], A.BESS_GW_2050["nzs"]),
        ("Grid intensity 2050, Ember basis (gCO2/kWh; NITI rescaled)", res["current_policy"].loc[2050, "intensity_g_per_kwh"],
         to_ember_basis(A.GRID_EF_2050["cps"]), res["nz_demand"].loc[2050, "intensity_g_per_kwh"], to_ember_basis(A.GRID_EF_2050["nzs"])),
        ("Investment 2025-2050, generation (USD tn)", summary.loc[labels["current_policy"], "Investment 2025-2050, generation (USD tn)"],
         A.INVESTMENT_2025_2050_TUSD["cps"]["generation"], summary.loc[labels["nz_demand"], "Investment 2025-2050, generation (USD tn)"],
         A.INVESTMENT_2025_2050_TUSD["nzs"]["generation"]),
        ("Investment 2025-2050, storage (USD tn)", summary.loc[labels["current_policy"], "Investment 2025-2050, storage (USD tn)"],
         A.INVESTMENT_2025_2050_TUSD["cps"]["storage"], summary.loc[labels["nz_demand"], "Investment 2025-2050, storage (USD tn)"],
         A.INVESTMENT_2025_2050_TUSD["nzs"]["storage"]),
        ("Investment 2025-2050, T&D (USD tn)", summary.loc[labels["current_policy"], "Investment 2025-2050, T&D (USD tn)"],
         A.INVESTMENT_2025_2050_TUSD["cps"]["t&d"], summary.loc[labels["nz_demand"], "Investment 2025-2050, T&D (USD tn)"],
         A.INVESTMENT_2025_2050_TUSD["nzs"]["t&d"]),
        ("Investment 2025-2050, total (USD tn)", summary.loc[labels["current_policy"], "Investment 2025-2050, total (USD tn)"],
         A.INVESTMENT_2025_2050_TUSD["cps"]["total"], summary.loc[labels["nz_demand"], "Investment 2025-2050, total (USD tn)"],
         A.INVESTMENT_2025_2050_TUSD["nzs"]["total"]),
        ("New coal capacity 2025-2045 (GW)", res["current_policy"].loc[2025:2045, "add_coal"].sum(), A.NEW_COAL_BY_2045_CPS_GW, None, None),
    ], columns=["metric", "This model: Current policy", "NITI CPS", "This model: net-zero demand", "NITI NZS"]).set_index("metric")
    bench.round(2).to_csv(RES / "benchmarks_vs_niti.csv")

    sens = pd.DataFrame({
        "Capacity factors improve (central)": [res["current_policy"].loc[2050, ["cap_solar", "cap_wind"]].sum(),
                                               summary.loc[labels["current_policy"], "Investment 2025-2050, total (USD tn)"]],
        "Capacity factors stay at 2022-24 level": [res_flat.loc[2050, ["cap_solar", "cap_wind"]].sum(),
                                                   res_flat.loc[2025:2050, "inv_total"].sum() / 1000],
    }, index=["Solar + wind capacity 2050 (GW)", "Investment 2025-2050 (USD tn)"])
    sens.round(2).to_csv(RES / "sensitivity_capacity_factor.csv")

    figures(res, labels, data)
    return base, res, summary, bench, sens


def figures(res, labels, data):
    order = ["coal", "gas", "nuclear", "bio", "hydro", "wind", "solar"]

    # 1. Generation mix, small multiples
    fig, axes = new_fig(11, 7.4, 2, 2, sharey=True)
    for ax, name in zip(axes.flat, ["slower", "current_policy", "accelerated", "nz_demand"]):
        df = res[name]
        ys = [df[f"gen_{s}"] + (df["gen_other"] if s == "bio" else 0) for s in order]
        ax.stackplot(df.index, [y / 1000 for y in ys], colors=[SRC_COLORS[s] for s in order],
                     edgecolor=SURF, linewidth=0.6, labels=[SRC_LABELS[s] for s in order])
        style(ax, labels[name], "Generation (thousand TWh)" if name in ("slower", "accelerated") else None)
        ax.set_xlim(2024, 2050)
        share = df.loc[2050, "coal_share"]
        ax.text(0.02, 0.93, f"Coal share 2050: {share:.0%}", transform=ax.transAxes, fontsize=8.5, color=INK2)
    handles, lbls = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles[::-1], lbls[::-1], loc="lower center", ncol=7, frameon=False, fontsize=8.5,
               labelcolor=INK, bbox_to_anchor=(0.5, -0.005))
    header(fig, "India's electricity generation by source, 2024-2050",
           "2024 is Ember data; later years are model scenarios. Bioenergy includes small 'other' sources.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(FIG / "fig1_generation_mix.png", facecolor=SURF, bbox_inches="tight")
    plt.close(fig)

    # 2. Coal generation, emissions, intensity
    fig, axes = new_fig(12, 4.2, 1, 3)
    panels = [("Coal generation", "TWh", "gen_coal", 1), ("Power-sector CO2", "Mt CO2", "emissions_mt", 1),
              ("Grid emission intensity", "gCO2/kWh", "intensity_g_per_kwh", 1)]
    for ax, (title, unit, col, scale) in zip(axes, panels):
        for name in ["slower", "current_policy", "accelerated", "nz_demand"]:
            c, ls = SC_STYLE[name]
            ax.plot(res[name].index, res[name][col] / scale, color=c, linestyle=ls, linewidth=2, label=labels[name])
        style(ax, title, unit)
        ax.set_xlim(2024, 2050)
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="lower center", ncol=4, frameon=False, fontsize=9, labelcolor=INK,
               bbox_to_anchor=(0.5, -0.02))
    header(fig, "Coal use and emissions under each scenario",
           "Emissions use Ember's lifecycle emission factors. Dashed line: same coal share as Accelerated, with net-zero electrification demand.",
           sub_y=0.905)
    fig.tight_layout(rect=(0, 0.07, 1, 0.9))
    fig.savefig(FIG / "fig2_coal_emissions.png", facecolor=SURF, bbox_inches="tight")
    plt.close(fig)

    # 3. Annual solar + wind additions vs history and NITI build-rate limits
    cap = data["capacity_gw"]
    hist_add = (cap["solar"] + cap["wind"]).diff().loc[2020:]
    fig, ax = new_fig(8.5, 4.6)
    ax.bar(hist_add.index, hist_add.values, color="#8a8985", width=0.7, label="Historical (Ember)")
    for name in ["slower", "current_policy", "accelerated", "nz_demand"]:
        c, ls = SC_STYLE[name]
        df = res[name].loc[2025:]
        ax.plot(df.index, df["add_solar"] + df["add_wind"], color=c, linestyle=ls, linewidth=2, label=labels[name])
    lim_years = list(range(2030, 2051))
    lim_vals = [build_limit("solar", min(y, 2049)) + build_limit("wind", min(y, 2049)) for y in lim_years]
    ax.step(lim_years, lim_vals, where="post",
            color=INK2, linewidth=1.2, linestyle=":", label="NITI max. additions (solar + wind)")
    style(ax, "Annual solar + wind additions", "GW per year")
    ax.set_xlim(2019.5, 2050.5)
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "fig3_vre_additions.png", facecolor=SURF, bbox_inches="tight")
    plt.close(fig)

    # 4. Cumulative investment 2025-2050 vs NITI
    comp = [("inv_generation", "Generation", "#2a78d6"), ("inv_storage", "Storage", "#eb6834"),
            ("inv_td", "Transmission & distribution", "#1baf7a")]
    cats = [labels[n] for n in ["slower", "current_policy", "accelerated", "nz_demand"]] + ["NITI CPS", "NITI NZS"]
    vals = {k: [res[n].loc[2025:2050, k].sum() / 1000 for n in ["slower", "current_policy", "accelerated", "nz_demand"]]
            + [A.INVESTMENT_2025_2050_TUSD["cps"][kk], A.INVESTMENT_2025_2050_TUSD["nzs"][kk]]
            for k, kk in (("inv_generation", "generation"), ("inv_storage", "storage"), ("inv_td", "t&d"))}
    fig, ax = new_fig(9, 4.8)
    left = [0.0] * len(cats)
    ypos = [6.2, 5.2, 4.2, 3.2, 1.0, 0.0]   # gap between model runs and NITI benchmarks
    for key, lab, col in comp:
        ax.barh(ypos, vals[key], left=left, color=col, height=0.62, label=lab, edgecolor=SURF, linewidth=1.5)
        left = [l + v for l, v in zip(left, vals[key])]
    for y, total in zip(ypos, left):
        ax.text(total + 0.06, y, f"{total:.1f}", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels([c.replace("Sensitivity: net-zero electrification demand", "Net-zero demand (sensitivity)")
                        for c in cats], fontsize=8.5, color=INK)
    ax.axhline(2.1, color=INK2, linewidth=0.8, linestyle=":")
    ax.text(0.02, 1.75, "NITI Aayog benchmarks (include captive plants and pumped hydro)", fontsize=8, color=INK2, va="bottom",
            transform=ax.get_yaxis_transform())
    style(ax, "Cumulative power-sector investment, 2025-2050", None)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("USD trillion (2025 prices, 80 INR/USD)", fontsize=9, color=INK2)
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK, loc="upper center", ncol=3,
              bbox_to_anchor=(0.5, -0.13))
    fig.tight_layout()
    fig.savefig(FIG / "fig4_investment.png", facecolor=SURF, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    base, res, summary, bench, sens = run()
    pd.set_option("display.width", 200)
    print(summary.T.round(2).to_string())
    print("\n", bench.round(2).to_string())
    print("\n", sens.round(2).to_string())
