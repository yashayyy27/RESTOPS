# Methodology, assumptions and limitations

## Source simulation

The fixed-seed generator creates 18 restaurants and 731 daily trading dates in
2024–2025. It creates customer orders before product lines, preserving a clear
basket structure. Restaurant identity, size and location influence demand;
weekday, season, growth, holidays and campaigns create temporal variation.
Prices and ingredient costs increase modestly in 2025. Service pressure,
operating efficiency and random variation influence survey scores and delivery.
Waste is linked to sold quantities, product groups and efficiency.

Latent efficiency values are generator-only mechanisms. Models receive exported
operational observations, not hidden causal parameters. Manager assignments
provide context, but one manager per store means this dataset cannot identify
an independent manager effect separate from restaurant identity.

State public holiday dates come from the installed `holidays` package. School
holiday flags are illustrative seasonal proxies, explicitly named as such.
Trading hours, wage rates and loadings are simulated business assumptions, not
Australian award or legal advice. GST is a simplified 10% line calculation.

## Data quality

Raw files are retained through cleaning. Exact duplicates are removed; conflicting
primary keys stop the pipeline. Store IDs resolve inconsistent names. Product
names are checked against the versioned business-approved taxonomy in
`config/product_categories.json`; the hidden defect manifest is not used to
restore values. Invalid basket lines cause the entire order to be quarantined.
Linked delivery and loyalty events are excluded with an audit trail; surveys
retain store-level observations and lose invalid order links.

Paid hours can be recovered from valid shift times and breaks. Missing loaded
rates are inferred from comparable role/weekend/holiday classes and flagged.
Invalid survey scores become null. Negative waste records are quarantined.
Extreme values are assessed with business constraints rather than indiscriminately
winsorised. Deliberately damaged records reduce coverage; excluded revenue is
not interpreted as a business loss.

## Operational analysis

Hourly paid time is distributed uniformly over each shift because break timing
is absent. Service capacity is six orders per paid service hour. A gap greater
than two orders flags pressure; utilisation below 45% flags spare capacity.
These are scenario thresholds requiring operational validation, and pressure
does not itself prove actual understaffing.

Store segments use standardised margin, labour rate, waste, satisfaction and sales
per labour hour in three-cluster K-means. Clusters are named by mean margin for
interpretability. Eighteen stores is a small sample; assignments are exploratory,
not permanent ratings. Location-based peers remain available as an alternative.

Sales anomalies compare each store/weekday against the preceding 12 observations,
requiring at least eight. Robust z-scores use the prior median and median absolute
deviation; absolute values over 3.5 are review flags. Holidays and promotions are
retained as context rather than automatically classified as export errors.

## Customer analysis

RFM segments use a snapshot at the historical end date. Visit frequency counts
distinct business dates. Customers are anonymous store-local IDs; cross-store
identity is not simulated. Repeat rate uses the first observed visit, not proven
first-ever acquisition, and requires 90 full follow-up days.

Segment rules are applied in order: Champions have recency ≤30 days and at least
12 visit dates; Lapsed customers have recency >90 days; New / occasional customers
have at most two visits and recency ≤30 days; Regulars have at least six visits;
remaining identified customers are Developing. These practical thresholds are
assumptions, not learned customer propensities.

For behaviour analysis, early visits/redemption are measured in days 0–30, then
returns in days 31–90. Comparisons are stratified by early activity. Selection,
customer preference and opportunity to visit prevent causal attribution to
loyalty redemption. Simulated points redemptions are behavioural events and do
not represent additional monetary POS discounts in this version.

## Promotions

Campaign timing is staggered across stores. A treated store's prior 14-day
fortnight supplies same-weekday reference observations; unpromoted stores of the
same location type supply the contemporaneous demand-change adjustment. Controls
with campaigns during either window are excluded. No eligible controls yields
an explicit unavailable estimate.

Incremental contribution subtracts estimated incremental ingredient/waste/
commission costs, observed incremental labour and campaign spending. Fixed
overheads are assumed unchanged. The prior variable-cost ratio supplies the
counterfactual. Discount costs are already reflected in net revenue.
Incremental order counts are also estimated using the control group's order
change, keeping customer volume separate from discounted net sales.

Approximate 95% ranges resample the 14 daily contribution differences 1,000 times.
They do not fully capture counterfactual uncertainty, serial dependence or
unmeasured differences between controls and treatment. Parallel trends are not
proven. Results support a controlled trial, not a definitive causal ROI claim.

## Correlation and statistical analysis

Store-month KPI correlations show relationships with profitability. Labour rates,
margin and productivity share accounting components and denominators: strong
correlations are partly mechanical, not independent causal effects.

Staffing pressure and satisfaction are residualised against restaurant, weekday,
calendar month and log order volume using ridge regression. Residual correlation
is accompanied by an approximate store-cluster bootstrap interval (400 samples)
with fixed residuals. This reduces some confounding but does not address all
endogeneity, model uncertainty or selective survey response. Days require at
least three answered surveys. No unsupported significance or causal claim is made.

## Forecasting

Business question: what daily restaurant revenue should management expect over
the next 28 days? Models are a weekly seasonal naive benchmark, standardised
calendar/lag ridge regression, and a histogram gradient-boosting challenger.
Features include restaurant and weekday effects, location-sensitive weekend
interactions, annual seasonality, time trend, public holidays, lag-7, lag-28 and
the prior 28-day mean.

Three consecutive 28-day validation windows precede a final untouched 28-day
holdout. The smallest mean validation MAE selects the model; holdout scores do
not change selection. Future lag features are updated recursively from predictions,
not future actuals. Known calendar values are allowed; future promotion uplift,
staffing changes and customer outcomes are not assumed known.

MAE, RMSE, MAPE and WAPE are reported. Final refitting uses all observed history.
Approximate 80% bands use per-store absolute validation-error quantiles from
84 validation observations per restaurant (three folds × 28 dates);
holdout coverage is reported for the selected model. They are empirical planning
ranges, not guaranteed probabilities. Store bounds are not summed to create
chain intervals. Forecast dates in January 2026 are a historical synthetic
continuation, not predictions for today's real-world calendar.

## Risks and next steps

| Risk | Implication | Practical next step |
|---|---|---|
| Synthetic data | Results reflect constructed mechanisms | Revalidate with authorised real sources before business use |
| Missing factors | Weather, events and stock-outs are absent | Add operational context and intervention logging |
| Incomplete baskets excluded | A small reduction in measured demand | Monitor rejection coverage and correct source exports |
| Survey selection | Respondents may not represent all guests | Track response coverage and compare channels |
| Customer identification | Anonymous and cross-store visits are missed | Establish reliable identity and consent rules in a real system |
| Capacity assumption | Pressure does not prove staffing need | Conduct service-time observation and manager review |
| Promotion confounding | Estimated uplift may be biased | Randomise a future store trial |
| Small store sample | Clustering may be unstable | Review against location peers and rerun sensitivity checks |
| Index judgement | Ranking depends on thresholds and weights | Agree weights with stakeholders; retain component detail |
| Forecast drift | Menu/channel/operational changes may alter demand | Monitor weekly accuracy and record overrides |
| CSV floating-point money | Tiny binary representation differences | Reconcile with cent-level tolerances; use decimal finance types in production |

The project deliberately keeps algorithms understandable. Forecasts and
segmentation serve named decisions; model complexity is not an objective.
