# Governance and project scope

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

The repository owner is `mohammadrezwankhan`; existing citation metadata identifies **Mohammad Rezwan Khan** and the ORCID already recorded by the project. No backup maintainer, service-level agreement or production operator is declared in the pinned source. Role assignments below are proposals, not evidence of staffed teams. [CITATION.cff:1–13](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/CITATION.cff#L1-L13)

## Purpose and supported claims

Maintain an auditable finite-state battery-arbitrage benchmark with explicit data, information, objective and source provenance. The project compares policies and exposes their limits; it does not connect to a market, dispatch a plant or certify degradation. Its teaching site is a separate synthetic explanation. [README.md:90–119](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/README.md#L90-L119) [README.md:270–278](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/README.md#L270-L278)

| Responsibility | Suggested role | Required decision/evidence |
| --- | --- | --- |
| Scientific protocol and claims | Scientific maintainer | Approve information boundary, battery/cost conventions, comparison objective and uncertainty estimand |
| Implementation and audit contracts | Python maintainer | Preserve reproducible interfaces and historical audit behavior; add meaningful regression tests for changes |
| Research data | Data steward | Record exact OPSD version/digest, terms, preprocessing and any proposed new input |
| Documentation and teaching | Documentation maintainer | Keep native and browser boundaries explicit; regenerate derived handbook |
| CI, release and access | Repository owner / release maintainer | Observe complete branch rules, signatures, checks/reviews, guarded merge and deployment provenance |
| Recovery | Designated backup maintainer, to be appointed | Demonstrate restore/audit procedure using independently retained repository and required input |

The owner should approve scientific scope expansions, new data/licensing obligations and release claims. Documentation clarification can preserve current science while recording defects as proposals. [Roadmap](../../ROADMAP.md) effort and staffing are estimates, not commitments.

## Sources of authority

Source and tests define implemented behavior; manifests define archived experiment configuration; OPSD defines its data package and upstream terms; CFF and LICENSE define existing software attribution/license. A README assertion, a browser checkpoint or a successful hash audit alone does not establish the whole scientific claim. [Evidence limits](../math-and-physics/ASSUMPTIONS_AND_LIMITS.md).

The observed active signature ruleset has no bypass. Classic protection details require an authorized refresh before integration. Owner permissions do not erase these requirements. Retain exact-revision QA and delivery receipts separately from canonical explanatory documents. [Release playbook](../maintainer/CI_CD_AND_RELEASE_PLAYBOOK.md).

## Decisions requiring explicit follow-up

The current interpretation of `max_power_mw` as internal step rate, historical delivery-time abstraction, interpolation method, terminal valuation and aging proxy materially affect interpretation. Changing any of them needs a reviewed protocol and a new comparison, not just a wording change. Submission assets referenced by MANIFEST are unavailable in this tree; publication claims require the actual assets and checks. [voltrl.py:105–194](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl.py#L105-L194) [voltrl_benchmark.py:712–811](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L712-L811) [voltrl_benchmark.py:1083–1118](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/voltrl_benchmark.py#L1083-L1118) [MANIFEST.md:5–9](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/MANIFEST.md#L5-L9)

Public project documentation contains only public Voltrl evidence. Do not insert private portfolio repository identities, counts, findings, credentials or owner recovery secrets into this repository.
