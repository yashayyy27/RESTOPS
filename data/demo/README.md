# Portable RESTOPS demo

Exact synthetic aggregates for 1 October–31 December 2025 (92 days), all 18
restaurants. Compressed CSVs load directly in Pandas without manual extraction.
Customer/cohort snapshots retain their original full-history/as-of scope;
campaign and chronological forecast evaluation evidence retain their labelled
periods. Future revenue covers 1–28 January 2026.

Quality checks are precomputed full-pipeline evidence; the raw ledger is not in
this bundle. A 100-line quarantine preview is included. No individual-customer
table or hidden generator parameters are supplied as app/model features.
Promotion method validation contains expected-effect comparison results only.

Run `python -m streamlit run streamlit_app.py` without generating raw data.
The app automatically uses this bundle when full local marts are absent, or
choose Dataset **Demo**. Rebuild with `python -m src.run_pipeline --regenerate`;
`src.build_management.demo_bundle` refreshes the compressed extracts with fixed
gzip timestamps for stable commits. See `app_manifest.json` for exact scope.
