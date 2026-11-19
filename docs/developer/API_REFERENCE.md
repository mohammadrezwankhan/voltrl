# Native declaration catalog

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

This catalog lists every non-underscore function/class declared at top level in the nine native modules, plus their non-underscore methods/properties and declared dataclass fields. It is generated from the reviewed Python AST. Private helpers and test/tool declarations remain accounted in the operational interface inventory; imported third-party names are outside this API catalog. Argument defaults are optional; signatures preserve explicit calling conventions. See [contracts and CLI](API_CLI_AND_INTERFACES.md) for units, shapes, errors and file behavior.

## `voltrl.py`

### `Action`

[voltrl.py:36–45](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L36-L45)

Discrete control actions.

The enumeration value is the action-array index, not an energy quantity.
SOC increments are defined by :meth:`BatterySpec.soc_delta`.

Declared fields / enum values:

```python
CHARGE = 0
IDLE = 1
DISCHARGE = 2
```

### `BatterySpec`

[voltrl.py:51–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L51-L194)

Physical and economic parameters of the BESS.

Declared fields / enum values:

```python
capacity_mwh: float = 500.0
max_power_mw: float = 100.0
interval_hours: float = 1.0
charge_efficiency: float = 1.0
discharge_efficiency: float = 1.0
degradation_cost_per_mwh: float = 0.0
nonlinear_degradation: bool = False
dod_stress_exponent: float = 1.6
linear_degradation_fraction: float = 0.25
soc_stress_cost_per_hour: float = 0.0
```

#### `BatterySpec.energy_step_mwh`

[voltrl.py:96–98](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L96-L98)

```python
@property
BatterySpec.energy_step_mwh(self) -> float
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatterySpec.soc_levels`

[voltrl.py:100–103](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L100-L103)

```python
@property
BatterySpec.soc_levels(self) -> np.ndarray
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatterySpec.soc_delta`

[voltrl.py:105–111](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L105-L111)

```python
BatterySpec.soc_delta(self, action: int | Action) -> float
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatterySpec.degradation_cost`

[voltrl.py:113–165](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L113-L165)

```python
BatterySpec.degradation_cost(self, action: int | Action, soc_before_mwh: float | None=None) -> float
```

Return the stage degradation cost.

The legacy model is linear in internal energy throughput.  The revised
model retains a small linear component and adds a convex cumulative
depth-of-discharge (DOD) potential on discharge plus an hourly extreme-
SOC stress term.  The DOD potential is normalized so a full 0-100-0%
cycle has the same nominal cost as the legacy linear proxy, while
shallow cycles are cheaper and deeper excursions are progressively
more expensive.

#### `BatterySpec.reward_components`

[voltrl.py:167–180](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L167-L180)

```python
BatterySpec.reward_components(self, price: float, action: int | Action, soc_before_mwh: float | None=None) -> tuple[float, float, float]
```

Return energy-market cash flow, degradation cost, and net reward.

#### `BatterySpec.realized_reward`

[voltrl.py:182–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L182-L194)

```python
BatterySpec.realized_reward(self, price: float, action: int | Action, soc_before_mwh: float | None=None) -> float
```

One-hour cash flow in currency units.

Positive SOC movement requires grid purchases of ``delta / eta_c``;
negative movement sells ``-delta * eta_d`` to the grid.

### `SolverConfig`

[voltrl.py:197–213](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L197-L213)

Declared fields / enum values:

```python
gamma: float = 0.99
tolerance: float = 1e-08
max_iterations: int = 100000
```

### `PriceDiscretizer`

[voltrl.py:216–266](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L216-L266)

Quantile price discretizer with fitted representative prices.

Declared fields / enum values:

```python
edges: np.ndarray
representatives: np.ndarray
counts: np.ndarray
```

#### `PriceDiscretizer.n_bins`

[voltrl.py:224–226](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L224-L226)

```python
@property
PriceDiscretizer.n_bins(self) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `PriceDiscretizer.fit`

[voltrl.py:228–248](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L228-L248)

```python
@classmethod
PriceDiscretizer.fit(cls, prices: Sequence[float], n_bins: int) -> 'PriceDiscretizer'
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `PriceDiscretizer.transform`

