# Scenario and labour planning methodology

All data, wage rates, productivity and treatment mechanisms are synthetic.
Estimates answer operational questions and are not forecasts or legal rosters.

## Profit scenario

Baseline grain: one selected restaurant / observed calendar month. Inputs are
additive ledger amounts from `store_day`. All currency excludes GST.

Let list sales L = net revenue R + discounts D, orders N, sold-ingredient cost I,
waste W, labour cost B, paid hours H, commissions C, overheads O and campaign spend M.
Let demand change v, price change p, hours change h and loaded-wage change w.
Discount d and waste share q are replacement absolute rates, not additive changes.

```text
Baseline discount = D / L
Baseline waste share = W / (I + W)
Scenario orders = N × (1 + v)
Scenario list sales = L × (1 + v) × (1 + p)
Scenario revenue = scenario list sales × (1 − d)
Scenario sold-ingredient cost = I × (1 + v)
Scenario waste = scenario sold-ingredient cost × q / (1 − q)
Scenario COGS = scenario sold-ingredient cost + scenario waste
Scenario hours = H × (1 + h)
Scenario loaded wage = (B / H) × (1 + w)
Scenario labour = scenario hours × scenario loaded wage
Scenario commissions = scenario revenue × (C / R)
Operating contribution = revenue − COGS − commissions − labour − M
Operating profit = operating contribution − O
Operating margin = operating profit / revenue
```

Discounts reduce revenue once. Waste is included in COGS once. The legacy
ingredient gross-margin KPI excludes discarded food; it is explicitly different
from total-food COGS in scenarios. Overheads and campaign costs remain fixed.
Ingredient unit cost and channel mix remain unchanged. Independent demand inputs
represent assumed price response or service response; no elasticity is inferred.

Break-even fixes the chosen hours/wages, overhead and campaign cost for this
period. Variable food and commission cost per order stay constant:

```text
Contribution per order = (revenue − COGS − commissions) / scenario orders
Fixed period costs = scenario labour + overhead + campaign spend
Break-even orders = fixed period costs / contribution per order
Break-even revenue = break-even orders × scenario net revenue per order
```

Non-positive unit contribution gives no finite break-even. Capacity ceilings,
overtime, step costs, tax/cash-flow and multi-product elasticity are absent.
Demand sensitivity multiplies the scenario order volume by (1 ± user range),
keeping staffing fixed. It is an assumption range, not a probability interval.

## Hourly labour planning

Daily forecasts are generated at a single origin after model selection from
chronological validation. Revenue is divided by the restaurant's prior 84-day
same-weekday net basket value to estimate daily orders. Prior same-weekday hourly
order shares allocate those orders to 11:00–21:00. Every shaping observation is
at or before the forecast origin.

```text
Hourly orders = daily forecast revenue / reference net basket value × hour share
Effective service productivity = orders per service hour × target utilisation
Suggested service staff-hours = max(minimum staff, CEILING(hourly orders / productivity))
Suggested paid hours = suggested service hours + reference non-service hours
Budget difference = (suggested paid hours − scheduled template hours) × loaded wage
```

Each row is one hour, so a service headcount equals one paid hour before explicit
shift/break construction. Forecast revenue bounds are transformed using the same
basket/mix assumptions; they exclude basket and intraday allocation uncertainty.

Scheduled hours are the prior 84-day weekday scheduled-shift template, scaled by
the user. Actual hours are recorded separately. Support hours use historical
actual non-service coverage. Scheduled and actual breaks are spread uniformly
within shifts because the data lacks break timing. Zero schedule multiplier
means zero template hours and is preserved rather than replaced by defaults.

Potential under-coverage/spare capacity flags use a ±0.5 service-hour tolerance.
No assumption is made that all spare time can be removed. Skill mix, employment
terms, availability, break rules and service standards require manager review.

## Investigation and weekly decisions

For current/prior periods, N is orders and A is net basket value:

```text
Volume effect = (N_current − N_prior) × A_prior
Basket effect = (A_current − A_prior) × N_current
Revenue movement = volume effect + basket effect
Profit movement = revenue movement − sum(current cost − prior cost)
```

The interaction is assigned to basket value. Product mix and discounts help
interpret that effect but are not counted again. The revenue target has no
order/basket budget; a driver-level actual-versus-budget bridge is unavailable.
Monthly comparisons retain different month lengths. Weekly comparisons use two
complete seven-day windows; monthly revenue targets are allocated by calendar day.

Weekly opportunity examples compare current labour cost with the prior labour /
revenue ratio, or current waste with the prior waste share on current sold-food
cost. They are conditional component comparisons, not causal effects or additive
recoverable profit. Owners and success measures are proposed, not approved.
