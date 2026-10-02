# Management KPI extension

Read alongside [baseline KPI definitions](kpi_definitions.md). All figures use
synthetic data. Financial rates recalculate from additive sums.

| Metric | Formula / unit | Data grain and population | Interpretation |
|---|---|---|---|
| Weekly revenue growth | (current − prior revenue) / prior revenue | Restaurant / two complete rolling seven-day windows | Undefined if prior revenue is zero; holidays can change mix |
| Weekly target achievement | current seven-day revenue / sum(monthly revenue target / days in each month) | Restaurant / current window | Daily allocation is an assumption, not an hourly budget |
| Monthly Performance Index | weighted revenue, margin, labour, waste and satisfaction scores | Restaurant/calendar month | Shown alongside weekly queue; not a weekly index |
| Volume effect | (current orders − prior orders) × prior ATV; AUD | Restaurant/current and prior calendar month | Exact accounting decomposition, not causation |
| Net basket effect | (current ATV − prior ATV) × current orders; AUD | Same comparison | Includes price, mix and discount interactions; do not add them again |
| Scenario COGS | sold ingredients + discarded food cost; AUD | Restaurant/selected observed month under scenario | Different from legacy ingredient-only gross-margin denominator |
| Scenario operating contribution | revenue − COGS − commissions − labour − campaign spend | Same scenario | Before overheads; neither EBITDA nor cash flow is claimed |
| Scenario operating profit | contribution − overheads | Same scenario | Matches baseline ledger at zero changes |
| Break-even orders | fixed period labour/overheads/campaign spend divided by net unit contribution | Same scenario | No finite result if unit contribution ≤0; hours fixed within period |
| Forecast WAPE | sum(abs(actual − prediction)) / sum(actual) × 100 | Restaurant/model/evaluation period | Source metric unit 0–100; never average store WAPE into chain WAPE |
| Empirical band coverage | holdout actuals inside band / holdout observations | Selected model/restaurant/28 dates | Measured coverage, not a guarantee of 80% probability |
| Forecast hourly orders | daily forecast revenue / reference weekday ATV × prior hourly share | Restaurant/future local date/hour | Basket value and mix calibrated at/before origin |
| Suggested service hours | max(min staff, ceiling(hourly orders / (productivity × utilisation))) | Same hourly plan | One-hour integer coverage; not a constructed shift |
| Service coverage gap | suggested − scheduled-template service hours | Same hourly plan | Positive >0.5 flags potential under-coverage; below −0.5 flags potential spare capacity |
| Budget difference | (suggested total − scheduled-template total hours) × loaded wage | Same hourly plan / summed dates | Conditional cost difference; not realised payroll savings |
| Weekly waste opportunity | max(0, current waste − current ingredients × prior waste share / (1 − prior waste share)) | Restaurant/week | Conditional same-component comparison; feasibility untested |
| Weekly labour opportunity | max(0, current labour − current revenue × prior labour/revenue ratio) | Restaurant/week | Conditional rate comparison, not a recommended staffing cut |

The brief prioritises stores missing the allocated revenue target or operating
below a 10% margin, then proposes investigation. This 10% review threshold is an
analyst assumption for the case study, not an agreed stakeholder standard.

## Action measurement fields

Action primary targets use explicit metric units and direction: labour/waste share
lower; margin/profit/revenue/satisfaction higher. Compare entered value to the
revision's recorded absolute target, not a re-estimated target. Satisfaction floor
and maximum late-delivery share are separate guardrails. `window_complete` means
observation dates exactly span the measurement window; only a reviewed full-window
record on the latest revision can complete an action. Currency thresholds refer
to that window's total; unequal-duration baseline totals require normalisation.
Scenario profit delta is same-baseline-duration estimate, never achieved savings.
No cross-action sum of opportunities is reported. User-entered outcomes are unverified;
threshold results are not causal impact estimates. See [tracker](action_tracker.md).
