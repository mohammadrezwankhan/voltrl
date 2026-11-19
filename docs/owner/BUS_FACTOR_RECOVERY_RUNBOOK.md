# Recovery and continuity runbook

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

A successful recovery means another authorized maintainer can identify the right code/data, run the applicable audits, explain the claim limits and restore publication through normal gates. It does not require inventing a new experiment or weakening the signature policy.

## Recover the scientific record

1. Obtain a full repository clone from the approved origin or a verified mirror. Check source SHA and complete tree; preserve release/tag objects and the older generating commits recorded by the manifests.
2. Create an isolated Python 3.12 environment and install the exact current requirements for current tests. Retain the historical manifests' runtime records separately; current pins are not the archived environment.
3. Run the 80-test suite and both aggregate bundle audits. Revision 1's historical skip is expected; revision 2 needs all five checks. Stop and diagnose any missing object, file or digest mismatch.
4. For a fresh historical reproduction, obtain the original OPSD versioned file, give it the required basename and pass `input_provenance.py`. Store input access and licensing information in an authorized location. Raw data is not in Git.
5. Run a new experiment into a fresh output directory, capture configuration/source/runtime provenance and audit it. Compare protocols before comparing profit values.

[README.md:179–205](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/README.md#L179-L205) [data/opsd_source.json:1–8](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/data/opsd_source.json#L1-L8) [result_bundle_audit.py:75–162](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/result_bundle_audit.py#L75-L162)

## Recover documentation publication

Regenerate `docs/reference/index.html` from canonical Markdown/CFF, run `--check`, validate links and inspect the static view. Open the teaching lab separately to ensure navigation still works. Preserve lesson JSON/source identities and archived animations. Then use a signed documentation commit, the repository's required reviews/checks and an expected-head merge. Trace the main-branch Pages run to the merged revision and confirm the changed live handbook. [.github/workflows/deploy-dashboard.yml:26–82](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/deploy-dashboard.yml#L26-L82)

## What must be retained outside ordinary working files

| Material | Why it matters | Recovery evidence |
| --- | --- | --- |
| Full Git history and release refs | Historical clean provenance reads old blobs | Both bundle software checks pass |
| Original versioned OPSD input | Needed for new historical experiments | Required basename and raw SHA match |
| Exact candidate/QA/delivery receipts | Establish what was reviewed and merged | Fingerprint-to-commit-to-deployment chain |
| Publication assets listed by MANIFEST | Manuscript/template/response/ZIP are absent in this tree | Independently obtained bytes, checksums and actual build/render receipts |
| Authorized owner/access recovery procedure | Access policy is external to repository content | Owner-confirmed recovery drill; no credential material in Git |

[software_provenance.py:163–252](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/software_provenance.py#L163-L252) [MANIFEST.md:5–9](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/MANIFEST.md#L5-L9) [MANIFEST.md:51–57](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/MANIFEST.md#L51-L57)

## Proposed continuity drill

Assign a backup maintainer, restore a full clone into an isolated directory, reproduce the local checks without help from the original author, and have them explain: current vs recorded source, skipped vs passed audit, synthetic vs historical vs browser units, and the missing raw-data/publication-assets boundaries. Record failed steps and owners. Proposed acceptance: all applicable audits pass, no undocumented access dependency remains, and the new maintainer can regenerate the handbook. No backup person or completed drill is claimed by this snapshot.
