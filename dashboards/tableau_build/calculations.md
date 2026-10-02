# Tableau calculations by source

Paste these into their named data sources. Ratios return 0–1; format as %.
Existing forecast score exports use 0–100, so do not format those as a ratio.

`store_month_kpis` (monthly) or `store_day` where inputs exist:

```text
Revenue: SUM([revenue])
Operating Profit: SUM([operating_profit])
Operating Margin: IF SUM([revenue]) != 0 THEN SUM([operating_profit])/SUM([revenue]) END
Labour Cost Share: IF SUM([revenue]) != 0 THEN SUM([labour_cost])/SUM([revenue]) END
Average Basket: IF SUM([transactions]) != 0 THEN SUM([revenue])/SUM([transactions]) END
Waste Share: IF SUM([ingredient_cost])+SUM([waste_cost]) != 0 THEN SUM([waste_cost])/(SUM([ingredient_cost])+SUM([waste_cost])) END
Satisfaction: IF SUM([survey_responses]) != 0 THEN SUM([score_sum])/SUM([survey_responses]) END
```

`store_month_kpis` only:

```text
Target Achievement: IF SUM([revenue_target]) != 0 THEN SUM([revenue])/SUM([revenue_target]) END
Mean Monthly Index: AVG([performance_index])
```

`customer_cohorts`:

```text
Repeat Rate: IF SUM([eligible_customers]) != 0 THEN SUM([repeat_customers])/SUM([eligible_customers]) END
```

`promotion_effectiveness`: filter the ROI card to
`[estimate_status] != 'No eligible control stores'`. This filter must affect
both numerator and denominator, excluding unavailable campaign spend.

```text
Eligible Promotion ROI: IF SUM([campaign_cost]) != 0 THEN SUM([incremental_contribution])/SUM([campaign_cost]) END
```

`forecast_backtests`: filter to one evaluation period, retain model on the view
or filter to one model, and use store filters consistently in all measures.

```text
Absolute Error: ABS([actual_revenue]-[forecast_revenue])
Squared Error: POWER([actual_revenue]-[forecast_revenue],2)
Forecast MAE: AVG([Absolute Error])
Forecast RMSE: SQRT(AVG([Squared Error]))
Forecast WAPE: IF SUM([actual_revenue]) != 0 THEN SUM([Absolute Error])/SUM([actual_revenue]) END
```

`labour_plan`:

```text
Planning Budget Difference: SUM([suggested_labour_cost])-SUM([template_labour_cost])
Service Gap: SUM([suggested_service_hours])-SUM([scheduled_service_hours])
```

Do not sum store forecast bands. Show lower_80/upper_80 only for a single store.
Do not average store WAPE or monthly labour share into a chain ratio. All costs
in the historical profit ledger are already deducted once; waste or discounts
must not be subtracted again in Tableau.
