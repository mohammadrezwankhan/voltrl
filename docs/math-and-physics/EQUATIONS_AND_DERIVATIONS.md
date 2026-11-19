# Implemented equations and derivations

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

This chapter describes the pinned implementation, including the differences between the legacy stationary solver and the benchmark. Prices are currency per MWh; synthetic prices have no measured currency calibration. Historical plots interpret the OPSD price columns as EUR/MWh. The browser's USD/bps screen is documented separately. [voltrl.py:167–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L167-L194) [voltrl_benchmark.py:1481–1516](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1481-L1516)

## 1. Energy grid, feasible actions and market cash

Let capacity be C MWh, internal power step P MW and interval Δt h. The internal energy step is q=PΔt. The code requires C/q to be an integer and uses E in {0,q,…,C}. Actions encode charge=0, idle=1, discharge=2, but their energy changes are +q, 0, −q. An action is feasible only when 0≤E+δ≤C. At default C=500 and q=100, the six states are 0,100,…,500 MWh. [voltrl.py:36–45](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L36-L45) [voltrl.py:52–111](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L52-L111) [voltrl.py:412–481](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L412-L481)

Grid purchase and sale energies are

$$E^{buy}=\frac{\max(\delta,0)}{\eta_c},\qquad E^{sell}=\eta_d\max(-\delta,0).$$

The cash flow is $p(E^{sell}-E^{buy})$; net reward subtracts the modeled degradation/stress cost. Both efficiencies act on grid energy, while the SOC step stays q. Thus a 100 MWh internal charge with ηc=.95 purchases 105.263158 MWh. `max_power_mw` is not a separately enforced 100 MW grid-import cap in this implementation. One charge followed by a discharge transfers the same internal q and returns ηcηd=.9025 of the purchased energy when both efficiencies are .95. [voltrl.py:167–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L167-L194)

## 2. Aging proxy

Legacy linear aging is $D=d|\delta|$. In nonlinear mode, with x=E/C, x′=(E+δ)/C, ν≥1, 0≤α≤1 and stress coefficient s:

$$D=\alpha d|\delta|+2(1-\alpha)dC\,\mathbf{1}_{\delta<0}\max\{(1-x')^\nu-(1-x)^\nu,0\}+s\Delta t\left(\frac{x'-0.5}{0.5}\right)^2.$$

The nonlinear term is an increment of an **absolute-SOC depth potential on discharge**. It has no cycle history, rainflow counting, changing physical capacity or calibrated electrochemical damage state. The quadratic term uses after-action SOC and also charges idle actions away from mid-SOC. The primary specification uses d=5, α=.25, ν=1.6, s=1. [voltrl.py:113–165](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L113-L165) [voltrl_benchmark.py:1671–1682](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1671-L1682)

