# CI, release and publication playbook

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

The source configures GitHub Actions and a static GitHub Pages deployment. There is no CircleCI or Buildkite configuration in the pinned tree. A missing optional provider connector is therefore not a Voltrl validation failure. Preserve current workflow behavior and use repository-configured checks. [.github/workflows/python-validation.yml:1–60](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/python-validation.yml#L1-L60) [.github/workflows/deploy-dashboard.yml:1–82](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/deploy-dashboard.yml#L1-L82)

## Actual workflow coverage

| Workflow | Triggers at this source | Work and material limits |
| --- | --- | --- |
| `no-codex-attribution.yml` | PR, merge group, main push and all tag pushes | `human-authorship-policy`; scans event-specific commit ranges for metadata policy, not documentation meaning |
| `python-validation.yml` | Manual; PR and main push with Python, `.gitattributes`, data JSON, results, requirements or workflow paths | Python 3.12, pinned requirements, full Git history, all unit tests and both bundle audits; no fresh external-data reproduction |
| `markdown-maintenance.yml` | Manual; PR/main push for Markdown, CFF or its own file | Lychee checks only README.md, MANIFEST.md and data/README.md; added handbook links are not included |
| `portfolio-dashboard-check.yml` | PR and push with guide/asset/validator/workflow paths; no branch filter and no manual trigger | Validates six-path config, paths and SVG; tag pushes are not path-filtered by GitHub |
| `deploy-dashboard.yml` | Main push changing docs/assets/self; manual | Static validation, then main-only Pages deployment of `docs/`; not a PR preview |

[.github/workflows/no-codex-attribution.yml:1–99](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/no-codex-attribution.yml#L1-L99) [.github/workflows/python-validation.yml:1–60](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/python-validation.yml#L1-L60) [.github/workflows/markdown-maintenance.yml:1–37](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/markdown-maintenance.yml#L1-L37) [.github/workflows/portfolio-dashboard-check.yml:1–22](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/portfolio-dashboard-check.yml#L1-L22) [.github/workflows/deploy-dashboard.yml:1–82](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/deploy-dashboard.yml#L1-L82). GitHub documents that [path filters are not evaluated for tag pushes](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onpushpull_requestpull_request_targetpathspaths-ignore).

A new `.py` documentation renderer matches the Python validation paths. The current workflows do not execute the renderer's freshness check or a comprehensive handbook link check; run these locally and record the gap for a separately reviewed CI change. Preserve job names and gates when evaluating future CI economics. AGENTS.md requests measured savings, pinned actions and retention of required coverage. [AGENTS.md:1–3](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/AGENTS.md#L1-L3)

## Observed protection, not assumed policy

On 2026-11-19, ruleset [20091523](https://github.com/mohammadrezwankhan/voltrl/rules/20091523) was active on all branches, with `required_signatures`, no bypass actors and `current_user_can_bypass=never`. Branch metadata marked main protected. The classic protection endpoint returned HTTP 403 to the integration; that leaves its required reviews/checks unknown. Rulesets and classic protection are separate sources of requirements. A permissions summary or historical green check cannot fill that gap.

Before delivery, read the complete applicable rules in an authorized supported surface, refresh the base/head and inspect the exact candidate diff. Use a legitimately verified commit route permitted by the signature rule. Do not change policy, disable checks, forge an identity or treat an unsigned API commit as verified. Current metadata policy and attribution must also be honored.

## Ordinary guarded delivery

1. Create an isolated documentation branch from the intended base and stage only the reviewed documentation/navigation/renderer files. Preserve application, workflow, dependency, result and license bytes.
2. Bind independent QA to the complete candidate tree. After committing, bind that same reviewed tree to the actual signed commit SHA; re-review any changed content.
3. Open the scoped PR and observe checks on its current head or the correct tested merge revision. Capture provider, conclusion, revision linkage and required-policy source. Resolve reviews/conversations and use any required merge queue normally.
4. Re-fetch head/base/rules immediately before merge. Use an expected-head guard; do not allow a changed PR head to inherit approval for an earlier tree.
5. Record merged SHA and deployment identity separately. A PR page or pending/neutral/skipped check is not a passed required gate.

## Release records and a new research release

Read-only metadata found existing [v1.0.0](https://github.com/mohammadrezwankhan/voltrl/releases/tag/v1.0.0) and [v1.1.0](https://github.com/mohammadrezwankhan/voltrl/releases/tag/v1.1.0), both published 2026-07-16. Their annotated tags point to `2e01d9f…` and `70fa960…` respectively. Existing CFF declares software v1.1.0/date 2026-07-16; this documentation change does not create a version, DOI, release or manuscript publication. [CITATION.cff:1–13](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/CITATION.cff#L1-L13)

For a future research release, rerun the declared data/protocol, capture actual source/runtime provenance, audit all outputs, review changed scientific conclusions, reconcile CFF/codemeta/release notes and verify downloadable release assets. `MANIFEST.md` lists manuscript, reference-template, response and ZIP paths absent from the pinned tree; obtain and verify them separately before claiming a complete submission archive. [MANIFEST.md:5–9](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/MANIFEST.md#L5-L9) [MANIFEST.md:51–63](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/MANIFEST.md#L51-L63)

## Pages verification

The existing workflow uploads all of `docs/`, then deploys with Pages/id-token permissions on main. It preserves deployment concurrency (`cancel-in-progress: false`). A successful source-era deployment does not prove the new handbook is live. [.github/workflows/deploy-dashboard.yml:18–82](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/deploy-dashboard.yml#L18-L82)

After merge, identify the deployment run's source commit, environment and reported URL. Open the actual `/voltrl/reference/` route, confirm the dated source snapshot and a changed chapter, and check navigation from the existing lab. Verify the deployment corresponds to the merged candidate. Record `AWAITING_DEPLOYMENT` or a concrete failure if it does not; do not mark publication from HTTP success alone.