[voltrl.py:250–255](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L250-L255)

```python
PriceDiscretizer.transform(self, prices: Sequence[float]) -> np.ndarray
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `PriceDiscretizer.interval_labels`

[voltrl.py:257–266](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L257-L266)

```python
PriceDiscretizer.interval_labels(self, observed_prices: Sequence[float]) -> list[str]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `estimate_price_transition`

[voltrl.py:278–307](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L278-L307)

```python
estimate_price_transition(price_bins: Sequence[int], n_bins: int, prior_strength: float=1.0) -> tuple[np.ndarray, np.ndarray]
```

Estimate a row-stochastic first-order price transition matrix.

A Dirichlet empirical-marginal prior prevents zero-probability rows while
preserving observed transition frequencies as the sample grows.

### `select_bin_count_bic`

[voltrl.py:310–370](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L310-L370)

```python
select_bin_count_bic(prices: Sequence[float], candidates: Iterable[int]=range(4, 11), validation_fraction: float=0.2, prior_strength: float=1.0) -> tuple[int, pd.DataFrame]
```

Select a quantile-bin count using chronological validation and BIC.

For each candidate, the first-order Markov kernel is fitted on the early
training segment and scored on the held-out tail.  To make likelihoods
comparable across different bin counts, the categorical transition
probability is converted to a piecewise-uniform conditional *density* by
dividing by the destination-bin width.  The criterion is
``BIC = -2 log L_density + (k(k-1) + k-1) log(n_validation_transitions)``;
the final term counts transition and interior-edge parameters.

### `BatteryArbitrageMDP`

[voltrl.py:373–481](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L373-L481)

Finite joint SOC-price MDP.

Declared fields / enum values:

```python
battery: BatterySpec
price_representatives: np.ndarray
price_transition: np.ndarray
transition: np.ndarray
reward: np.ndarray
valid_actions: np.ndarray
soc_levels: np.ndarray
```

#### `BatteryArbitrageMDP.n_price_bins`

[voltrl.py:385–387](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L385-L387)

```python
@property
BatteryArbitrageMDP.n_price_bins(self) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatteryArbitrageMDP.n_soc_levels`

[voltrl.py:389–391](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L389-L391)

```python
@property
BatteryArbitrageMDP.n_soc_levels(self) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatteryArbitrageMDP.n_states`

[voltrl.py:393–395](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L393-L395)

```python
@property
BatteryArbitrageMDP.n_states(self) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatteryArbitrageMDP.n_actions`

[voltrl.py:397–399](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L397-L399)

```python
@property
BatteryArbitrageMDP.n_actions(self) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatteryArbitrageMDP.state_index`

[voltrl.py:401–402](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L401-L402)

```python
BatteryArbitrageMDP.state_index(self, soc_index: int, price_bin: int) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatteryArbitrageMDP.decode_state`

[voltrl.py:404–405](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L404-L405)

```python
BatteryArbitrageMDP.decode_state(self, state: int) -> tuple[int, int]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatteryArbitrageMDP.build`

[voltrl.py:407–461](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L407-L461)

```python
@classmethod
BatteryArbitrageMDP.build(cls, battery: BatterySpec, price_representatives: Sequence[float], price_transition: np.ndarray) -> 'BatteryArbitrageMDP'
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BatteryArbitrageMDP.validate`

[voltrl.py:463–481](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L463-L481)

```python
BatteryArbitrageMDP.validate(self) -> None
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `SolverResult`

[voltrl.py:484–491](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L484-L491)

Declared fields / enum values:

```python
values: np.ndarray
policy: np.ndarray
iterations: int
converged: bool
runtime_seconds: float
log: pd.DataFrame
```

### `bellman_q`

[voltrl.py:494–498](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L494-L498)

```python
bellman_q(mdp: BatteryArbitrageMDP, values: np.ndarray, gamma: float) -> np.ndarray
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `value_iteration`

[voltrl.py:501–528](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L501-L528)

```python
value_iteration(mdp: BatteryArbitrageMDP, config: SolverConfig=SolverConfig()) -> SolverResult
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `evaluate_policy_exact`

[voltrl.py:531–542](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L531-L542)

```python
evaluate_policy_exact(mdp: BatteryArbitrageMDP, policy: np.ndarray, gamma: float) -> np.ndarray
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `policy_iteration`

