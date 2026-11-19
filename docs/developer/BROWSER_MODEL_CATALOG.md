# Browser models and interaction boundaries

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

The active lesson is `markets`: a deterministic USD/basis-point friction exercise. It neither calls Python nor loads the committed CSV bundles or OPSD. Source links in the preserved browser configuration point to its own historical package revision `c86bf0e52adf06922bbbf35f2274b68485a22660`; this handbook's review uses current pinned source `8058e89e4d3516825a400fe86ac45d2e36b6bef0`. Both identities remain visible. [docs/lesson-config.json:1–317](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/lesson-config.json#L1-L317) [docs/index.html:159–166](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L159-L166)

## Active equation and controls

For model time t in hours,

$$spread=b+12\sin(2\pi t/12)+5\sin(2\pi t/5),\quad edge=spread-fees-slippage,$$

$$P\&L=N\,edge/10000,\qquad cost=N(fees+slippage)/10000.$$

| Input key | Range | Config default | Unit |
| --- | --- | ---: | --- |
| `baseSpreadBps` | 0…100, step 1 | 40 | bps |
| `feeBps` | 0…50, step 1 | 10 | bps, round trip |
| `slippageBps` | 0…30, step 1 | 5 | bps |
| `notionalUSD` | 1000…100000, step 1000 | 10000 | USD |

The pure library's fallback defaults are 35/15/8/10000, whereas the active configuration overrides them to 40/10/5/10000. Time is clamped to [0,24]; provided finite numeric parameters are clamped to each built-in range, and invalid/missing values fall back to defaults. Slider step sizes do not imply the pure API rounds values to those steps. [docs/index.html:214–219](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L214-L219) [docs/index.html:243–258](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L243-L258) [docs/index.html:369–381](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L369-L381)

Outputs are `spreadBps`, `netEdgeBps`, `netPnlUSD`, `costUSD`. P&L is a single hypothetical opportunity, not an integral of the waveform. There is no battery energy, state of charge, degradation, terminal inventory, execution latency or accepted-order model in this screen. [docs/index.html:296–299](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L296-L299)

## Exported JavaScript API

| Export | Contract |
| --- | --- |
| `LabSimulation.MODEL_SPECS` | Ten built-in teaching models with ranges, defaults, metrics and assumptions |
| `getModelSpec(kind)` | Returns spec or throws for an unknown kind |
| `resolveParameters(kind, provided)` | Produces the validated/clamped numeric parameter map |
| `evaluateModel(kind, provided, time)` | Returns the selected model's deterministic numeric metric map |
| `checkCheckpoint(check, metrics)` | Returns `pass`, `fail` or `invalid`, value, target/operator/tolerance; strict `<`/`>` ignore tolerance |
| `LabDashboard.getState()` | Snapshot of kind, copied params, time, play state, selected metric and active module |
| `LabDashboard.evaluateModel`, `.getModelSpec` | Same pure functions exposed for classroom inspection |

[docs/index.html:243–348](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L243-L348) [docs/index.html:481–482](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L481-L482)

## Other bundled modes

The UMD block contains battery, thermal, degradation, grid, cooling, agents, control, security and charging teaching modes in addition to markets. They are dormant for this repository's configured lesson. Their equations and exports were inspected/enumerated, but the eight numerical checkpoint executions apply only to the active market mode. None is a native VoltRL policy implementation. [docs/index.html:171–241](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L171-L241) [docs/index.html:260–329](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L260-L329)

| Kind | Time horizon | Model boundary |
| --- | --- | --- |
| `battery` | 6 h | Ohmic constant-current discharge, depletion cutoff and lumped cooling; no native MWh arbitrage |
| `thermal` | 60 min | One thermal mass with constant heat input and linear removal |
| `degradation` | 1000 cycles | Uncalibrated exponential capacity fade, distinct from native DOD/SOC cost |
| `grid` | 24 h | Ideal daily demand/solar and fixed external battery power; no energy inventory |
| `cooling` | 60 min | Synthetic compute load, constant COP and heuristic inlet temperature |
| `agents` | 30 min | Deterministic fluid queue with coordination overhead |
| `markets` | 24 h | Active spread/cost arithmetic above |
| `control` | 20 s | Closed-form second-order step response from rest |
| `security` | 60 min | Staffing/alert fluid balance, assuming automatic resolutions correct |
| `charging` | 120 min | Constant effective power to 80%, then exponential taper |

## Local UI data

The lab creates 241 curve samples, exposes the current point in metric cards and canvas text, and exports numeric CSV with current input parameters. Config export is the canonical embedded JSON, not current slider state. Lesson outcomes are kept in the page's in-memory `Map`; the six-path portfolio guide instead stores notes/completion/motion locally under a key containing repository and source revision. A path marked reviewed is a personal record, not a test result. [docs/index.html:410–419](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L410-L419) [docs/index.html:463–482](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L463-L482) [docs/portfolio/index.html:351–380](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/portfolio/index.html#L351-L380)

