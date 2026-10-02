# Data dictionary

**Company:** Southern Table Hospitality (fictional). **Currency:** AUD. **Dates:** local ISO dates; money excludes GST except `gst_amount`. Ratios are 0–1 unless stated otherwise.

Tables are generated for 2024–2025. Cleaned source tables preserve source grain; derived fields are marked by their definitions. Primary keys must be unique/non-null. Restaurant/product foreign keys must resolve. Anonymous customer IDs, non-promoted campaign IDs, unanswered survey scores and optional order links can be null.

## restaurants.csv

**Grain:** One restaurant. **Primary key:** `restaurant_id`.

| Field | Definition / units |
|---|---|
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `restaurant_name` | Canonical restaurant display name; cleaned from the restaurant master |
| `state` | NSW, VIC or QLD; determines state calendar and timezone |
| `location_type` | CBD, Suburban, Shopping centre or Regional peer group |
| `area` | Fictional management area: East, South or North |
| `timezone` | IANA timezone for local POS and roster timestamps |
| `seats` | Simulated dining capacity; seats |
| `opening_date` | Restaurant opening date; ISO date |
| `open_hour` | Local opening hour, inclusive |
| `close_hour` | Local closing hour, exclusive |

## products.csv

**Grain:** One menu product. **Primary key:** `product_id`.

| Field | Definition / units |
|---|---|
| `product_id` | Stable product foreign key; primary key in product master |
| `product_name` | Menu item name validated against the approved category taxonomy |
| `category` | Canonical category: Mains, Salads, Sides, Drinks or Desserts |
| `menu_price_ex_gst` | 2024 base unit menu price; AUD excluding GST |
| `standard_ingredient_cost` | 2024 base unit ingredient cost; AUD |

## transactions.csv

**Grain:** One product line in a complete customer order. **Primary key:** `transaction_line_id`.

| Field | Definition / units |
|---|---|
| `transaction_line_id` | Unique exported POS product-line key |
| `order_id` | Basket identifier; multiple lines belong to one order; optional for enrolment/unlinked surveys |
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `restaurant_name` | Canonical restaurant display name; cleaned from the restaurant master |
| `timestamp_local` | Store-local order timestamp, YYYY-MM-DD HH:MM:SS; interpret with restaurant timezone |
| `product_id` | Stable product foreign key; primary key in product master |
| `quantity` | Units sold on the line; validated range 1–20 |
| `channel` | Dine-in, Takeaway or Delivery |
| `customer_id` | Anonymous store-local customer identifier; null means unidentified order |
| `promotion_id` | Campaign foreign key; null means no attributed campaign |
| `list_revenue` | Line quantity × sale-time menu price before discount; AUD excluding GST |
| `discount_amount` | Line or order discount already deducted from revenue; AUD excluding GST |
| `net_revenue` | Line sales after discount; AUD excluding GST |
| `gst_amount` | Simplified tax component: 10% of net line revenue; AUD |
| `ingredient_cost` | Sale-time ingredient cost for sold units; excludes waste; AUD |
| `business_date` | Local trading date, ISO YYYY-MM-DD |
| `month` | YYYY-MM for facts/budgets; integer 1–12 only in calendar |
| `hour` | Local order hour, 11–21 |
| `daypart` | Lunch 11:00–15:59, Dinner 16:00–21:59 |

## labour.csv

**Grain:** One employee shift. **Primary key:** `shift_id`.

| Field | Definition / units |
|---|---|
| `shift_id` | Unique employee shift key |
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `employee_id` | Fictional employee identifier; no personal data |
| `role` | Service, Kitchen or Manager |
| `business_date` | Local trading date, ISO YYYY-MM-DD |
| `daypart` | Lunch 11:00–15:59, Dinner 16:00–21:59 |
| `scheduled_start` | Planned shift start in local time |
| `scheduled_end` | Planned shift end in local time |
| `actual_start` | Observed shift start in local time; scheduled=actual in this simulation |
| `actual_end` | Observed shift end in local time |
| `break_hours` | Unpaid break duration; hours |
| `paid_hours` | Actual shift duration less unpaid breaks; hours |
| `hourly_cost` | Simulated loaded cost for role and weekend/holiday class; AUD/hour |
| `rate_imputed` | 1 if hourly cost inferred from comparable valid shifts; otherwise 0 |
| `labour_cost` | Paid hours × loaded hourly cost; AUD |

