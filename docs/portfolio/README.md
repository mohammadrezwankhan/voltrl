# VoltRL · Battery Arbitrage Research — learning map

A finite-state battery-arbitrage benchmark with explicit data provenance, information boundaries and result contracts.

This companion organises 6 selected source-backed paths. It complements the repository's full documentation and native lessons. It does not execute its scientific or operational models.

Open `index.html` locally for search, topic filters, source/configuration inspection, personal notes and study-plan export. The guide has no network or build dependency.

Open the [offline interactive lesson lab](../index.html) and inspect its [lesson configuration](../lesson-config.json).

> [!IMPORTANT]
> Preserve the native [information boundary](../../README.md): realized prices enter settlement only after the action is selected. Forecast-driven policy inputs must not include future realized prices; the lesson simulators do not certify a trading strategy.

| Path | Learning objective | Level | First source |
| --- | --- | --- | --- |
| path-01 | Verify historical input provenance | Foundation | [data/opsd_source.json](../../data/opsd_source.json) |
| path-02 | Define causal information boundaries | Foundation | [voltrl_benchmark.py](../../voltrl_benchmark.py) |
| path-03 | Select a finite-state model | Applied | [voltrl_benchmark.py](../../voltrl_benchmark.py) |
| path-04 | Check battery reward and feasibility | Applied | [voltrl_benchmark.py](../../voltrl_benchmark.py) |
| path-05 | Recompute synthetic policy comparisons | Advanced | [synthetic_statistics_contract.py](../../synthetic_statistics_contract.py) |
| path-06 | Verify the complete evidence bundle | Advanced | [result_bundle_audit.py](../../result_bundle_audit.py) |

## Provenance

Repository: <https://github.com/mohammadrezwankhan/voltrl>

Pinned source: c86bf0e52adf06922bbbf35f2274b68485a22660

Native commands and expected outputs are guidance unless accompanied by a separate execution record. Reviewed-path progress is a personal learning record.
