# KPI definitions

All financial values are AUD excluding GST. Completed orders are the only order
status simulated. Refund/cancellation economics are outside this version.

| KPI | Formula | Grain / interpretation |
|---|---|---|
| Revenue | Sum of line net revenue | Discounts already subtracted; do not subtract them twice |
| Revenue growth | Current / comparable previous revenue − 1 | Store-month MoM and YoY; first periods are undefined |
| Transactions | Count of distinct complete order IDs | Product-line count is not order count |
| Average transaction value | Revenue / transactions | Recalculate for selected population |
| Gross contribution | Revenue − ingredient cost of sold items | Before labour, waste, overhead and commissions |
| Gross margin % | Gross contribution / revenue | Ingredient cost of sold items excludes discarded stock |
| Operating profit | Revenue − sold ingredient cost − waste − labour − commissions − overheads − campaign cost | Full observed operating cost bridge |
| Operating margin % | Operating profit / revenue | Negative values retained |
| Labour cost % | Loaded labour cost / revenue | Simulated rates include role/weekend/holiday differences |
| Sales per labour hour | Revenue / actual paid hours | All roles; breaks excluded |
| Transactions per labour hour | Transactions / actual paid hours | All roles; not the service capacity benchmark |
| Waste % | Waste cost / (sold ingredient cost + waste cost) | Approximation to food input utilisation; not waste/revenue |
| Satisfaction | Sum of answered overall scores / answer count | 1–5; null responses excluded; sample size displayed |
| 90-day repeat rate | Eligible identified customers returning on another day within 90 days / eligible identified customers | First observed visit; complete follow-up required |
| Promotion ROI | Estimated incremental contribution after campaign spending / campaign spending | Exploratory counterfactual; denominator zero is undefined |
| Target achievement % | Revenue / budget revenue | Targets are independent simulation budgets |
| MAE | Mean absolute actual-minus-predicted error | AUD per restaurant/day |
| RMSE | Square root of mean squared error | Penalises larger misses |
| MAPE | Mean absolute error / positive actual × 100 | Zero actuals excluded; percentage units |
| WAPE | Sum absolute errors / sum actual × 100 | Supplementary chain-weighted forecast error |
| Late delivery % | Completed deliveries exceeding promised minutes / completed deliveries | Delivery orders only |

## Restaurant Performance Index

Five bounded component scores, each from 0 to 100:

- Revenue: `100 × revenue / revenue_target`, capped at 100.
- Margin: `100 × operating_margin / margin_target`, clipped to 0–100.
- Labour: `100 × target_labour_pct / actual_labour_pct`, clipped to 0–100.
- Waste: `100 × target_waste_pct / actual_waste_pct`, clipped to 0–100; zero waste scores 100.
- Satisfaction: `100 × satisfaction / satisfaction_target`, clipped to 0–100.

Weights are 25%, 25%, 20%, 15% and 15%, respectively. The index is undefined
when a component is missing; `index_complete` exposes coverage. Targets are
assumed positive. A quarterly overview shows the mean of monthly index scores,
labelled as such; it is not a newly recomputed quarterly index.

Weights are judgement-based for a portfolio demonstration and are not validated
management preferences. The index is a navigation aid, not an instruction to cut
labour. Component saturation can conceal outperformance, so underlying rates
and amounts remain visible.

## Aggregation rules

Sum additive numerators and denominators before division. Do not average store
margins, transaction values, waste rates or satisfaction means. Do not sum
`orders_with_product` across products or categories. Customer rates use cohort
denominators, not survey respondents or POS lines. Zero denominators yield null.
