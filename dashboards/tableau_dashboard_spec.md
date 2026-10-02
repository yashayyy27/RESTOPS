# Tableau dashboard specification

**Audience:** Area Managers and Operations Managers  
**Decision cycle:** Weekly, with store/daypart drill-down  
**Status:** Build specification and prepared datasets; a native Tableau workbook
has not been built or published.

## Visual system

- Canvas: 1440 × 900; a compact header, KPI row, diagnostic charts, action context.
- Formula 1-inspired presentation: near-black canvas `#101014`, charcoal panels
  `#19191F`, racing red `#FF3B30`, off-white text `#F4F4F6` and muted text `#B0B0BB`.
- Use racing red for the active view, key series and section accents; cyan
  `#58D6DF` distinguishes comparison series and amber `#FFC16A` marks review flags.
  Red is an accent, not an automatic loss signal. Always label values and statuses.
- Use bold, slightly italic display titles, tabular numerals, compact uppercase
  field labels and numbered views. Frame panels with subtle borders and one
  rounded upper corner, evoking a motorsport performance screen.
- Restaurant priority grids show operating margin from lowest to highest and
  clearly label that ordering; an index badge never replaces its underlying KPIs.
- Use AUD units, one decimal for percentages, two decimals for satisfaction.
- Make denominator, period and metric scope available in every tooltip.
- Keep executive cards to six; favour directly labelled charts over decoration.
- Display a visible **Synthetic portfolio data** label and refresh/source period.

## Data sources and safe relationships

| Dataset | Grain | Use |
|---|---|---|
| `store_month_kpis.csv` | Store/month | Executive finance, targets and index |
| `store_day.csv` | Store/date | Trends and operating detail |
| `store_hour.csv` | Store/date/hour | Demand, service capacity and staffing |
| `product_month.csv` | Store/month/product/channel | Product economics |
| `store_segments.csv` | Store/full period | Exploratory store segments |
| `latest_store_opportunities.csv` | Store/latest quarter | Waste peer opportunities |
| `customer_segments.csv` | Identified customer/as-of date | RFM worklist |
| `customer_cohorts.csv` | Store/acquisition month | Eligible repeat cohorts |
| `loyalty_behaviours.csv` | Early-activity/redemption group | Later-return comparisons |
| `promotion_effectiveness.csv` | Campaign/store | Incremental contribution estimates |
| `staffing_patterns.csv` | Store/weekday/hour | Recurring staffing patterns |
| `sales_anomalies.csv` | Flagged store/date | Investigation queue |
| `forecast_daily.csv` | Store/future date | Four-week planning |
| `forecast_backtests.csv` | Store/date/model/origin | Forecast validation |
| `forecast_metrics.csv` | Evaluation period/fold/model | Accuracy comparison |
| `forecast_store_metrics.csv` | Store/evaluation/model | Store-level error and band coverage |
| `customer_segment_summary.csv` | Store/segment/as-of snapshot | Compact segment counts and value |
| `waste_detail.csv` | Store/date/product/reason | Waste investigation |
| `labour_plan.csv` | Store/future date/hour/default assumptions | Forecast demand, suggested vs scheduled-template coverage and costs |
| `weekly_performance.csv` | Store/rolling seven-day window | Attention queue and prior-week comparisons |
| `weekly_management_brief.csv` | Store/rolling seven-day decision | Proposed owner, conditional impact and measurement |

Use Tableau logical relationships or separate data sources. Do not physically
join monthly, hourly, product or customer facts, which would multiply measures.
Store dimensions relate by ID. Temporal relationships require the appropriate
date/month key. `loyalty_behaviours.csv` is an aggregated all-company table and
must not pretend to respond to a store filter.

Explicit keys and export semantics are in `docs/tableau_catalog.json` and
`docs/tableau_data_guide.md`. Scheduled paid/service hours are separate from
observed actual paid/service hours in `store_hour`. The planning schedule is a
historical weekday template, not a supplied or approved future roster.

## Page 1 · Executive Performance

**Decision:** Which restaurants need attention this week, and why?

- KPIs: revenue, operating profit, operating margin, revenue YoY growth, revenue
  target achievement and mean monthly Performance Index.
- Charts: revenue/profit monthly trend; store margin ranking; actual vs target
  bullet chart; cost bridge showing ingredient, labour, waste, commissions,
  overhead and campaign costs; index components by selected restaurant.
