# Historical data provenance

The historical pilot uses the `DK_1_price_day_ahead` and
`DK_2_price_day_ahead` columns from **Open Power System Data, Time series,
version 2020-10-06**.

- DOI: <https://doi.org/10.25832/time_series/2020-10-06>
- Official package: <https://data.open-power-system-data.org/time_series/2020-10-06/>
- Required local filename: `opsd_time_series_60min_singleindex_2020-10-06.csv`
- SHA-256: `6A7F2BC571314CBF9C321CC03437691CD4BE95C3A6F075E60FF99E8035C704C8`

The CSV is not stored in this repository because its size exceeds GitHub's
per-file limit. Download it from the official versioned package, place it in
this directory, and verify the checksum before running the benchmark. The same
metadata is available to tools in [`opsd_source.json`](opsd_source.json).

Cross-platform verification:

```powershell
python input_provenance.py `
  data\opsd_time_series_60min_singleindex_2020-10-06.csv
```

`voltrl_benchmark.py` performs this verification automatically and stops before
loading the CSV if its filename or content does not match the source record.
