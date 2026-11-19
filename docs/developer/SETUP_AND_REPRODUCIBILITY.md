# Setup and reproducibility

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

Use a full Git clone with Python 3.12 and the pinned requirements. Historical bundle audits read old Git objects; a ZIP or shallow clone can lack them even when all visible files are present. [README.md:157–188](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/README.md#L157-L188) [.github/workflows/python-validation.yml:37–60](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/python-validation.yml#L37-L60)

## Isolated checkout

```bash
git clone https://github.com/mohammadrezwankhan/voltrl.git
cd voltrl
git switch --detach 8058e89e4d3516825a400fe86ac45d2e36b6bef0
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python result_bundle_audit.py results_revision/experiment_manifest.json --json
python result_bundle_audit.py results_revision2/experiment_manifest.json --json
```

On PowerShell activate with `.venv\Scripts\Activate.ps1`; use the README's PowerShell line continuations or keep commands on one line. No credentials or environment secret is required for native local calculations. Repository access and later publication authorization are separate.

Expected audit outcomes: revision 1 has four passing checks and one explicit historical-forecast skip; revision 2 has five passing checks. A skip is not a historical protocol test. The 2026-11-19 review observed these outcomes plus 80 passing tests on the pinned implementation. Its environment was Python 3.12.14/Linux with all eight exact requirements installed in an isolated venv inheriting system packages; that is not a minimal-environment certification. [Toolchain details](../maintainer/TOOLCHAIN_AND_DEPENDENCY_MATRIX.md).

## First native run without external data

```bash
python voltrl.py --help
python voltrl.py --synthetic-hours 1000 --seed 7 --bins 4 --output-dir ../voltrl-smoke
```

Use a new output directory: the CLI writes named files and can replace earlier files. This is the **legacy stationary-MDP demonstration** with ideal efficiency/no aging defaults, not the current revision-2 research specification. Expected split is 700/300 hours, six SOC levels and four price bins. See [worked examples](WORKED_EXAMPLES_AND_LABS.md) for the observed solver and accounting results. [voltrl.py:1001–1168](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1001-L1168)

## Historical reproduction requires the exact external input

Download `time_series_60min_singleindex.csv` from the [official OPSD 2020-10-06 package](https://data.open-power-system-data.org/time_series/2020-10-06/), save the bytes under the required local name below, and verify them. Do not edit the source record to make a different dataset pass.

```bash
python input_provenance.py data/opsd_time_series_60min_singleindex_2020-10-06.csv
python voltrl_benchmark.py --opsd-csv data/opsd_time_series_60min_singleindex_2020-10-06.csv --output-dir ../voltrl-reproduction --synthetic-seeds 30 --synthetic-hours 17520 --candidates 4,6,8,10,12,16,20,24,32,40,48
python result_bundle_audit.py ../voltrl-reproduction/experiment_manifest.json --source-root . --json
```

The expected raw SHA-256 is `6a7f2bc571314cbf9c321cc03437691cd4be95c3a6f075e60ff99e8035c704c8`. Filename and digest are both enforced before data parsing. The original CSV is not in the pinned tree and was not downloaded in this documentation review; the full 30-seed/historical command above is source-supported guidance, **not an executed reproduction claim**. [data/opsd_source.json:1–8](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/data/opsd_source.json#L1-L8) [input_provenance.py:56–86](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L56-L86) [voltrl_benchmark.py:1666–1701](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1666-L1701)

When auditing a fresh bundle outside the repository, `--source-root .` matters: the aggregate default is inferred from the manifest's parent directories. Never run any verifier's `--write` option to conceal a changed artifact. Those options record a new inventory/provenance snapshot and require deliberate review. [result_bundle_audit.py:105–119](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L105-L119) [artifact_integrity.py:193–228](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/artifact_integrity.py#L193-L228) [software_provenance.py:255–298](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L255-L298)

## Static documentation and teaching pages

Open `docs/index.html` locally for the teaching lab. Serve the site at a local origin to inspect navigation consistently:

```bash
python -m http.server 8000 --directory docs
```

Open `/reference/` for the handbook, `/portfolio/` for six learning paths and `/native-lessons.html` for the preserved source catalog. Rendering the handbook requires Pandoc in addition to Python; runtime scientific requirements remain unchanged:

```bash
python docs/reference/build_reference.py
python docs/reference/build_reference.py --check
python scripts/portfolio/validate_guide.py
```

The static guide works without JavaScript. Native tests and the browser proxy are distinct checks; neither establishes a deployment receipt.
