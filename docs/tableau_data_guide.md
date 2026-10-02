# Tableau and Excel data guide

Native Tableau workbooks and published dashboards have not been created. The
working interactive application is Streamlit. Tableau receives explicit-grain
CSV marts after reproduction; [tableau_catalog.json](tableau_catalog.json)
records keys, lineage and safe-join guidance for management datasets.

## Relationships

| Dataset | Unique key | Grain and period |
|---|---|---|
| store_day | restaurant_id, business_date | One restaurant/trading date; finance facts aggregated independently |
| store_hour | restaurant_id, business_date, hour | Local trading hour; actual and scheduled paid hours remain separate |
| store_month_kpis | restaurant_id, month | Calendar-month additive financials, monthly targets and index |
| product_month | restaurant_id, month, product_id, channel | Product sales, list sales, discount, ingredient contribution and units |
| waste_detail | restaurant_id, business_date, product_id, reason | Waste units and cost by logged reason |
| customer_segment_summary | restaurant_id, segment | Identified customer snapshot at history end |
| customer_cohorts | restaurant_id, cohort_month | First-observed cohort and full-follow-up repeat numerator/denominator |
| promotion_effectiveness | promotion_id | One campaign/store; full before/during comparison and cost bridge |
| forecast_daily | restaurant_id, business_date | One future date at one forecast origin |
| forecast_store_metrics | restaurant_id, evaluation_period, model | Store error summaries; validation combines three folds |
| forecast_backtests | restaurant_id, business_date, model, origin_date | Actual/predicted pairs; filter model and period before aggregating |
| labour_plan | restaurant_id, business_date, hour | Default future hourly allocation and coverage suggestions |
| weekly_performance | restaurant_id, window_end | Latest rolling seven-day window versus previous seven days |
| weekly_management_brief | restaurant_id, window_end | Computed evidence, conditional opportunity and proposed action |

Use separate logical data sources or relationships through stable store
dimensions and matching temporal grains. Do not physically join hourly, monthly,
product, customer and campaign facts on store/date alone. This multiplies rows
and campaign/cost amounts. Aggregate facts separately to a common grain before
a physical join. Validate uniqueness on the complete key before loading.

Product `orders_with_product` is not additive across products. Recalculate
financial ratios from summed values. The index is a mean of bounded store-month
scores when aggregated, not a weekly financial metric. `loyalty_behaviours` is a
company-wide table that does not support store filtering. Customer snapshots and
campaign windows must not silently inherit a historical reporting-month filter.

## Percentage and missing-value conventions

KPI ratios, ROI and interval coverage use 0–1 fractions; forecast WAPE/MAPE in
metrics files use 0–100. Undefined denominators and unavailable controls stay
null. Zero sales/costs remain zero. Anonymous customers and missing survey answers
are optional nulls, not data-quality failures. CSVs are UTF-8, numeric values
remain numeric, dates use ISO format, and monetary units are AUD excluding GST.

## Excel delivery

The app downloads current-selection UTF-8 BOM CSVs and scenario assumption JSON.
These are the authoritative exports for current filters and scenario settings.
Pipeline CSVs in `reports/exports/` include weekly performance, hourly labour
planning, scenario comparisons/sensitivity, campaign review and forecasts.

`reports/exports/weekly_management_pack.xlsx` is a prepared snapshot with weekly
performance, daily labour totals and an illustrative Wollongong scenario. It
does not recalculate when app filters change and is not an editable Excel
scenario engine. The scenario comparison distinguishes observed baseline from
estimated results and records its assumptions and source period.

Rebuild analytical inputs with `python -m src.run_pipeline --regenerate
--skip-notebooks`. The optional `tools/export_excel.mjs` exports the prepared XLSX
with an available `@oai/artifact-tool` runtime, after `python -m
src.excel_inputs`. Core Python reproduction and current-selection CSV downloads
do not depend on that optional authoring runtime.

## Minimal verified build handoff

[Build ZIP](../dashboards/tableau_build/restops_tableau_bundle.zip) provides 13
sources, checks/hashes, exact relationships/calculations, sheet placements and
four-page assembly instructions. [Native checklist](../dashboards/tableau_build/verification_checklist.md)
remains NOT VERIFIED. `python -m src.tableau_bundle` regenerates this small handoff
from committed demo data. Source checks are not native Tableau validation.
