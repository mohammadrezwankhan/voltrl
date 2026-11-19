# Security and responsible reporting

[Handbook](docs/INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

VoltRL is a local research benchmark with a static teaching site. The source contains no market credentials, live trading connector or production device controller. Input files, output directories, Git provenance and scientific claims still deserve careful handling. [README.md:270–278](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/README.md#L270-L278) [input_provenance.py:56–86](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/input_provenance.py#L56-L86)

## Reporting

For a sensitive vulnerability, use GitHub's private vulnerability reporting option **if the repository currently offers it**, or an already verified private channel to the owner. This review did not establish that private reporting is enabled and does not invent a contact address. Avoid posting credentials, private datasets or exploit details in a public issue. A sanitized public issue can describe a non-sensitive reproducibility or validation defect.

Include the affected source SHA, module/command, minimal synthetic reproduction, expected/actual behavior and impact. For a scientific-integrity issue, identify the affected result bundle, artifact path and failed claim-specific check. Preserve the original bytes and logs; do not replace recorded hashes to make a failure disappear.

## Scope and support

The repository has releases v1.0.0 and v1.1.0, but no source-defined supported-version/security SLA matrix was found. A release tag or green audit is not a security certification. Existing author identity, citation and MIT software license remain unchanged. [CITATION.cff:1–13](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/CITATION.cff#L1-L13)

The path/digest/provenance helpers reject several traversal and tampering cases, and their existing tests ran in this review. This is bounded verification, not a penetration test of every dependency or browser surface. Raw OPSD input must pass its pinned filename/digest before use. Write experimental outputs to a fresh directory and treat remote data as untrusted until validated. [tests/test_artifact_integrity.py:90–119](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_artifact_integrity.py#L90-L119) [tests/test_software_provenance.py:77–91](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_software_provenance.py#L77-L91) [tests/test_input_provenance.py:35–72](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/tests/test_input_provenance.py#L35-L72)

Ordinary branch protections, required signatures, checks and reviews apply to remediation as well. No bypass is authorized by this document. See the [release playbook](docs/maintainer/CI_CD_AND_RELEASE_PLAYBOOK.md) for current observed policy and the [roadmap](ROADMAP.md) for proposed audit improvements.
