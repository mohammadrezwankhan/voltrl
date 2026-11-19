# Documentation maintenance runbook

[Handbook](../INDEX.md) · Source `8058e89e4d35` · Documentation snapshot 2026-11-19.

Markdown is canonical. `docs/reference/index.html` is a dated derived reading view built from the explicit [chapter manifest](../reference/chapters.json), [renderer](../reference/build_reference.py) and [stylesheet](../reference/reference.css). Keep the existing lesson pages as their own preserved teaching products; add navigation without changing their models or embedded configurations.

## A source-grounded update

1. Pin the reviewed commit and enumerate its full Git tree. Read changed scientific logic, public interfaces, tests, data records and publication configuration; index generated/binary material with an honest disposition.
2. Update canonical pages with exact source commit/line links. Distinguish implemented behavior, declared settings, measured checks, inferred limitations and proposed work. Keep source, test, result-generation, docs, merge and deployment identities separate.
3. Update the chapter manifest's reviewed date/source only when the underlying review changes. Update affected equations, parameter tables, examples and evidence limits together.
4. Run the relevant native commands and docs checks. Preserve command/environment/revision/outcome receipts externally; avoid circular “this commit verified itself” claims in the files it introduces.
5. Regenerate the reading view, inspect desktop/narrow reading layouts, then obtain independent content review and follow the guarded release playbook.

## Regenerate deterministically

```bash
python docs/reference/build_reference.py
python docs/reference/build_reference.py --check
python scripts/portfolio/validate_guide.py
git diff --check
```

The renderer uses a fixed file manifest, Python standard library and Pandoc (reviewed with 3.1.11.1). It converts GitHub-flavored Markdown and mathematical expressions to static HTML/MathML, namespaces headings, resolves chapter links, and records SHA-256 for each canonical input plus manifest, renderer and CSS in a final HTML comment. It rejects active chapter HTML/event attributes and uses an explicit no-script Content Security Policy. It writes only the derived `index.html`; `--check` compares the expected output without writing. A different Pandoc version can cause a deliberate freshness diff and needs review.

Chapter links resolve within the generated handbook; site HTML routes remain local. Repository files outside the handbook are linked to the reviewed source SHA, while the canonical Markdown preserves normal repository-relative navigation. The root README is an entry point and is preserved; its large existing presentation is not duplicated as a handbook chapter. New policies and citation metadata are included in the reading view.

## Required review checks

Verify all 24 requested canonical outputs, preserved README/CONTRIBUTING prefixes and unchanged citation/license. Check local Markdown and generated HTML paths/anchors, source locator ranges, unique headings/IDs, no broken table/fence structure, CFF 1.2.0 schema, all planned roadmap fields, and an authorized file diff. New native examples need actual execution or an explicit unexecuted label. User-facing dates are snapshots or proposals, not release/deployment claims.

The current Lychee workflow checks README, MANIFEST and data/README only. Its success does not establish complete handbook link coverage. The portfolio validator likewise validates the existing six-path guide, not every new chapter. Keep the local full-handbook checks until separately authorized CI work closes this gap. [.github/workflows/markdown-maintenance.yml:24–37](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/.github/workflows/markdown-maintenance.yml#L24-L37) [scripts/portfolio/validate_guide.py:1–33](https://github.com/mohammadrezwankhan/voltrl/blob/8058e89e4d3516825a400fe86ac45d2e36b6bef0/scripts/portfolio/validate_guide.py#L1-L33)

## Presentation and accessibility

The handbook uses the existing dark purple, cream and orange palette; readable line length, visible keyboard focus, a skip link, scrollable wide tables, mobile chapter navigation and a print stylesheet. It introduces no motion, network script or external font. Inspect equations, long source links, tables and code on a narrow viewport and in print. Static structure checks support this review; only an actual browser/assistive-technology session can establish runtime accessibility.

## Correcting a published statement

Add a dated correction grounded in evidence, regenerate the handbook and review the exact diff. Preserve archived result files and source manifests unless a separately authorized scientific change intentionally supersedes them. If the old bundle is withdrawn, retain the explanation and provenance instead of silently rewriting history. Use [CHANGELOG](../../CHANGELOG.md) for documentation changes and [ADR index](../owner/ADR/ADR-0000-INDEX.md) for decisions requiring owner approval.
