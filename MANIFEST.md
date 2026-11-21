<!-- markdownlint-disable MD013 -->

# VoltRL revision 2 submission manifest

## Public availability

This repository contains the benchmark code, documentation and archived results.
The IntechOpen manuscript, reviewer response, template, build and QA files, and
submission ZIP are absent from this tree and the public release assets.

## Scientific implementation

- `voltrl.py` — finite battery model, nonlinear DOD/SOC aging cost, solvers, simulation, and perfect-foresight diagnostic.
- `voltrl_benchmark.py` — synthetic state ablation, expanded training-only resolution selection, SARX forecasting, historical 24-hour block scheduling, uncertainty, sensitivity, and figures.
- `artifact_integrity.py` — records and verifies byte sizes and SHA-256 digests
  for every declared result artifact, with cross-platform LF canonicalization
  for CSV tables and byte-exact checks for figures.
- `experiment_contract.py` — checks manifest physics and study configuration
  against seed, policy, candidate/fold, selected-bin, split, and sample-count
  coverage in the published result tables.
- `synthetic_statistics_contract.py` — recomputes policy summaries, paired
  contrasts, oracle-efficiency means, and row-level annualization from the
  published synthetic seed metrics.
- `software_provenance.py` — binds each result manifest to a clean historical
  Git commit or the exact bytes of an uncommitted source snapshot.
- `result_bundle_audit.py` — runs every verifier applicable to a result bundle
  and emits either a readable check summary or structured JSON.
- `tests/` — deterministic tests covering forecast causality, same-day block
  commitment, artifact and source tampering, historical commit verification,
  aggregate audit reporting, synthetic statistics drift, path safety, nonlinear
  full-cycle normalization, SOC feasibility, and oracle dominance.
- `requirements.txt`, `LICENSE`, `CITATION.cff`, and `README.md` — pinned environment, license, citation metadata, and reproduction instructions.

## Results

`results_revision2/` contains:

- 30-seed synthetic policy metrics, summaries, and paired bootstrap contrasts;
- complete model-selection folds and case diagnostics;
- DK1/DK2 block-schedule metrics and data-quality disclosure;
- day-ahead forecast-detail and forecast-summary tables;
- physical, planner-discount, and degradation-model sensitivities;
- solver diagnostics and an artifact- and source-verifiable
  `experiment_manifest.json`;
- mandatory OPSD input verification using `input_provenance.py` and the
  machine-readable `data/opsd_source.json` record;
- six result figures in PNG and PDF, with both formats declared in the manifest.

The public repository does not redistribute the 124 MB OPSD source CSV. Its
official version, DOI `10.25832/time_series/2020-10-06`, SHA-256 digest, and
reproduction instructions are recorded in [the data guide](data/README.md).

## Public record

Repository: <https://github.com/mohammadrezwankhan/voltrl>

The software and results are tagged [v1.1.0](https://github.com/mohammadrezwankhan/voltrl/releases/tag/v1.1.0).
The archived experiment manifest records the source commit used to generate the results.
