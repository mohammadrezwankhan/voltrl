# Toolchain and dependency matrix

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

Distinguish the current declared environment, the environment recorded in archived experiments and the environment actually used for documentation checks. All current requirement and workflow bytes are preserved. [requirements.txt:1–8](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/requirements.txt#L1-L8)

| Component | Source declaration / archived record | Review observation and purpose |
| --- | --- | --- |
| Python | README recommends 3.12; Python workflow requests 3.12 | 3.12.14 on Linux; existing native tests and examples executed |
| NumPy | Current 2.5.4; archived manifests 2.5.1 | 2.5.4 installed; arrays, linear solves, random generators |
| pandas | Current 3.1.1; archived 3.0.1 | 3.1.1 installed; hourly frames, CSV, aggregations |
| Matplotlib | Current 3.11.2; archived 3.11.0 | 3.11.2 installed; Agg figure generation |
| python-docx | 1.2.0 | Exact requirement installed; manuscript builder is absent from tree, so no DOCX build was claimed |
| latex2mathml | 3.81.1 | Exact requirement installed; not needed by the native solver example |
| lxml | 6.1.3 | Exact requirement installed; no complete XML toolchain qualification |
| Pillow | 13.0.0 | Exact requirement installed; no fresh archival figure visual certification |
| PyMuPDF | 2.1 | Exact requirement installed; this alone does not reproduce the source-listed manuscript |
| Git | Full historical objects needed for clean recorded-source audit | Candidate history fetched read-only; both recorded commits resolved |
| Node.js | No Node package/lockfile declared by this repository | Used only as an external review harness for the actual inline browser model |
| Pandoc | Added documentation-maintenance prerequisite, not scientific runtime dependency | 3.1.11.1 used to render canonical Markdown to static HTML/MathML |
| JSON Schema / YAML | No native solver runtime requirement | External review tools validate CFF, static lesson schema and handoffs |
| GitHub Actions / Pages | Pinned action references and explicit job permissions | Current source-head checks observed separately from local tests; candidate delivery pending |

[README.md:157–188](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/README.md#L157-L188) [results_revision2/experiment_manifest.json:1–140](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/results_revision2/experiment_manifest.json#L1-L140) [.github/workflows/python-validation.yml:39–60](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/python-validation.yml#L39-L60).

The author environment used an isolated venv with system packages inherited, then installed the eight exact `requirements.txt` pins. Record the resolved environment for a reproduction; this review does not certify installation into a minimal fresh OS or all transitive dependencies on every platform. The archived Windows runtime and local Linux runtime should not be presented as bitwise equivalent execution environments.

## Updating dependencies

Dependabot declares weekly pip and GitHub Actions updates with five open PRs per ecosystem. Review changes against native tests, both historical bundle audits and applicable documentation checks. Historical provenance should continue to validate the old recorded blobs even when the current requirements change. Do not replace historical source digests with current files. [.github/dependabot.yml:1–12](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/dependabot.yml#L1-L12) [tests/test_software_provenance.py:60–75](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_software_provenance.py#L60-L75)

Pandas deprecation warnings observed in seasonal timestamp features are a maintenance issue to schedule before a future major upgrade. No dependency or implementation change is part of this documentation package. [voltrl_benchmark.py:517–531](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L517-L531)

## Reproducibility record checklist

Retain OS/Python/package versions, source SHA, clean/dirty scope, raw input hash/filename, candidate K values, seeds, physical settings, information protocol, terminal valuation, generated artifact inventory and all verifier outcomes. For a docs-only change also retain renderer version and the canonical-input hashes embedded in the generated page. The local evidence ledger is a review snapshot, not a support contract.