- Filters: month range, state, area, restaurant and location type.
- Parameters: selected financial metric and comparable period (prior month or
  prior year). For range comparisons, use identical elapsed months and store sets.
- Tooltips: selected period, revenue, transaction count, target, answered surveys,
  cost amounts, component scores and whether the index is complete.
- Interactions: selecting a store filters the trend and component views; an
  Operations navigation action preserves restaurant/area selection.
  A weekly queue selection opens a restaurant's exact volume/basket/cost bridge.
  Supporting product mix and discount views explain associations but are not
  counted as extra additive revenue bridge components.
- Watch-outs: the index is a mean of store-month scores when aggregated; financial
  percentages are recalculated from sums. Never sum precomputed percentages.

## Page 2 · Restaurant Operations

**Decision:** Where should managers change roster timing or preparation practices?

- KPIs: labour cost %, sales/labour hour, orders/labour hour, waste %, pressure
  hour share and late-delivery share.
- Charts: weekday/hour pressure heatmap; hourly demand vs service capacity;
  product contribution bars; waste by product and reason; store waste vs
  location peers; annotated sales exception list.
- Filters: business date, store, state, area, weekday and daypart. Product/category
  filters apply only to product/waste views; they do not filter all-store labour.
- Parameters: service capacity benchmark (default 6 orders/service hour), gap
  tolerance (default 2 orders) and spare-capacity threshold (default 45%).
- Tooltips: paid service hours, total paid hours, orders, capacity assumption,
  capacity gap, allocation assumption and cost denominators.
  Forward-planning tooltips include forecast origin, historical ATV/hour mix,
  scheduled template, suggested service/support hours and budget difference.
- Interactions: clicking a heatmap cell opens daily observations for that
  restaurant/weekday/hour. Product selection filters its waste detail.
- Guardrail: label output as **Modelled service pressure**, not proven understaffing.
  Benchmark parameters modify staffing calculations only; they do not regenerate
  historical satisfaction, sales or forecasts.

## Page 3 · Customer & Loyalty

**Decision:** Which customer/service experiments should be prioritised?

- KPIs: satisfaction with answer count, identified-order share, eligible 90-day
  repeat rate, identified customers and estimated promotion contribution/ROI.
- Charts: satisfaction trend; first-observed cohort repeat heatmap; RFM segment
  size/value; early activity vs later return; campaign contribution with
  approximate 95% uncertainty ranges; sales uplift vs contribution scatter.
- Filters: restaurant/state for scoped datasets; first-observed cohort month;
  segment; campaign and campaign start period.
- Parameters: customer measure (customers, spend or visits) and promotion measure
  (incremental revenue, contribution or ROI).
- Tooltips: cohort eligibility, complete follow-up, anonymous exclusion,
  campaign cost, control count, counterfactual method and uncertainty limitation.
- Interactions: selecting a segment shows recency/frequency/value detail. Campaign
  selection opens campaign economics. Explain when a global behaviour view is
  unaffected by restaurant filters.
- Guardrails: do not expose a repeat-window selector without regenerating cohorts.
  Do not call redemption comparisons causal retention improvements.

## Page 4 · Forecasting & Opportunities

**Decision:** What should managers expect over the next four weeks, and where can
they run a measurable operational pilot?

- KPIs: 28-day expected revenue, selected-model holdout MAE/RMSE/MAPE/WAPE, and
  measured store-level empirical-band holdout coverage.
  Include per-store baseline comparison and keep evaluation-period/model filters
  locked for each comparison. Store WAPE must not be averaged into chain WAPE.
- Charts: historical daily sales + future forecast; per-store empirical bands;
  weekly forecast totals; model comparison; ranked latest-quarter waste worklist;
  hourly demand mix to support a roster discussion.
- Filters: restaurant, state, area, forecast week and evaluation period.
- Parameters: displayed comparison model for backtests and selected opportunity
  type. The published future forecast uses the validation-selected model only.
- Tooltips: forecast origin, horizon day, selected model, evaluation period,
  actual/predicted values, error and interval method.
- Interactions: choosing a store updates its forecast and opportunity details.
  Selecting a model changes accuracy/backtest views, not an ungenerated future
  series. Link to the recommendation register.
  An opportunity selection opens the proposed owner, success measure and
  conditional impact basis. The implemented Streamlit scenario workflow can be
  linked as a separate local tool; no native Tableau scenario worksheet is claimed.