[voltrl.py:545–580](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L545-L580)

```python
policy_iteration(mdp: BatteryArbitrageMDP, config: SolverConfig=SolverConfig()) -> SolverResult
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `policy_bellman_residual`

[voltrl.py:583–588](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L583-L588)

```python
policy_bellman_residual(mdp: BatteryArbitrageMDP, values: np.ndarray, gamma: float) -> float
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `nearest_soc_index`

[voltrl.py:591–599](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L591-L599)

```python
nearest_soc_index(mdp: BatteryArbitrageMDP, initial_soc_mwh: float) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `simulate_policy`

[voltrl.py:602–645](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L602-L645)

```python
simulate_policy(prices: Sequence[float], timestamps: Sequence[object], discretizer: PriceDiscretizer, mdp: BatteryArbitrageMDP, policy: np.ndarray, initial_soc_mwh: float) -> pd.DataFrame
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `perfect_foresight_dispatch`

[voltrl.py:648–714](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L648-L714)

```python
perfect_foresight_dispatch(prices: Sequence[float], timestamps: Sequence[object], battery: BatterySpec, initial_soc_mwh: float, terminal_salvage_price: float) -> pd.DataFrame
```

Finite-horizon clairvoyant benchmark solved by backward induction.

### `trajectory_metrics`

[voltrl.py:717–797](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L717-L797)

```python
trajectory_metrics(learned: pd.DataFrame, perfect: pd.DataFrame, battery: BatterySpec, initial_soc_mwh: float, terminal_salvage_price: float) -> dict[str, float | int]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `generate_synthetic_prices`

[voltrl.py:800–834](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L800-L834)

```python
generate_synthetic_prices(hours: int=17520, seed: int=42) -> pd.DataFrame
```

Create a reproducible hourly series with seasonality and price regimes.

### `load_price_data`

[voltrl.py:837–865](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L837-L865)

```python
load_price_data(csv_path: str | None, price_column: str, timestamp_column: str | None, synthetic_hours: int, seed: int) -> tuple[pd.DataFrame, str]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `make_policy_table`

[voltrl.py:868–889](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L868-L889)

```python
make_policy_table(mdp: BatteryArbitrageMDP, policy: np.ndarray, discretizer: PriceDiscretizer, train_prices: Sequence[float]) -> pd.DataFrame
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `save_figures`

[voltrl.py:892–986](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L892-L986)

```python
save_figures(output_dir: Path, train: pd.DataFrame, test: pd.DataFrame, mdp: BatteryArbitrageMDP, discretizer: PriceDiscretizer, vi: SolverResult, pi: SolverResult, learned: pd.DataFrame, perfect: pd.DataFrame) -> None
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `run_experiment`

[voltrl.py:1001–1168](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1001-L1168)

```python
run_experiment(args: argparse.Namespace) -> dict[str, object]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `build_parser`

[voltrl.py:1171–1203](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1171-L1203)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[voltrl.py:1206–1221](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1206-L1221)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.


## `voltrl_benchmark.py`

### `StateModel`

[voltrl_benchmark.py:77–90](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L77-L90)

Discretized exogenous-state model with full-support emissions.

Declared fields / enum values:

```python
discretizer: PriceDiscretizer
transition: np.ndarray
emission_mean: np.ndarray
emission_std: np.ndarray
calendar_aware: bool
transition_counts: np.ndarray
```

#### `StateModel.n_bins`

[voltrl_benchmark.py:88–90](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L88-L90)

```python
@property
StateModel.n_bins(self) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `SeasonalARModel`

[voltrl_benchmark.py:93–102](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L93-L102)

Regularized seasonal autoregression fitted on training data only.

Declared fields / enum values:

```python
lags: tuple[int, ...]
coefficients: np.ndarray
price_mean: float
price_scale: float
clip_low: float
clip_high: float
```

### `chronological_split`

[voltrl_benchmark.py:127–136](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L127-L136)

```python
chronological_split(frame: pd.DataFrame, train_fraction: float=0.7) -> tuple[pd.DataFrame, pd.DataFrame]
```

