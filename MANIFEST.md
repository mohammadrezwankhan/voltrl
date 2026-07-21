<!-- markdownlint-disable MD013 -->

# VoltRL revision 2 submission manifest

## Publication deliverables

- `VoltRL_IntechOpen_Article/VoltRL_IntechOpen_Manuscript_Revision2.docx` — IntechOpen-formatted ACRT manuscript generated from the preserved reference template.
- `VoltRL_IntechOpen_Article/Response_to_Reviewers_Revision2.md` — point-by-point response to both Grade A reviews.
- `Project_VoltRL_Submission_Revision2.zip` — submission and reproducibility archive.

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

The 124 MB OPSD source CSV is not duplicated in the public repository or final archive. Its official version, DOI `10.25832/time_series/2020-10-06`, local SHA-256, and reproduction instructions are recorded under `data/`.

## Manuscript build and QA

- `VoltRL_IntechOpen_Article/reference_template.docx` — preserved IntechOpen template; SHA-256 `6F8338130EDBF52CFA73EB2264015465E75FBEA7488F1C643D0A5302A4D489E3`.
- `VoltRL_IntechOpen_Article/build_voltrl_manuscript_revised.py` — deterministic revision-2 DOCX builder.
- `VoltRL_IntechOpen_Article/validate_revised_manuscript.py` — abstract, keywords, headings, citations, references, captions, declarations, metadata, alt-text, and placeholder audit.
- `VoltRL_IntechOpen_Article/.qa/revision2_compliance_report.json` — machine-readable compliance result.
- `VoltRL_IntechOpen_Article/.qa/word_render_revision2/` — Microsoft Word render and page images used for full visual inspection.

## Public record

Repository: <https://github.com/mohammadrezwankhan/voltrl>

Revision 2 is released as `v1.1.0`; the exact commit is recorded in the final manuscript, reviewer response, and archive after publication of the synchronized artifacts.
