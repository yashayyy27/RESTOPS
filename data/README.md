# Data layers

All data is generated and fictional. Do not use these figures as industry benchmarks.

- `raw/`: source exports with deliberate quality problems; unchanged during cleaning.
- `processed/`: validated source tables, quarantine files, orders, marts and SQLite.
- `tableau/`: explicit-grain CSVs prepared for Tableau relationships and worksheets.
- `sample/`: small previews committed to Git; not a complete relational dataset.

Large generated files are excluded from ordinary Git commits. Run
`python -m src.run_pipeline` from the repository root to recreate them. The
generation manifest records the seed, configuration and injected defect locations
for independent QA; cleaning does not consume that manifest.

CSV exports also open in Excel. Raw transaction lines exceed Excel's per-sheet
row limit, so use the smaller management exports or SQLite for full analysis.
See `docs/data_dictionary.md` for grains, keys, units and null semantics.