Split once in chronological order; no test value enters model fitting.

### `chronological_day_split`

[voltrl_benchmark.py:139–155](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L139-L155)

```python
chronological_day_split(frame: pd.DataFrame, train_fraction: float=0.7) -> tuple[pd.DataFrame, pd.DataFrame, int]
```

Chronologically split complete UTC delivery days for block scheduling.

### `fit_state_model`

[voltrl_benchmark.py:173–224](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L173-L224)

```python
fit_state_model(frame: pd.DataFrame, n_bins: int, calendar_aware: bool, prior_strength: float=12.0) -> StateModel
```

Fit a price-only or hour-conditioned transition kernel.

A hierarchical empirical-marginal Dirichlet prior prevents zero rows and
stabilizes the expanded high-resolution candidate set.  In
the calendar-aware model, T[h, i, j] predicts the next price bin from the
current UTC hour and current price bin; the next hour is deterministic.

### `continuous_predictive_nll`

[voltrl_benchmark.py:227–258](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L227-L258)

```python
continuous_predictive_nll(model: StateModel, frame: pd.DataFrame) -> float
```

Mean next-price negative log density under a Gaussian mixture.

Unlike the previous truncated-bin likelihood, every component has support
over the real line, so tail observations remain valid and comparable across
candidate bin counts.

### `expanding_window_selection`

[voltrl_benchmark.py:261–295](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L261-L295)

```python
expanding_window_selection(frame: pd.DataFrame, candidates: Iterable[int]) -> tuple[int, pd.DataFrame]
```

Select K using three leakage-free expanding-window validation folds.

### `finite_horizon_policy`

[voltrl_benchmark.py:311–397](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L311-L397)

```python
finite_horizon_policy(model: StateModel, battery: BatterySpec, timestamps: Sequence[object], terminal_salvage_price: float, planner_discount: float=1.0) -> np.ndarray
```

Solve the test-length finite-horizon MDP by backward induction.

The primary experiment uses planner_discount=1, exactly matching the
undiscounted evaluation objective and terminal inventory valuation.
Decisions have shape (time, SOC level, price bin) and depend only on the
fitted model, current state, known calendar hour, and remaining horizon.

### `trajectory_from_actions`

[voltrl_benchmark.py:400–450](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L400-L450)

```python
trajectory_from_actions(frame: pd.DataFrame, actions: Sequence[int], battery: BatterySpec, initial_soc_mwh: float) -> pd.DataFrame
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `simulate_finite_policy`

[voltrl_benchmark.py:453–469](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L453-L469)

```python
simulate_finite_policy(frame: pd.DataFrame, model: StateModel, decisions: np.ndarray, battery: BatterySpec, initial_soc_mwh: float) -> pd.DataFrame
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `idle_trajectory`

[voltrl_benchmark.py:472–477](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L472-L477)

```python
idle_trajectory(frame: pd.DataFrame, battery: BatterySpec, initial_soc_mwh: float) -> pd.DataFrame
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `threshold_trajectory`

[voltrl_benchmark.py:480–495](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L480-L495)

```python
threshold_trajectory(train: pd.DataFrame, test: pd.DataFrame, battery: BatterySpec, initial_soc_mwh: float) -> pd.DataFrame
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `fit_seasonal_ar`

[voltrl_benchmark.py:544–588](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L544-L588)

```python
fit_seasonal_ar(train: pd.DataFrame, lags: tuple[int, ...]=(1, 2, 24, 48, 168), ridge: float=0.001) -> SeasonalARModel
```

Fit a ridge-stabilized seasonal autoregression on the training segment.

### `seasonal_ar_forecast`

[voltrl_benchmark.py:591–652](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L591-L652)

```python
seasonal_ar_forecast(model: SeasonalARModel, observed_prices: np.ndarray, timestamps: pd.Series, current_index: int, steps: int=23) -> np.ndarray
```

Recursively forecast future prices using only observations available now.

### `seasonal_mpc_trajectory`

[voltrl_benchmark.py:655–709](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L655-L709)

```python
seasonal_mpc_trajectory(train: pd.DataFrame, test: pd.DataFrame, battery: BatterySpec, initial_soc_mwh: float, terminal_salvage_price: float) -> pd.DataFrame
```

