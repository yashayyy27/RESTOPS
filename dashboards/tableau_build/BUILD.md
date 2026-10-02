# RESTOPS minimal Tableau build bundle

**Native workbook status: NOT VERIFIED / not authored.** No Tableau application
or native authoring/validation connector is available in this environment.
The ZIP contains 13 reconciled synthetic CSV sources and their manifest, not a
`.twb` or `.twbx`. Source and financial verification does not verify a dashboard.

## Data connection and relationships

1. Unzip `restops_tableau_bundle.zip` into a stable folder. Open Tableau Desktop
   or Tableau Public's desktop authoring application. Add a Text File connection
   for each CSV named below; do not physically join any two fact tables.
2. For each fact source, use a separate logical data source. If it lacks store
   names/state, add `store_dimension.csv` as a logical relationship on
   `restaurant_id` (fact many → dimension one). All store keys have passed
   relationship validation. Declare matching records only after checking the
   provided manifest and key checks. Never relate two facts via this dimension
   inside the same multi-fact source for this minimal build.
3. Set `restaurant_id`, product IDs and campaign IDs to dimensions; ISO date
   fields to Date. Convert `month`/`cohort_month` with
   `DATE([month] + '-01')` / `DATE([cohort_month] + '-01')`. Preserve hour as
   integer. Use `Restaurant` and `State` filters from the dimension when present.
4. Keep customer snapshots (as of 31 Dec 2025), campaign windows (2024–2025) and
   forecast January 2026 separate from historical October–December month filters.
   Use explicit dashboard parameter-driven store filters per source:
   integer `pRestaurant` (all = 0), calculation `[pRestaurant] = 0 OR
   [restaurant_id] = [pRestaurant]`; keep True on every store-scoped sheet.
   Parameter `pMonth` string `2025-12` applies only to finance/product sheets
   using `[month] = [pMonth]`. Date filters on hourly views are independent.
5. Recalculate ratios with the fields in `calculations.md`; default monetary
   formatting `A$#,##0;(A$#,##0)`, ratios Percentage with one decimal, satisfaction
   two decimals. Null comparisons remain null. Do not replace them with zero.

## Exact minimal worksheet instructions

Create the sheets below. Each row names the sole fact source, field placements,
filter scope and what its tooltip must disclose. Extra decoration is optional.

| Page / worksheet | CSV source | Tableau shelves / marks | Filters and tooltip |
|---|---|---|---|
| Executive / Finance cards | store_month_kpis | Measure Names Columns; Measure Values Text; retain Revenue, Operating Profit, Operating Margin, Target Achievement | Store and pMonth; tooltip month, AUD ex-GST, formula denominator |
| Executive / Margin ranking | store_month_kpis | restaurant_name Rows; Operating Margin Columns; Bar; ascending margin | Store and pMonth; revenue, orders, six cost amounts and target |
| Executive / Revenue trend | store_day | business_date continuous Columns; SUM(revenue) Rows; Line | Store and historical date; exact selected date range |
| Executive / Weekly queue | weekly_performance | restaurant_name Rows; revenue, operating_profit, target_achievement_pct and labour_cost_pct Text via Measure Values | Store only; window_start/end and evenly prorated target definition |
| Operations / Demand pressure | store_hour | hour Columns; weekday Rows; AVG(capacity_gap_orders) Colour; Square | Store and historical date; AVG(transactions), AVG(service_hours), 6-order capacity assumption; pressure is modelled |
| Operations / Product contribution | product_month | category Rows; SUM(gross_contribution) Columns; Bar | Store and pMonth; units, net revenue and discount_amount; before labour/commission; orders_with_product not additive |
| Operations / Forward staffing | labour_plan | hour Columns; Measure Values Rows; scheduled_service_hours and suggested_service_hours Lines | Store and one business_date; forecast origin, productivity 6, utilisation 80%, default wage A$35, fixed support, historical schedule template |
| Customers / Repeat cohorts | customer_cohorts | cohort_month Columns; restaurant_id Rows; Repeat Rate Colour; Square | Store/cohort only; eligible_customers/repeat_customers; complete 90-day follow-up; anonymous visits excluded |
| Customers / Segment size | customer_segment_summary | segment Rows; SUM(customers) Columns; Bar | Store only; as-of 31 Dec 2025, SUM(spend), SUM(visits) |
| Customers / Campaign economics | promotion_effectiveness | promotion_id Rows; SUM(incremental_contribution) Columns; Bar | Store and campaign-start date only; estimate_status, control_stores, campaign_cost, low95/high95; observational result. Eligible ROI card uses only estimable campaigns |
| Forecast / History and future | forecast_plot | business_date continuous Columns; SUM(revenue) Rows; record_kind Colour; Line | Store only; record kind, lower_80/upper_80 (store only), origin 31 Dec 2025; synthetic continuation |
| Forecast / Model accuracy | forecast_backtests | model Rows; Forecast MAE, RMSE, WAPE Text via Measure Values | Store; evaluation_period='Holdout'; tooltip 4–31 Dec 2025; selection was on earlier validation, not this sheet |
| Forecast / Labour opportunity | labour_plan | business_date Columns; SUM(budget_difference) Rows; Bar | Store / future date; suggested minus repeated-template costs; conditional budget trade-off, not saved payroll |

## Assemble the four pages

Dashboard size Automatic or fixed 1440×900; dark canvas `#101014`, charcoal
`#19191F`, red `#FF3B30`, cyan `#58D6DF`. Titles: **Executive Performance**,
**Restaurant Operations**, **Customer & Loyalty**, **Forecasting & Opportunities**.
Place a visible “Synthetic portfolio data · AUD excluding GST” text object and
the page-specific period. Place relevant parameter/filter controls near the top.
Add navigation buttons between pages. A parameter action on Margin ranking
sets `pRestaurant` from restaurant_id so the investigation carries the store.
Add a URL action to the public repository's interview guide. Do not add an
unverified live app URL or claim the workbook writes to the action tracker.

The monthly index may be added with AVG(performance_index), labelled as mean
store-month index; it is not an additive weekly metric. YoY growth is excluded
from this minimal bundle demo because prior-year raw periods are not included.

## Manual work still required

Build and save the actual `.twb`/packaged `.twbx`, follow
`verification_checklist.md`, compare totals to `manifest.json`, and capture four
actual workbook screenshots. Only then update workbook status. Publishing to
Tableau Public requires separate user approval; it exposes its packaged data.
