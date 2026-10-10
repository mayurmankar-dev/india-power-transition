#set document(title: "How fast must India build renewables? Power-sector scenarios to 2050", author: "Mayur Mankar")
#set page(paper: "a4", margin: (x: 2cm, y: 2cm), numbering: "1")
#set text(size: 10pt)
#set par(justify: true, leading: 0.62em)
#set heading(numbering: "1.")
#show heading.where(level: 1): it => block(above: 1.1em, below: 0.6em, text(size: 11.5pt, weight: "bold", it))
#show figure.caption: set text(size: 8.5pt)

#align(left)[
  #text(size: 16pt, weight: "bold")[How fast must India build renewables?] \
  #text(size: 12pt)[Power-sector scenarios for coal, emissions and investment to 2050] \
  #v(0.3em)
  #text(size: 9.5pt)[Mayur Mankar · October 2026 · Research note · Code and data: #link("https://github.com/mayurmankar-dev/india-power-transition")[github.com/mayurmankar-dev/india-power-transition]]
]

#v(0.4em)
#block(fill: rgb("#f3f2ee"), inset: 10pt, radius: 3pt, width: 100%)[
  *Summary.* India's electricity demand is set to roughly quadruple by 2050. This note builds a transparent annual scenario model of the power sector from Ember's 2024 data and benchmarks it against NITI Aayog's 2026 Current Policy and Net Zero scenarios. Four findings stand out:
  - *The current pace of solar and wind deployment is far too slow.* Continuing the 2022–24 average of about 19 GW a year would leave coal at over 70% of generation in 2050. That path would need about 680 GW of new coal plants and emit 4.3 Gt CO2 a year.
  - *Even NITI's current-policy coal share implies coal generation 80% above today's in 2050.* Power-sector CO2 nearly doubles, although grid intensity halves. Annual solar and wind additions must reach about 47 GW by 2030 and 109 GW by 2050, against 28 GW in 2024.
  - *A path aligned with NITI's Net Zero coal share keeps coal generation roughly flat until the mid-2040s.* It needs about 9% more capital than current policy over 2025–2050 (USD 3.7 vs 3.3 trillion). In exchange it avoids about 7 Gt of cumulative CO2 and about 145 GW of new coal capacity.
  - *Electrification raises absolute power-sector emissions even at the same grid intensity.* Delivering NITI's Net Zero demand at the same 22% coal share needs USD 5.2 trillion of investment. It also needs build rates above NITI's own expansion limits from 2030.
]

= Question and approach

India's power sector emitted about 1.1 Gt CO2 in 2024 (Ember), with coal supplying 74% of generation. Demand growth will be the main driver of the sector's emissions and capital needs over the next two decades. This note asks three questions:

1. How fast must solar and wind capacity grow to bend the coal trajectory?
2. What does each pace imply for coal generation, coal capacity and emissions?
3. How much investment does each path require?

The model is deliberately simple and fully traceable, with every assumption sourced in `data/assumptions.csv`. Its value lies in making the arithmetic of the transition explicit. It is not a substitute for least-cost optimisation models such as the TIMES and ORDENA models used by NITI Aayog. Instead, it checks how far a transparent accounting model reproduces their headline results.

= Data and method

*Base year.* The model starts from 2024 national data by fuel from Ember's India Electricity Data (CC-BY-4.0): 462 GW of capacity, 1,804 TWh of generation and 1,121 MtCO2. Capacity factors are 2022–24 averages on a mid-year-capacity basis: solar 18.7%, wind 20.4%, hydro 35.2%, nuclear 78.2%.

*Demand.* Generation requirements grow at the rate implied by NITI Aayog's path from about 2,000 TWh in 2025 to 7,350–7,700 TWh in 2050 under current policy (5.4% a year). Using the growth rate rather than the level keeps the scope consistent, because NITI's totals include captive plants and Ember's base data are utility-scale.

*Supply.* Hydro and bioenergy follow NITI's 2070 capacity ranges. Nuclear follows NITI's 2050 capacity share for each scenario. Gas generation declines to zero by 2050. Solar and wind follow explicit build paths, and their fleet capacity factors rise linearly to the values implied by NITI's 2050 capacity and generation (solar 23.5%, wind 26.3%). Coal supplies the residual. New coal capacity is added whenever existing plants cannot meet coal generation at a load factor that glides from today's 69% to NITI's 65% by 2030. Retirements are not modelled.