Causal 24-hour MPC driven by a training-fitted seasonal AR forecast.

### `day_ahead_block_trajectory`

[voltrl_benchmark.py:712–811](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L712-L811)

```python
day_ahead_block_trajectory(train: pd.DataFrame, test: pd.DataFrame, battery: BatterySpec, initial_soc_mwh: float, terminal_salvage_price: float, forecast_method: str) -> tuple[pd.DataFrame, pd.DataFrame]
```

Commit one feasible 24-hour schedule before each delivery day.

The information set contains prices observed through the preceding UTC
day.  The actual delivery-day clearing prices are used only to settle the
already committed schedule.

### `trajectory_metrics`

[voltrl_benchmark.py:814–851](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L814-L851)

```python
trajectory_metrics(trajectory: pd.DataFrame, battery: BatterySpec, initial_soc_mwh: float, terminal_salvage_price: float) -> dict[str, float | int]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `moving_block_daily_difference`

[voltrl_benchmark.py:854–883](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L854-L883)

```python
moving_block_daily_difference(reference: pd.DataFrame, comparator: pd.DataFrame, seed: int, block_days: int=7, replications: int=5000) -> tuple[float, float, float]
```

Conditional moving-block interval for paired daily cash-profit differences.

### `evaluate_case`

[voltrl_benchmark.py:886–979](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L886-L979)

```python
evaluate_case(frame: pd.DataFrame, case: str, battery: BatterySpec, candidates: Iterable[int], initial_soc_mwh: float=200.0) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]
```

Fit, select, and evaluate every policy on one chronological case.

### `evaluate_day_ahead_case`

[voltrl_benchmark.py:982–1080](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L982-L1080)

```python
evaluate_day_ahead_case(frame: pd.DataFrame, case: str, battery: BatterySpec, initial_soc_mwh: float=200.0) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]
```

Evaluate schedules committed as one 24-hour block before delivery.

### `load_opsd_markets`

[voltrl_benchmark.py:1083–1118](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1083-L1118)

```python
load_opsd_markets(csv_path: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]
```

Load and minimally repair DK1/DK2 from OPSD version 2020-10-06.

### `bootstrap_mean_ci`

[voltrl_benchmark.py:1121–1130](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1121-L1130)

```python
bootstrap_mean_ci(values: Sequence[float], seed: int, replications: int=5000) -> tuple[float, float]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `summarize_seed_results`

[voltrl_benchmark.py:1133–1171](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1133-L1171)

```python
summarize_seed_results(metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `evaluate_single_policy`

[voltrl_benchmark.py:1174–1205](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1174-L1205)

```python
evaluate_single_policy(frame: pd.DataFrame, model: StateModel, battery: BatterySpec, initial_soc_mwh: float, planner_discount: float=1.0) -> dict[str, float | int]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `sensitivity_analysis`

[voltrl_benchmark.py:1208–1254](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1208-L1254)

```python
sensitivity_analysis(frames: dict[str, pd.DataFrame], selected_bins: dict[str, int], initial_soc_mwh: float) -> tuple[pd.DataFrame, pd.DataFrame]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `evaluate_block_policy`

[voltrl_benchmark.py:1257–1286](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1257-L1286)

```python
evaluate_block_policy(frame: pd.DataFrame, battery: BatterySpec, initial_soc_mwh: float) -> dict[str, float | int]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `revision_sensitivity_analysis`

[voltrl_benchmark.py:1289–1400](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1289-L1400)

```python
revision_sensitivity_analysis(synthetic_frame: pd.DataFrame, synthetic_bins: int, historical_frame: pd.DataFrame, initial_soc_mwh: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
```

Evaluate physical, planner, and degradation-model dependence.

### `solver_diagnostics`

[voltrl_benchmark.py:1403–1440](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1403-L1440)

```python
solver_diagnostics(frame: pd.DataFrame, n_bins: int) -> pd.DataFrame
```

Retain VI/PI agreement only as a software-verification diagnostic.

### `make_figures`

[voltrl_benchmark.py:1460–1663](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1460-L1663)

