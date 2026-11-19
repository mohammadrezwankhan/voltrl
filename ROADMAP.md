# Twelve-calendar-month development roadmap

[Handbook](docs/INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

All items below are proposals, not staffed commitments or changes implemented by this documentation package. Window: **2026-11-19 through 2027-11-18 inclusive** (end-exclusive 2027-11-19). Now covers the remaining part of Q4 2026; Next is Q1 2027; Later is Q2 2027; Horizon spans Q3 and the first 49 days of Q4 2027. Effort means person-days of focused work, not calendar duration.

The current package clarifies source behavior and adds navigation. Algorithm, workflow, dependency and scientific-policy changes below require separate owner review. Shared documentation/audit design can be coordinated across the portfolio, but no cross-repository runtime dependency is implemented. Critical scientific sequence: VR-01 → VR-02 → VR-09, with VR-04 and VR-07 evidence/recovery prerequisites.

## Now

### VR-01 — Make historical information availability and preprocessing independently reviewable.

**Engineering improvement · P1 · Proposed 2026-11-19–2026-12-31.**

Write an explicit delivery/publication/decision timeline; assess interpolation before splitting and define an auditable alternative protocol before operational claims.

**Evidence:** [voltrl_benchmark.py:712–811](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L712-L811) [voltrl_benchmark.py:1083–1118](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1083-L1118)

**Owner role:** Scientific maintainer with data steward. **Dependencies:** None. **Effort:** 3–6 person-days. **Confidence:** Medium.

**Risks:** An actual market gate may invalidate the current prior-delivery-hour abstraction. **Unresolved assumptions:** Relevant official publication timing and raw input remain obtainable.

**Acceptance criteria:**

- Every forecast input has a documented availability time and cited timing source.
- At least one boundary-day fixture demonstrates information cutoff and disclosed imputation behavior.
- Existing stored bundles remain interpretable under their original protocol.

**Verification:** Independent protocol review plus causal dependency and boundary-data tests in a separate implementation change.

### VR-03 — Custom runs report their actual seeds rather than default labels.

**Defect · P1 · Proposed 2026-11-19–2026-12-31.**

Derive sensitivity case labels and figure seed counts from configuration; audit all displayed run labels.

**Evidence:** [voltrl_benchmark.py:1289–1400](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1289-L1400) [voltrl_benchmark.py:1485–1495](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1485-L1495) [voltrl_benchmark.py:1724–1748](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1724-L1748)

**Owner role:** Python maintainer. **Dependencies:** None. **Effort:** 1–2 person-days. **Confidence:** High.

**Risks:** Renaming case keys may affect downstream table consumers. **Unresolved assumptions:** A compatibility policy for legacy artifact labels is agreed.

**Acceptance criteria:**

- Nondefault sensitivity seed and synthetic seed count appear correctly in every affected table/figure label.
- Default-run scientific values remain unchanged.

**Verification:** Regression tests with nondefault arguments and a reviewed default-result comparison.

### VR-05 — Keep the entire canonical handbook and its reading view verifiable.

**Documentation · P2 · Proposed 2026-11-19–2026-12-31.**

Add comprehensive local-link/source-locator and renderer-freshness checks to scoped documentation CI after measuring runtime.

**Evidence:** [.github/workflows/markdown-maintenance.yml:24–37](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/markdown-maintenance.yml#L24-L37) [scripts/portfolio/validate_guide.py:1–33](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/scripts/portfolio/validate_guide.py#L1-L33) [AGENTS.md:1–3](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/AGENTS.md#L1-L3)

**Owner role:** Documentation and CI maintainer. **Dependencies:** None. **Effort:** 2–4 person-days. **Confidence:** High.

**Risks:** Overbroad path filters may duplicate expensive validation or leave required checks pending. **Unresolved assumptions:** Pandoc can be pinned/provisioned in the docs-only job without runtime dependency changes.

**Acceptance criteria:**

- A broken new-chapter link and stale generated handbook fail the intended job.
- Required existing check names, branch coverage and deployment guards remain intact.
- Measured job cost and trigger matrix are recorded.

**Verification:** Positive/negative docs fixtures and event/path trigger review; compare actual run duration before claiming savings.


## Next

### VR-02 — Remove ambiguity between internal SOC power and converter-side ratings.

**Engineering improvement · P1 · Proposed 2027-01-01–2027-03-31.**

Compare the current fixed internal-energy step with an explicit AC import/export limit model; define a new protocol only after assessing state/action changes.

**Evidence:** [voltrl.py:105–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L105-L194)

**Owner role:** Battery-model maintainer. **Dependencies:** VR-01. **Effort:** 4–8 person-days. **Confidence:** Medium.

**Risks:** New feasible actions can change profits and invalidate direct historical comparisons. **Unresolved assumptions:** A proposed physical power convention is selected and documented.

**Acceptance criteria:**

- Energy conservation and efficiency units hold for charge/discharge fixtures.
- No AC limit is exceeded in the proposed model.
- Old and proposed model results are labeled separately with matching oracle constraints.

**Verification:** Analytical energy fixtures, feasibility tests and controlled sensitivity comparison; owner scientific sign-off.

### VR-04 — Match audit claims to selected-K, uncertainty and complete source evidence.

**Engineering improvement · P1 · Proposed 2027-01-01–2027-03-31.**

Add explicit selected-K/minimum checks, reproducible bootstrap endpoint checks and a declared source-closure inventory without rewriting old provenance.

**Evidence:** [experiment_contract.py:306–487](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/experiment_contract.py#L306-L487) [synthetic_statistics_contract.py:348–501](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/synthetic_statistics_contract.py#L348-L501) [software_provenance.py:14–18](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L14-L18)

**Owner role:** Verification maintainer. **Dependencies:** VR-03. **Effort:** 5–9 person-days. **Confidence:** Medium.

**Risks:** Historical RNG/version behavior and expanded source scope need backward compatibility. **Unresolved assumptions:** Resampling seeds and historical source objects are sufficient for targeted checks.

**Acceptance criteria:**

- Tampered selected K and bootstrap endpoints produce specific failures.
- All included source files have canonical path/hash records and declared scope.
- Both old bundles still produce accurately labeled compatible audit outcomes.

**Verification:** Adversarial fixture tests plus old-bundle regression, with independent claim-by-claim audit review.

### VR-06 — Remove observed timestamp-accessor deprecations before a future pandas upgrade.

**Maintenance · P2 · Proposed 2027-01-01–2027-03-31.**

Use supported timestamp property names and exercise seasonal-feature parity with the pinned environment.

**Evidence:** [voltrl_benchmark.py:517–531](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L517-L531) [requirements.txt:1–8](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/requirements.txt#L1-L8)

**Owner role:** Python maintainer. **Dependencies:** None. **Effort:** 1–3 person-days. **Confidence:** High.

**Risks:** A later dependency version may change numerical or time-zone behavior beyond renamed properties. **Unresolved assumptions:** Only accessor changes are needed in the first maintenance patch.

**Acceptance criteria:**

- Current deprecation warnings disappear.
- Seasonal feature arrays and existing causal/solver tests remain equivalent.
- Both historical bundle audits still pass their applicable checks.

**Verification:** Warning-as-error targeted tests, numerical feature comparison and full existing suite.


## Later

### VR-07 — Make publication assets and recovery responsibilities recoverable.

**Maintenance · P2 · Proposed 2027-04-01–2027-06-30.**

Locate source-listed manuscript/template/response/archive materials, record availability and hashes, and assign a backup recovery drill.

**Evidence:** [MANIFEST.md:5–9](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/MANIFEST.md#L5-L9) [MANIFEST.md:51–63](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/MANIFEST.md#L51-L63) [CITATION.cff:1–13](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/CITATION.cff#L1-L13)

**Owner role:** Repository owner and release maintainer. **Dependencies:** VR-04, VR-05. **Effort:** 3–6 person-days. **Confidence:** Medium.

**Risks:** Referenced assets may be unavailable or subject to separate publication terms. **Unresolved assumptions:** Owner can identify authoritative copies and an authorized backup maintainer.

**Acceptance criteria:**

- Every listed deliverable is verified available or explicitly marked unavailable with reason.
- A second authorized maintainer restores history and passes applicable audits.
- Release/citation/asset records agree without invented DOI or publication status.

**Verification:** Recovery drill, artifact inventory and independent publication-record reconciliation.

### VR-08 — Help learners transfer from synthetic browser arithmetic to native benchmark evidence.

**Documentation · P3 · Proposed 2027-04-01–2027-06-30.**

Review dated teaching links and add source-specific learning exercises that use the handbook and native CLI while preserving historical provenance.

**Evidence:** [docs/portfolio/README.md:5–29](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/portfolio/README.md#L5-L29) [docs/index.html:296–299](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L296-L299) [docs/index.html:469–482](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L469-L482)

**Owner role:** Documentation maintainer. **Dependencies:** VR-05. **Effort:** 2–5 person-days. **Confidence:** High.

**Risks:** A visual shortcut could imply native execution or measured performance. **Unresolved assumptions:** Native demonstrations can remain small and deterministic.

**Acceptance criteria:**

- Each learning exercise names its units, source revision and whether it executes native code.
- Keyboard, narrow-screen and reduced-motion checks are recorded for any changed interaction.
- No historical source identity is silently replaced.

**Verification:** Independent content review, actual browser user-flow checks and reproducible small native examples.


## Horizon

### VR-09 — Determine whether a separately defined study can support more realistic battery/market claims.

**Exploratory research · P3 · Proposed 2027-07-01–2027-11-18.**

Design an external measured-data, physical-constraint and information-timing validation study with preregistered comparison objectives and explicit null results.

**Evidence:** [README.md:270–278](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/README.md#L270-L278) [voltrl.py:113–165](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L113-L165) [voltrl_benchmark.py:982–1118](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L982-L1118)

**Owner role:** Scientific owner with domain/data reviewers. **Dependencies:** VR-01, VR-02, VR-04, VR-07. **Effort:** 10–20 person-days for study design and pilot, not full certification. **Confidence:** Low.

**Risks:** Data access, calibrated degradation parameters and genuine market timing may remain unresolved. **Unresolved assumptions:** Suitable lawful measured data and independent domain review become available.

**Acceptance criteria:**

- Protocol states measurable validation targets before fitting/evaluation.
- Synthetic, historical and measured evidence are kept distinct.
- Pilot reports failures, uncertainty and scope limits; no deployment claim without corresponding evidence.

**Verification:** Independent protocol review and a separately versioned pilot with held-out measured evidence and repeatable checks.