For a complete 0→C→0 traversal, the linear contribution is 2αdC. Discharge potential increments telescope to 2(1−α)dC. Their sum is 2dC; **SOC stress is additional**, so full-cycle normalization does not imply the all-in cost is exactly 2dC when s>0. The existing normalization test sets the default s=0. [tests/test_voltrl.py:92–118](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_voltrl.py#L92-L118)

At E=200 MWh, idle costs $1((0.4-0.5)/0.5)^2=0.04$ currency/hour. The primary six-point grid omits exactly 250 MWh, so there is no grid point with zero quadratic stress. This explains the stored idle annualization of −350.4 (=−.04×8760). [results_revision2/synthetic_summary.csv:1–7](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/results_revision2/synthetic_summary.csv#L1-L7)

## 3. Price discretization and transition inference

Quantile edges are fitted on training prices only. Edges must remain distinct, with at least 10K training observations; the outer transform bins extend to ±∞. Each bin's representative is its training mean. [voltrl.py:217–266](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L217-L266)

For destination marginal m and transition counts Nij, smoothing is

$$P_{ij}=\frac{N_{ij}+\lambda m_j}{\sum_kN_{ik}+\lambda}.$$

The legacy estimator uses a smoothed marginal of destination observations and λ=1 by default. The benchmark uses its fitted frame's bin marginal, λ=12, and optionally a separate count matrix per current UTC hour h. Smoothing is validated as finite/nonnegative; λ=0 fails when a needed row has no outgoing observations. Price transitions are exogenous to battery actions. [voltrl.py:278–307](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L278-L307) [voltrl_benchmark.py:173–224](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L173-L224)

The benchmark scores the next observed price with a full-support mixture

$$f(p_{t+1}\mid z_t,h_t)=\sum_j P_{h_t,z_t,j}\,\mathcal{N}(p_{t+1};\mu_j,\sigma_j^2).$$

Each σj is at least max(.5,.05×pooled training sample SD). The score is mean negative log density using a log-sum-exp computation. Three expanding training folds use boundaries at 1/2, 2/3, 5/6 and all of the development window. **K minimizes mean hour-aware validation NLL**; the same K is then used for the price-only ablation. The test window never selects K. [voltrl_benchmark.py:158–295](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L158-L295)

The original `select_bin_count_bic` remains in the legacy CLI. Its density uses finite observed bin widths and its penalty is `[K(K−1)+K−1] log(n)`. It is not the benchmark's revised selection method. [voltrl.py:310–370](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L310-L370)

## 4. Stationary and finite-horizon control

The legacy stationary Bellman update is

$$V_{n+1}(s)=\max_{a\in A(s)}\left[R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)V_n(s')\right],\quad0\le\gamma<1.$$

VI starts at zero and stops when max absolute value change is ≤tolerance, subject to the iteration cap. PI starts with idle, evaluates a fixed policy via `(I−γPπ)V=rπ`, and improves it until actions stop changing. The reported Bellman residual is $\|TV-V\|_\infty$. For this discounted finite-state system, the contraction argument bounds value error by residual/(1−γ); small residual is numerical evidence under the model, not physical validation. [voltrl.py:494–588](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L494-L588)

The benchmark instead computes a finite-horizon recurrence, with terminal salvage $V_H(E,z)=v\eta_dE$ and v equal to the training-median price:

$$V_t(E,z)=\max_{a\in A(E)}\left[R(E,\mu_z,a)+\gamma\sum_jP_{h_t,z,j}V_{t+1}(E+\delta(a),j)\right].$$

The primary γ=1 needs no infinite-horizon convergence test; a finite backward loop evaluates each time slice. The observed price determines the current bin when applying the policy. The hour-aware model conditions transitions on UTC hour; the price-only model omits that conditioning. Finite planner ties prefer idle, charge, then discharge; legacy argmax order starts with charge. [voltrl_benchmark.py:72–74](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L72-L74) [voltrl_benchmark.py:311–469](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L311-L469)

The oracle runs backward on the entire actual test-price sequence with the same SOC grid, costs and terminal salvage. It is an upper bound for feasible policies evaluated under that same finite objective, not an implementable policy input. Discounted stationary policies can optimize a different objective from the undiscounted comparison, and the documentation keeps those cases separate. [voltrl.py:648–714](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L648-L714)

## 5. SARX forecasts and the historical block

The fitted regression standardizes prices and uses an intercept, lags 1,2,24,48,168 and sine/cosine pairs for daily, weekly and annual periods. Ridge λ=.001 penalizes all coefficients except the intercept. Forecasts recurse from available history and are clipped to training .001/.999 quantiles extended by 25% of their range. This is a fixed training fit, not online retraining. [voltrl_benchmark.py:517–652](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L517-L652)

Synthetic MPC uses the current observed price plus up to 23 future forecasts, solves a forecast DP, and applies its first action. Historical dispatch forecasts 24 hours from the final available prior-delivery-hour observation, fixes the whole action vector, carries SOC between days, and settles against actual prices afterward. Seasonal-mean and prior-day persistence forecasts are explicit historical baselines. No exchange auction calendar is implemented. [voltrl_benchmark.py:655–811](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L655-L811)

## 6. Metrics and uncertainty

For a trajectory, cash profit is Σr, adjusted profit is $J=\sum_t r_t+v\eta_d(E_H-E_0)$, annualized adjusted profit is $8760J/H$ for H hourly observations, and equivalent full cycles are $\sum_t|\delta_t|/(2C)$. Drawdown uses cumulative cash, not salvage-adjusted wealth. A negative oracle-adjusted profit makes ratio-based interpretation problematic; the main evaluation only computes a percentage when the oracle denominator is positive. [voltrl_benchmark.py:814–851](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L814-L851) [voltrl_benchmark.py:931–960](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L931-L960)

Across synthetic seeds, the implementation reports sample SD, seeded 5,000-resample percentile intervals for the mean, and paired annualized differences. Within a single case it uses a paired seven-day circular moving-block bootstrap of **daily cash differences**; this is a different estimand from annualized inventory-adjusted profit and does not propagate fitted-model uncertainty. The statistical audit recomputes means/SD/pairs and interval sanity but does not replay bootstrap quantiles. [voltrl_benchmark.py:854–883](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L854-L883) [voltrl_benchmark.py:1121–1171](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1121-L1171) [synthetic_statistics_contract.py:348–501](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L348-L501)

There are no PDEs, spatial boundary conditions or numerical time integrators. The boundary problem is discrete SOC feasibility plus initial inventory and terminal value. All native price paths assume hourly observations; using another interval through low-level battery parameters does not automatically generalize the hourly annualization and forecast features.