```python
make_figures(output_dir: Path, market_frames: dict[str, pd.DataFrame], selections: pd.DataFrame, synthetic_summary: pd.DataFrame, paired: pd.DataFrame, real_metrics: pd.DataFrame, forecast_summary: pd.DataFrame, sensitivity: pd.DataFrame, gamma_sensitivity: pd.DataFrame, degradation_sensitivity: pd.DataFrame) -> None
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `run_benchmark`

[voltrl_benchmark.py:1666–1835](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1666-L1835)

```python
run_benchmark(args: argparse.Namespace) -> dict[str, object]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `build_parser`

[voltrl_benchmark.py:1838–1852](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1838-L1852)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[voltrl_benchmark.py:1855–1859](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1855-L1859)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.


## `input_provenance.py`

### `SourceVerification`

[input_provenance.py:20–30](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L20-L30)

Verified identity and provenance metadata for an input file.

Declared fields / enum values:

```python
path: Path
bytes: int
sha256: str
dataset: str
version: str
doi: str
url: str
```

### `load_source_record`

[input_provenance.py:33–53](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L33-L53)

```python
load_source_record(record_path: Path) -> dict[str, str]
```

Load and validate a machine-readable source provenance record.

### `verify_source_file`

[input_provenance.py:56–86](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L56-L86)

```python
verify_source_file(source_path: Path, record_path: Path=DEFAULT_SOURCE_RECORD) -> SourceVerification
```

Verify an input file against its versioned provenance record.

### `build_parser`

[input_provenance.py:89–98](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L89-L98)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[input_provenance.py:101–114](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L101-L114)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.


## `artifact_integrity.py`

### `sha256_file`

[artifact_integrity.py:40–45](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L40-L45)