*Emissions and investment.* Emissions use Ember's fuel emission factors (lifecycle basis; coal 0.82 tCO2/MWh). Investment multiplies capacity additions by CEA unit costs (2025 prices, from NITI Table 3.7), converted at 80 INR/USD. Battery capacity is sized relative to solar and wind capacity using NITI's 2050 ratios, with replacement after 12 years. Transmission and distribution costs follow NITI's ratio method: 0.75 times generation capex for conventional plants and 1.0 times for solar and wind.

#figure(
  table(
    columns: (auto, 1fr),
    inset: 5pt,
    stroke: 0.4pt + rgb("#c8c7c0"),
    align: (left, left),
    table.header([*Scenario*], [*Definition*]),
    [Slower transition], [Solar and wind additions stay at the 2022–24 average (16.1 GW solar, 2.7 GW wind a year). Current-policy demand.],
    [Current policy], [Additions ramp linearly from the 2024 level, calibrated so that coal's 2050 generation share matches NITI's Current Policy Scenario (33.5%).],
    [Accelerated renewables], [Same demand; ramp calibrated to NITI's Net Zero Scenario coal share (22%), with NITI's Net Zero nuclear and storage ratios.],
    [Net-zero demand (sensitivity)], [As Accelerated, but with NITI's higher Net Zero demand (9,700–10,200 TWh in 2050) and recalibrated to the same 22% coal share.],
  ),
  caption: [Scenario definitions. Benchmarks from NITI Aayog (2026).],
)

= Results

#figure(image("../figures/fig1_generation_mix.png", width: 100%), caption: [Electricity generation by source under each scenario.])

*Pace.* India added about 28 GW of solar and wind in 2024. Matching NITI's current-policy coal share requires about 47 GW a year by 2030, rising to about 109 GW a year by 2050 (Figure 3). At the 2022–24 pace, coal generation nearly quadruples to 5,100 TWh and requires roughly 680 GW of new coal plants. That scale is implausible, which shows the slower path cannot simply be read as "more of today".

*Coal and emissions.* Under current policy, coal's share falls from 74% to 33%. Its absolute generation still rises 80% to about 2,400 TWh, and power-sector CO2 roughly doubles to 2.1 Gt in 2050, even as grid intensity halves to about 300 gCO2/kWh. Only in the accelerated path does coal generation plateau, at about 1,360–1,420 TWh until the mid-2040s. Even there, coal edges up to about 1,575 TWh by 2050 because demand keeps growing (Figure 2).

#figure(image("../figures/fig2_coal_emissions.png", width: 100%), caption: [Coal generation, power-sector CO2 and grid emission intensity.])

*Electrification.* With NITI's Net Zero demand, the same 22% coal share in 2050 implies about 2.0 Gt CO2 from the power sector, 34% more than the accelerated path at current-policy demand. Grid intensity is nearly identical. The extra emissions come purely from serving more demand. In the wider economy they would be offset by lower direct fossil-fuel use in transport, industry and buildings, which this model does not capture.

#figure(image("../figures/fig3_vre_additions.png", width: 82%), caption: [Annual solar and wind additions: history (Ember) and scenarios, against NITI's maximum annual additions (Table 3.6).])

*Build-rate limits.* NITI's study caps annual additions at 50 GW of solar and 15 GW of wind in the 2030s. The current-policy and accelerated paths exceed the solar or wind cap from 2036 and 2034 respectively, and the net-zero-demand path exceeds it from 2030. NITI's own 2050 Net Zero solar capacity (about 2,440 GW) also implies average additions above these limits. This suggests the limits apply to a subset of capacity, such as utility-scale plants. Either way, delivery capacity (land, transmission and manufacturing) is a material risk.

#figure(image("../figures/fig4_investment.png", width: 88%), caption: [Cumulative investment 2025–2050 by component, compared with NITI Aayog's estimates.])

*Investment.* Current policy requires about USD 3.3 trillion over 2025–2050 and the accelerated path about USD 3.7 trillion. The extra USD 0.3 trillion (about 9%) avoids roughly 7 Gt of cumulative CO2 and about 145 GW of new coal capacity. Because this comparison covers capital costs only, it understates the accelerated path's advantage: lower coal generation also saves fuel. Storage and grids account for about 60% of the accelerated path's total, so the transition is as much a financing challenge as a generation one.

