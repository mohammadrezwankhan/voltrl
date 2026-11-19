# VoltRL source and evidence handbook

[Handbook](INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

VoltRL compares **finite-state battery-arbitrage policies**. Start with the native MWh model when reproducing research; use the browser's USD/basis-point exercise to learn about separating an opportunity from its costs. The browser does not run the Python benchmark or load OPSD prices. [voltrl.py:52–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L52-L194) [voltrl_benchmark.py:1666–1835](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1666-L1835) [docs/index.html:296–299](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L296-L299)

This handbook reviews immutable source `8058e89e4d3516825a400fe86ac45d2e36b6bef0`. It adds developer, scientific, maintainer and owner guidance. Existing result bundles, release metadata, original README, license and teaching pages retain their own provenance. The [reading view](reference/index.html) is generated from these Markdown files and the existing citation file; [maintenance instructions](maintainer/DOCS_MAINTENANCE_RUNBOOK.md) explain regeneration.

## Choose a route

| Need | Read or run |
| --- | --- |
| Understand the native system | [Architecture](developer/ARCHITECTURE.md), [equations](math-and-physics/EQUATIONS_AND_DERIVATIONS.md), [parameters and units](math-and-physics/PARAMETERS_AND_SYMBOLS.md) |
| Reproduce a bounded example | [Setup](developer/SETUP_AND_REPRODUCIBILITY.md), [worked examples](developer/WORKED_EXAMPLES_AND_LABS.md), [troubleshooting](developer/TROUBLESHOOTING.md) |
| Call a module or inspect output | [API and CLI contracts](developer/API_CLI_AND_INTERFACES.md), [declaration catalog](developer/API_REFERENCE.md) |
| Interpret a claim | [Assumptions and limits](math-and-physics/ASSUMPTIONS_AND_LIMITS.md), [verification evidence](maintainer/VERIFICATION_EVIDENCE_LEDGER.md), [source accounting](SOURCE_EVIDENCE.md) |
| Maintain or publish | [CI and release playbook](maintainer/CI_CD_AND_RELEASE_PLAYBOOK.md), [toolchain](maintainer/TOOLCHAIN_AND_DEPENDENCY_MATRIX.md), [debt](maintainer/FAILURE_MODES_AND_TECH_DEBT.md), [docs runbook](maintainer/DOCS_MAINTENANCE_RUNBOOK.md) |
| Own or recover the project | [Scope and governance](owner/GOVERNANCE_AND_SCOPE.md), [recovery](owner/BUS_FACTOR_RECOVERY_RUNBOOK.md), [portfolio boundary](owner/PORTFOLIO_INTEGRATION.md), [decision index](owner/ADR/ADR-0000-INDEX.md) |
| Plan work | [Twelve-month roadmap](../ROADMAP.md), [changelog](../CHANGELOG.md), [contributing](../CONTRIBUTING.md), [security](../SECURITY.md), [citation](../CITATION.cff) |
| Learn in the browser | [Interactive lab](index.html), [browser model contract](developer/BROWSER_MODEL_CATALOG.md), [native lesson catalog](native-lessons.html), [six source-linked paths](portfolio/index.html), [earlier animations](animations/index.html) |

## Four evidence boundaries

1. **Legacy demonstration:** `voltrl.py` solves a discounted stationary MDP, defaulting to ideal efficiency and no aging; its automatic BIC-like selector remains legacy. It is useful for solver mechanics. [voltrl.py:310–370](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L310-L370) [voltrl.py:1001–1203](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L1001-L1203)
2. **Current benchmark:** `voltrl_benchmark.py` uses training-only expanding-window selection, finite-horizon policies, nonlinear aging and separate synthetic sequential and historical 24-hour block protocols. [voltrl_benchmark.py:261–397](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L261-L397) [voltrl_benchmark.py:712–811](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L712-L811)
3. **Committed evidence:** `results_revision/` and `results_revision2/` record older generating commits. A successful audit validates the applicable stored contracts; it does not regenerate those experiments. [software_provenance.py:163–252](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L163-L252) [result_bundle_audit.py:75–162](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L75-L162)
4. **Teaching UI:** the active browser mode is a synthetic spread screen. Its eight checkpoints test its declared arithmetic; they are independent of native policy performance. [docs/index.html:159–166](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L159-L166) [docs/index.html:296–345](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/docs/index.html#L296-L345)

Local review executed 80 existing unit tests, both aggregate audits, the six-path guide validator, a 1,000-hour legacy smoke run, a 2,400-hour fixed-bin native example and the eight browser market checkpoints. These results are dated local evidence. Candidate GitHub checks, guarded merge and live deployment require later receipts.