```python
sha256_file(path: Path) -> str
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `build_artifact_inventory`

[artifact_integrity.py:55–77](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L55-L77)

```python
build_artifact_inventory(result_dir: Path, relative_paths: Sequence[str]) -> list[dict[str, object]]
```

Return deterministic size and SHA-256 records for declared artifacts.

### `record_artifact_inventory`

[artifact_integrity.py:111–123](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L111-L123)

```python
record_artifact_inventory(manifest_path: Path) -> int
```

Add or replace integrity records for every manifest output.

### `verify_artifact_manifest`

[artifact_integrity.py:126–193](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L126-L193)

```python
verify_artifact_manifest(manifest_path: Path) -> list[str]
```

Return integrity errors; an empty list means every artifact matched.

### `build_parser`

[artifact_integrity.py:196–204](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L196-L204)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[artifact_integrity.py:207–224](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L207-L224)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.


## `software_provenance.py`

### `capture_software_provenance`

[software_provenance.py:89–130](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L89-L130)

```python
capture_software_provenance(source_root: Path, relative_paths: Sequence[str]=DEFAULT_SOFTWARE_PATHS) -> dict[str, object]
```

Capture a portable source inventory and its Git state when available.

### `record_software_provenance`

[software_provenance.py:140–155](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L140-L155)

```python
record_software_provenance(manifest_path: Path, source_root: Path, relative_paths: Sequence[str]=DEFAULT_SOFTWARE_PATHS) -> int
```

Add or replace software provenance in an experiment manifest.

### `verify_software_provenance`

[software_provenance.py:191–250](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L191-L250)

```python
verify_software_provenance(manifest_path: Path, source_root: Path) -> list[str]
```

Return source-provenance errors; an empty list means a complete match.

### `build_parser`

[software_provenance.py:253–267](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L253-L267)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[software_provenance.py:270–294](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L270-L294)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.


## `experiment_contract.py`

### `verify_experiment_contract`

[experiment_contract.py:544–568](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/experiment_contract.py#L544-L568)

```python
verify_experiment_contract(manifest_path: Path) -> list[str]
```

Return semantic contract errors for one published result bundle.

### `build_parser`

[experiment_contract.py:571–574](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/experiment_contract.py#L571-L574)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[experiment_contract.py:577–595](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/experiment_contract.py#L577-L595)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.


## `synthetic_statistics_contract.py`

### `SeedMetric`

[synthetic_statistics_contract.py:25–33](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L25-L33)

Declared fields / enum values:

```python
line: int
seed: int
policy: str
test_hours: int
inventory_adjusted_profit: float
annualized_adjusted_profit: float
oracle_efficiency_percent: float
```

### `SummaryStatistic`

[synthetic_statistics_contract.py:36–44](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L36-L44)

Declared fields / enum values:

```python
line: int
seeds: int
mean_annualized_profit: float
standard_deviation: float
bootstrap_ci95_lower: float
bootstrap_ci95_upper: float
mean_oracle_efficiency_percent: float
```

### `PairedComparison`

[synthetic_statistics_contract.py:47–54](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L47-L54)

Declared fields / enum values:

```python
line: int
seeds: int
mean_paired_difference: float
bootstrap_ci95_lower: float
bootstrap_ci95_upper: float
positive_seed_fraction: float
```

### `AuditCounts`

[synthetic_statistics_contract.py:57–62](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L57-L62)

Declared fields / enum values:

```python
metric_rows: int
seeds: int
policies: int
comparisons: int
```

### `verify_synthetic_statistics_contract`

[synthetic_statistics_contract.py:563–567](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L563-L567)

```python
verify_synthetic_statistics_contract(manifest_path: Path) -> list[str]
```

Return synthetic statistics errors; empty means a valid bundle.

### `build_parser`

[synthetic_statistics_contract.py:570–573](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L570-L573)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[synthetic_statistics_contract.py:576–592](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L576-L592)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.


## `historical_forecast_contract.py`

### `ForecastRow`

[historical_forecast_contract.py:23–34](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L23-L34)

Declared fields / enum values:

```python
line: int
case: str
method: str
available: datetime
protocol: str
delivery: datetime
lead: int
forecast: float
realized: float
error: float
```

### `ForecastSummary`

[historical_forecast_contract.py:37–43](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L37-L43)

Declared fields / enum values:

```python
line: int
observations: int
mean_error: float
mean_absolute_error: float
root_mean_squared_error: float
```

### `AuditCounts`

[historical_forecast_contract.py:46–51](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L46-L51)

Declared fields / enum values:

```python
rows: int = 0
cases: int = 0
methods: int = 0
blocks: int = 0
```

### `verify_historical_forecast_contract`

[historical_forecast_contract.py:529–533](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L529-L533)

```python
verify_historical_forecast_contract(manifest_path: Path) -> list[str]
```

Return historical forecast contract errors; empty means a valid bundle.

### `build_parser`

[historical_forecast_contract.py:536–539](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L536-L539)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[historical_forecast_contract.py:542–557](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/historical_forecast_contract.py#L542-L557)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.


## `result_bundle_audit.py`

### `AuditCheck`

[result_bundle_audit.py:32–49](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L32-L49)

Outcome from one independently runnable bundle verifier.

Declared fields / enum values:

```python
name: str
status: CheckStatus
errors: tuple[str, ...] = ()
detail: str | None = None
```

#### `AuditCheck.as_dict`

[result_bundle_audit.py:41–49](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L41-L49)

```python
AuditCheck.as_dict(self) -> dict[str, object]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `BundleAudit`

[result_bundle_audit.py:52–70](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L52-L70)

Aggregate result from all checks that apply to a result bundle.

Declared fields / enum values:

```python
manifest: str
source_root: str
checks: tuple[AuditCheck, ...]
```

#### `BundleAudit.passed`

[result_bundle_audit.py:60–62](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L60-L62)

```python
@property
BundleAudit.passed(self) -> bool
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

#### `BundleAudit.as_dict`

[result_bundle_audit.py:64–70](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L64-L70)

```python
BundleAudit.as_dict(self) -> dict[str, object]
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `audit_result_bundle`

[result_bundle_audit.py:105–160](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L105-L160)

```python
audit_result_bundle(manifest_path: Path, source_root: Path | None=None) -> BundleAudit
```

Run semantic, artifact, source, and optional historical checks.

### `build_parser`

[result_bundle_audit.py:163–177](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L163-L177)

```python
build_parser() -> argparse.ArgumentParser
```

Source-defined interface; use the linked implementation and the main contract page for behavior.

### `main`

[result_bundle_audit.py:196–220](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L196-L220)

```python
main(argv: Sequence[str] | None=None) -> int
```

Source-defined interface; use the linked implementation and the main contract page for behavior.