#figure(
  table(
    columns: (1.8fr, 1fr, 1fr, 1fr, 1fr),
    inset: 4.5pt,
    stroke: 0.4pt + rgb("#c8c7c0"),
    align: (left, right, right, right, right),
    table.header([*Metric (2050 or 2025–2050)*], [*Model: current policy*], [*NITI CPS*], [*Model: net-zero demand*], [*NITI NZS*]),
    [Solar capacity (GW)], [1,516], [≈1,537], [2,354], [≈2,442],
    [Wind capacity (GW)], [451], [≈437], [736], [≈744],
    [Battery storage (GW)], [452], [420–520], [997], [900–1,150],
    [Grid intensity (gCO2/kWh, Ember basis)], [299], [≈287], [208], [≈225],
    [Investment, total (USD tn)], [3.35], [3.58], [5.23], [5.15],
    [New coal 2025–2045 (GW)], [134], [≈240], [–], [–],
  ),
  caption: [Benchmarks. NITI capacity values are table shares times midpoint totals; NITI grid factors are rescaled to Ember's base-year basis (621 vs 710 gCO2/kWh). Full table: `results/benchmarks_vs_niti.csv`.],
)

*Benchmarks.* Calibrated only to NITI's 2050 coal shares, the model reproduces NITI's 2050 solar, wind and storage capacities within about 5%, and its total investment within about 7%. It finds less new coal than NITI's figure of about 240 GW by 2045, because it does not model retirements of ageing plants or captive coal. Storage investment is lower because pumped hydro is not costed. Transmission and distribution investment is higher because NITI's VRE ratio is applied to all solar and wind.

*Capacity-factor sensitivity.* If solar and wind capacity factors stay at today's levels instead of improving, the current-policy coal share needs 2,494 GW of solar and wind by 2050 rather than 1,967 GW (27% more), and investment rises from USD 3.35 to 4.06 trillion. Better-performing new plants are a load-bearing assumption in official projections.

= Limitations

This is an annual energy-accounting model, not an optimisation or dispatch model:

- *Reliability and prices.* It does not test hourly reliability, curtailment or prices.
- *Fixed paths.* Retirements and the timing of new coal plants follow simple rules rather than economics.
- *Storage.* Battery capacity is scaled from NITI's ratios rather than sized for reliability, and pumped hydro is not costed.
- *Scope.* The base data are utility-scale only; captive plants are excluded.
- *Emissions basis.* Emission factors are Ember's lifecycle values, so absolute emissions are not directly comparable with CEA's grid factors.
- *Missing costs.* Investment figures are undiscounted capital costs in 2025 prices and exclude fuel, operations and financing costs.

Results are indicative and should be read as an explanation of what drives the official scenarios, not as forecasts.

= Implications

1. *The deployment rate is the binding variable.* Bending India's coal trajectory requires solar and wind additions to rise from about 28 GW a year to roughly 47–50 GW a year by 2030 and to keep rising. The 2022–24 pace is consistent only with continued coal expansion.
2. *Coal share and coal volume tell different stories.* Even with ambitious policy, absolute coal generation keeps rising for two decades because demand grows so quickly. Targets and finance decisions for coal plants should be judged on absolute volumes and lock-in, not shares alone.
3. *The transition is a capital-mobilisation problem.* The accelerated path costs only about 9% more capital than current policy, but storage and grids account for about 60% of it. The cost of capital and financing structures will matter as much as technology costs. This is the link to macro-financial modelling of the transition, a natural extension of this work (see my stock-flow consistent model of green public investment: #link("https://github.com/mayurmankar-dev/sfc-green-sim")[github.com/mayurmankar-dev/sfc-green-sim]).

= References

- Ember (2026). _India Electricity Data_ (yearly release, CC-BY-4.0). ember-energy.org/data/india-electricity-data.
- NITI Aayog (2026). _Scenarios Towards Viksit Bharat and Net Zero – Sectoral Insights: Power_ (Vol. 7). Tables 3.6, 3.7, 4.1–4.3, E.1; Figure 4.9; Annexure E.
- Central Electricity Authority. _CO2 Baseline Database for the Indian Power Sector_ and technology cost estimates, as reproduced in NITI Aayog (2026).