## customer_feedback.csv

**Grain:** One survey submission. **Primary key:** `feedback_id`.

| Field | Definition / units |
|---|---|
| `feedback_id` | Unique survey submission key |
| `order_id` | Basket identifier; multiple lines belong to one order; optional for enrolment/unlinked surveys |
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `business_date` | Local trading date, ISO YYYY-MM-DD |
| `overall_score` | Overall satisfaction 1–5; null for unanswered or invalid rating |
| `food_score` | Food satisfaction integer 1–5 |
| `service_score` | Service satisfaction integer 1–5 |

## loyalty.csv

**Grain:** One identified-customer loyalty event. **Primary key:** `loyalty_event_id`.

| Field | Definition / units |
|---|---|
| `loyalty_event_id` | Unique loyalty event key |
| `customer_id` | Anonymous store-local customer identifier; null means unidentified order |
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `order_id` | Basket identifier; multiple lines belong to one order; optional for enrolment/unlinked surveys |
| `event_date` | Local event date; ISO YYYY-MM-DD |
| `event_type` | Enroll, Earn or Redeem; redemption is behavioural, not an extra monetary discount |
| `points` | Points earned (positive), redeemed (negative), or zero on enrolment; no currency conversion |

## promotions.csv

**Grain:** One campaign at one restaurant. **Primary key:** `promotion_id`.

| Field | Definition / units |
|---|---|
| `promotion_id` | Campaign foreign key; null means no attributed campaign |
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `campaign_name` | Local Lunch, Winter Value or Spring Social |
| `start_date` | Campaign or assignment effective start, inclusive; ISO date |
| `end_date` | Campaign or assignment effective end, inclusive; ISO date |
| `discount_rate` | Fraction of pre-discount sales; 0.10 means 10% |
| `eligible_category` | All in this version; campaign applies to every product |
| `campaign_cost` | Unique campaign/store spend, or allocated daily campaign spend in marts; AUD |

## waste.csv

**Grain:** One restaurant/product/date waste record. **Primary key:** `waste_id`.

| Field | Definition / units |
|---|---|
| `waste_id` | Unique waste ledger key |
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `product_id` | Stable product foreign key; primary key in product master |
| `business_date` | Local trading date, ISO YYYY-MM-DD |
| `waste_units` | Discarded product-equivalent units; non-negative count |
| `waste_cost` | Discarded unit ingredient cost at period prices; AUD |
| `reason` | Over-preparation, Spoilage or Preparation error; illustrative classification |

## targets.csv

**Grain:** One restaurant/month budget. **Primary key:** `restaurant_id, month`.

| Field | Definition / units |
|---|---|
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `month` | YYYY-MM for facts/budgets; integer 1–12 only in calendar |
| `revenue_target` | Independent restaurant/month revenue budget; AUD excluding GST |
| `operating_margin_target` | Budget operating margin fraction |
| `labour_pct_target` | Maximum desired labour-cost/revenue fraction |
| `waste_pct_target` | Desired waste/(sold ingredient cost + waste) fraction |
| `satisfaction_target` | Desired mean score on the 1–5 scale |

## operating_costs.csv

**Grain:** One restaurant/month/cost-category ledger entry. **Primary key:** `cost_id`.

| Field | Definition / units |
|---|---|
| `cost_id` | Unique operating-cost ledger key |
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `month` | YYYY-MM for facts/budgets; integer 1–12 only in calendar |
| `cost_category` | Rent, Utilities or Other overhead; labour/ingredients excluded to prevent duplication |
| `amount` | Monthly operating-cost amount; AUD |

## delivery.csv

**Grain:** One completed delivery order. **Primary key:** `order_id`.