- Guardrails: forecasts are a January 2026 synthetic continuation. Do not sum
  store bounds for chain intervals. Waste estimates are hypotheses, not committed
  savings. Revenue forecasts alone do not determine an approved staffing plan.

## Calculated fields

```text
Revenue = SUM([revenue])
Operating Margin = SUM([operating_profit]) / SUM([revenue])
Gross Margin = (SUM([revenue]) - SUM([ingredient_cost])) / SUM([revenue])
Average Transaction Value = SUM([revenue]) / SUM([transactions])
Labour Cost % = SUM([labour_cost]) / SUM([revenue])
Sales per Labour Hour = SUM([revenue]) / SUM([paid_hours])
Orders per Labour Hour = SUM([transactions]) / SUM([paid_hours])
Waste % = SUM([waste_cost]) / SUM([ingredient_cost] + [waste_cost])
Satisfaction = SUM([score_sum]) / SUM([survey_responses])
Target Achievement = SUM([revenue]) / SUM([revenue_target])
Repeat Rate = SUM([repeat_customers]) / SUM([eligible_customers])
Promotion ROI = SUM([incremental_contribution]) / SUM([campaign_cost])
Service Capacity = [service_hours] * [Capacity Benchmark]
Capacity Gap = [transactions] - [Service Capacity]
Pressure Flag = INT([Capacity Gap] > [Gap Tolerance])
Pressure Hour Share = AVG([Pressure Flag])
Forecast MAE = AVG(ABS([actual_revenue] - [forecast_revenue]))
Forecast RMSE = SQRT(AVG(POWER([actual_revenue] - [forecast_revenue], 2)))
Forecast WAPE = SUM(ABS([actual_revenue] - [forecast_revenue])) / SUM([actual_revenue])
Suggested Service Hours = MAX([Minimum Service Staff], CEILING([forecast_orders] / ([Orders Per Service Hour] * [Target Utilisation])))
Planning Budget Difference = SUM([suggested_labour_cost]) - SUM([template_labour_cost])
Scenario COGS = [Scenario Sold Ingredient Cost] + [Scenario Waste Cost]
Scenario Operating Profit = [Scenario Revenue] - [Scenario COGS] - [Scenario Labour Cost] - [Scenario Commission Cost] - [Campaign Cost] - [Overhead Cost]
```

Add explicit denominator checks: `IF SUM([denominator]) = 0 THEN NULL ELSE ... END`.
For aggregate promotion ROI, filter both numerator and campaign-cost denominator
to campaigns with an available estimate. Missing controls must not dilute ROI
with unestimated spending; the exact minimal-build calculation records this filter.
For MAPE, return null for zero actuals before averaging. Forecast KPI sources
store percentage metrics in 0–100 units, whereas the ratio calculations above
return 0–1 and use percentage formatting. Do not average fold/store MAPE without
making that weighting explicit. Filter backtests to one model and evaluation
period before calculating errors.

YoY growth should join or look up the same store/month 12 months previously;
Tableau date filters must retain comparison data or use a prepared comparison
field. For product data, never sum `orders_with_product` into order counts.

The scenario field names above are logical worksheet build inputs, not existing
columns in historical marts. Their formulas and assumptions are documented in
`docs/decision_support_methodology.md`. The implemented six-driver simulator is
Streamlit. Dashboard parameters must not imply regenerated customer cohorts,
models, promotion outcomes or legal rosters.

## Acceptance and screenshot plan

Check finance cards against `management_store_scorecard.csv` and the source KPI
SQL. Confirm filters apply only where supported. Verify date populations, null
handling, sample sizes, index aggregation and campaign cost uniqueness.

Capture four native workbook screenshots into `dashboards/screenshots/`:
`executive.png`, `operations.png`, `customers.png`, `forecasting.png`.
README placeholders deliberately remain until these screenshots exist. The
offline HTML overview is a separate portfolio preview, not a Tableau screenshot.

## Executable manual build handoff

Use [BUILD.md](tableau_build/BUILD.md) and the packaged ZIP for exact source,
relationship, calculation, shelf and filter instructions. The minimal bundle
covers October–December historical finance, full labelled customer/campaign
snapshots and January forecasts. It excludes native scenario/action persistence,
YoY worksheets and full customer-ID worklists. These optional specification items
must not be implied to exist in a native workbook. Data bundle is verified;
native authoring, filters, screenshots and publication remain NOT VERIFIED.
