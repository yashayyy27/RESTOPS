# Actual validation results

**Local developer automation and agent browser verification, 2 October 2026.**
Fictional stakeholders and UAT scenarios have not been run or accepted by real
restaurant users. This record maps implemented acceptance evidence to the proposed
[UAT scenarios](uat_scenarios.md); it does not assert stakeholder approval.

## Reproduction and evidence

The full fixed-seed pipeline completed on Python 3.12.14 using
`python -m src.run_pipeline --regenerate --skip-notebooks` in approximately
195 seconds. It generated 18 stores, 731 trading dates and 24 months. Cleaning
retained **794,925 complete orders / 2,105,626 lines**, quarantining **2,049 orders**.
All **97 post-clean schema, key, relationship, validity and financial checks**
passed. Source hashes are recorded in the locally generated
`reports/source_manifest.json`; large raw/processed files are excluded from Git.

Analysis, reporting, management exports and demo snapshots were refreshed after
promotion metadata/control eligibility was tightened. All six notebooks were
subsequently executed with `src.project_assets.execute_notebooks()`; their **42
code cells have execution counts and zero error outputs**. The earlier pipeline
metadata correctly records `notebooks_executed: false` for that skip-notebook run;
this separate execution was checked by reading the saved notebooks.

The final full suite ran **39 tests, zero failures, zero errors, zero skips**.
[Machine-readable test record](../reports/test_results.json) preserves the actual
execution time, counts and local scope. Black checked 30 Python files unchanged;
`compileall` passed. GitHub Actions is configured but has not run remotely.

## Acceptance evidence

| Scenario | Actual evidence | Result / boundary |
|---|---|---|
| UAT01 · scoped attention queue | Streamlit AppTest changes state to QLD (six stores), exercises empty selection; target-allocation test crosses month boundaries; browser exercised state filter and all-store restoration | Pass for developer checks; NSW scenario remains a proposed human UAT sequence |
| UAT02 · investigation | Exact volume/basket identity; profit bridge rejects unreconciled totals; independent source SQL; browser December Wollongong bridge | Pass; residual A$0. December revenue A$75,110, profit A$2,992, target gap −A$552; observed cost movement does not prove an operational cause |
| UAT03 · scenario | Identity ledger, discount-once, multiplicative wages/hours, waste denominator, break-even, nonviable case, sensitivity; AppTest staffing change and reset after baseline month change; browser changed hours −1% and waste to 4% | Pass; browser conditional profit A$4,152 vs baseline A$2,992, unchanged revenue. This is an assumption-based result, not achieved savings |
| UAT04 · planning | Prior-origin isolation, hourly demand conservation, productivity/zero schedule, shift-break conservation; AppTest productivity response; browser loaded default plan and changed productivity to 8 | Pass; default Wollongong 28-day plan: about 1,630 orders, 896 suggested hours, 868 template hours and A$992 budget difference. At productivity 8, suggested hours fell to 821 and budget difference to −A$1,633; downloaded CSV had 308 rows / 28 dates for the selected store. Not an employee roster |
| UAT05 · forecast | Three validation folds, final holdout isolation, recursive lag tests; independent per-store score recomputation; browser store model comparison/bands | Pass; Wollongong selected-model holdout MAE A$388, RMSE A$476, WAPE 15.6%, band coverage 75.0%. Chain errors differ |
| UAT06 · promotion | Incremental revenue/cost/contribution and ROI identity; unavailable spend cannot dilute reported ROI; controls exclude any campaign overlap; isolated expected-order-uplift validation; all-view app execution | Pass; campaigns without eligible controls retain metadata and display no estimate. Counterfactual and intervals remain observational |
| UAT07 · customers | Eligible follow-up and independently computed repeat rate; full-snapshot/global-scope labels; app execution | Pass for developer evidence; no real retention experiment conducted |
| UAT08 · quality | Deliberate schema/key/relationship/null/date/money mutations fail; basket quarantine; SQLite integrity and foreign keys; independent ledger SQL; all-view app execution | Pass; demo shows precomputed full-source quality evidence, not a new raw audit |
| UAT09 · brief | Evidence and impact formula tests; current/prior store/window trace fields; generated Markdown/CSV | Pass; owners and actions are proposals; component opportunities are not additive or committed savings |
| UAT10 · portable demonstration | AppTest explicitly uses committed demo, all eight views have metrics and computed tables; actual browser screenshots; XLSX OOXML read-back | Pass locally; no clean external machine or remote CI execution claimed |

## Application and exports

The real Streamlit server started on loopback `127.0.0.1:8501`. Agent browser
verification covered the executive screen, state filter, restaurant investigation,
scenario controls/results, forecasting and labour controls. All eight views also
executed in Streamlit's AppTest against the committed demo without exceptions.
Actual screenshots are in `docs/screenshots/`; screen captures use the normal
in-app browser viewport and some show the controls/results part of a longer page.

The native Excel pack contains four worksheets: Weekly review, Labour planning,
Scenario comparison and ReadMe. All four were rendered and visually inspected;
the export inspection found zero spreadsheet error values. A separate OOXML
reader compared all 18 exported weekly revenue values to daily-ledger calculations
(to cents). The workbook is a typed snapshot, not a live scenario calculator.
Catalog keys were checked for uniqueness/non-nullness in 12 available demo marts.
Tableau logical-source grain/join instructions are provided; no native workbook
or published dashboard exists.

## Commands

```bash
python -m unittest discover -s tests -v
python -m black --check --workers 1 src tests streamlit_app.py
python -m compileall -q src tests streamlit_app.py
python -c 'from src.project_assets import execute_notebooks; execute_notebooks()'
python -m streamlit run streamlit_app.py
```

Proposed production acceptance still requires actual managers to validate service
productivity, source completeness, calendar target allocation, employee/award
constraints, decision workflow fit and measured pilot outcomes. Those activities
have not been invented or marked passed.