| Field | Definition / units |
|---|---|
| `order_id` | Basket identifier; multiple lines belong to one order; optional for enrolment/unlinked surveys |
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `promised_minutes` | Promised delivery time from order; minutes |
| `actual_minutes` | Observed simulated delivery time; minutes |
| `commission_cost` | Platform commission at 25% of net delivery sales; AUD |
| `delivery_fee` | Restaurant-collected fee; zero in this simulation |
| `status` | Completed; cancellations are not simulated |

## calendar.csv

**Grain:** One state/date. **Primary key:** `business_date, state`.

| Field | Definition / units |
|---|---|
| `business_date` | Local trading date, ISO YYYY-MM-DD |
| `state` | NSW, VIC or QLD; determines state calendar and timezone |
| `holiday_name` | State public holiday label from holidays package; blank on ordinary dates |
| `is_public_holiday` | 1 for public holiday, else 0 |
| `weekday` | Monday=0 through Sunday=6 |
| `is_weekend` | 1 for Saturday/Sunday, else 0 |
| `month` | YYYY-MM for facts/budgets; integer 1–12 only in calendar |
| `season` | Australian meteorological season: Summer, Autumn, Winter or Spring |
| `school_holiday_proxy` | Illustrative seasonal proxy, not an official school calendar; 0/1 |

## manager_assignments.csv

**Grain:** One manager/store effective period. **Primary key:** `restaurant_id, start_date`.

| Field | Definition / units |
|---|---|
| `restaurant_id` | Stable restaurant foreign key (1–18); primary key in the restaurant master |
| `manager_id` | Anonymous simulated manager; one per store, so manager effect is not separately identifiable |
| `start_date` | Campaign or assignment effective start, inclusive; ISO date |
| `end_date` | Campaign or assignment effective end, inclusive; ISO date |

## Analytical tables

| File | Grain | Important semantics |
|---|---|---|
| orders | Complete order | Revenue and ingredient cost sum the full basket; channel and customer are consistent across lines |
| store_day | Restaurant/business date | Independent fact aggregates; daily fixed-cost allocations; score sum and answer count support weighting |
| store_hour | Restaurant/business date/hour | Uniform paid-time allocation; six orders/service-hour capacity; Pressure/Spare capacity/Balanced are modelled flags |
| store_month_kpis | Restaurant/month | Additive finance + recalculated rates, budgets, growth, index components and completeness |
| product_month | Restaurant/month/product/channel | Orders-with-product is not additive across products; gross contribution excludes labour |
| customer_segments | Identified customer/snapshot | Recency in days, frequency in distinct visit dates, monetary spend in AUD; eligibility and return flags |
| customer_cohorts | Restaurant/first-observed month | Eligible 90-day denominator and returning customer numerator |
| loyalty_behaviours | Early activity band/redemption flag | Early behaviour days 0–30; return outcome days 31–90 |
| store_segments | Restaurant/full history | Standardised K-means features; exploratory three-cluster label |
| promotion_effectiveness | Campaign/store | Observed and counterfactual revenue, controls, net incremental contribution, ROI fraction, approximate 95% ranges |
| sales_anomalies | Flagged restaurant/date | Prior weekday median, robust z-score, holiday/campaign context |
| staffing_patterns | Restaurant/weekday/hour | Average demand/capacity and pressure/spare counts over observed hours |
| latest_store_opportunities | Restaurant/Q4 2025 | Weighted finance, mean monthly index, location-peer waste median and hypothetical waste-cost gap |
| forecast_daily | Restaurant/future date | Predicted AUD revenue, horizon 1–28, origin, selected model and approximate empirical lower/upper 80% bands |
| forecast_backtests | Restaurant/date/model/origin | Actual/predicted AUD, Validation/Holdout, fold; holdout bands use selected-model validation errors |
| forecast_metrics | Evaluation period/fold/model | MAE/RMSE AUD; MAPE/WAPE in 0–100 percentage units; selected-model holdout coverage fraction |

Analytical KPI definitions are in `kpi_definitions.md`; uncertainty, segmentation thresholds and assumptions are in `methodology.md`. `quality_reason` is the rejection explanation in quarantine exports. Null derived rates mean no valid denominator, not zero performance.