The native catalog filters source-material cards and copies commands; the gallery loads animated media only after a click and removes it when stopped. Archived waveform curves are decorative formulas with rate/temperature/damping controls, not native battery equations. [docs/native-lessons.html:50–100](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/native-lessons.html#L50-L100) [docs/animations/gallery.js:1–20](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/animations/gallery.js#L1-L20) [docs/animations/waveform.html:148–208](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/animations/waveform.html#L148-L208)

The documentation change adds navigation only to the existing pages. The derived handbook uses plain HTML/CSS and native mathematical markup with no script dependency. Runtime keyboard, screen-reader, export and storage checks still need an actual browser session; pure-model execution and static inspection do not establish those outcomes.

## Complete built-in parameter and metric keys

This index is read from the actual inline export. Bounds/defaults below are the library fallback values; the active market configuration overrides its defaults as explained above. Nonactive modes remain uncalibrated teaching functions.

| Kind | Parameters: key, unit, min…max, default | Returned metrics: key and unit |
| --- | --- | --- |
| `battery` | `capacityAh` (Ah), 20…200, default 100; `currentA` (A), 0…30, default 12; `resistanceOhm` (Ω), 0.005…0.1, default 0.035; `ambientC` (°C), 0…45, default 25; `initialSoc` (%), 30…100, default 90 | `socPct` (%); `voltageV` (V); `temperatureC` (°C); `powerKW` (kW) |
| `thermal` | `heatW` (W), 100…3000, default 1200; `coolingWK` (W/K), 10…120, default 40; `capacityJPerK` (J/K), 3000…60000, default 18000; `ambientC` (°C), 0…45, default 25 | `temperatureC` (°C); `heatRemovedW` (W); `storedEnergyKJ` (kJ); `residualW` (W) |
| `degradation` | `fadePer1000Pct` (% / 1k cycles), 2…40, default 18; `temperatureC` (°C), 10…50, default 25; `cRate` (C), 0.2…3, default 1; `initialCapacityAh` (Ah), 10…200, default 100 | `retentionPct` (%); `capacityAh` (Ah); `resistanceGrowthPct` (%); `throughputKWh` (kWh) |
| `grid` | `demandKW` (kW), 100…1200, default 500; `solarKW` (kW), 0…1400, default 600; `batteryKW` (kW), 0…300, default 100; `carbonGPerKWh` (g/kWh), 0…800, default 400 | `gridImportKW` (kW); `solarOutputKW` (kW); `renewablePct` (%); `emissionsKgPerH` (kg/h) |
| `cooling` | `serverCount` (servers), 10…500, default 100; `utilizationPct` (%), 10…90, default 65; `ambientC` (°C), 5…45, default 30; `coolingEfficiency` (ratio), 1.5…6, default 3.5 | `itKW` (kW); `coolingKW` (kW); `pue` (×); `inletC` (°C) |
| `agents` | `arrivalRate` (tasks/min), 2…40, default 12; `agentCount` (agents), 1…12, default 4; `serviceRate` (tasks/min), 1…10, default 4; `coordinationPct` (%), 0…70, default 20 | `backlog` (tasks); `throughput` (tasks/min); `utilizationPct` (%); `waitMinutes` (min) |
| `markets` | `baseSpreadBps` (bps), 0…100, default 35; `feeBps` (bps), 0…50, default 15; `slippageBps` (bps), 0…30, default 8; `notionalUSD` (USD), 1000…100000, default 10000 | `spreadBps` (bps); `netEdgeBps` (bps); `netPnlUSD` (USD); `costUSD` (USD) |
| `control` | `setpoint` (units), 10…100, default 60; `damping` (ζ), 0.1…2, default 0.5; `naturalFrequency` (rad/s), 0.2…3, default 1; `gain` (×), 0.5…1.5, default 1 | `output` (units); `error` (units); `velocity` (units/s); `overshootPct` (%) |
| `security` | `alertRate` (alerts/min), 2…60, default 20; `analystCount` (people), 1…12, default 4; `reviewRate` (alerts/min/person), 1…10, default 4; `automationPct` (%), 0…90, default 35 | `backlog` (alerts); `coveragePct` (%); `reviewedAlerts` (alerts); `workloadPct` (%) |
| `charging` | `capacityKWh` (kWh), 20…120, default 60; `chargerKW` (kW), 5…180, default 60; `initialSoc` (%), 5…70, default 20; `efficiencyPct` (%), 75…99, default 92 | `socPct` (%); `chargingKW` (kW); `energyAddedKWh` (kWh); `lossKW` (kW) |

[docs/index.html:171–241](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L171-L241)
