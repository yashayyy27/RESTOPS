"""Transparent, single-period restaurant profit scenarios (not forecasts)."""

from dataclasses import asdict, dataclass, replace

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Scenario:
    """Changes are fractions; discount and waste are replacement absolute rates."""

    hours_change: float = 0.0
    wage_change: float = 0.0
    price_change: float = 0.0
    demand_change: float = 0.0
    discount_rate: float | None = None
    waste_rate: float | None = None


def simulate(baseline, assumptions=Scenario()):
    """Preserve the cost ledger while applying explicit independent drivers.

    Ingredient cost measures food sold. Waste is additional discarded food, so
    total COGS = ingredient cost + waste. Discounts are already in net revenue.
    Labour hours and wage changes multiply; labour is fixed for break-even at
    the chosen staffing level. Channel mix, ingredient unit costs, overheads
    and campaign spend stay constant. Price elasticity is supplied as demand.
    """
    b = dict(baseline)
    required = [
        "revenue",
        "discounts",
        "transactions",
        "ingredient_cost",
        "waste_cost",
        "labour_cost",
        "paid_hours",
        "commission_cost",
        "overhead_cost",
        "campaign_cost",
    ]
    if any(k not in b or not np.isfinite(b[k]) or b[k] < 0 for k in required):
        raise ValueError("Baseline requires finite non-negative ledger inputs")
    if b["revenue"] <= 0 or b["transactions"] <= 0 or b["paid_hours"] <= 0:
        raise ValueError("Scenario requires positive revenue, orders and paid hours")
    for key in ("hours_change", "wage_change", "price_change", "demand_change"):
        value = getattr(assumptions, key)
        if not np.isfinite(value) or not -1 < value <= 2:
            raise ValueError(f"{key} must be greater than -100% and at most +200%")
    list_sales = b["revenue"] + b["discounts"]
    discount = b["discounts"] / list_sales
    food = b["ingredient_cost"] + b["waste_cost"]
    waste = b["waste_cost"] / food if food else 0.0
    discount = (
        discount if assumptions.discount_rate is None else assumptions.discount_rate
    )
    waste = waste if assumptions.waste_rate is None else assumptions.waste_rate
    if not np.isfinite(discount) or not 0 <= discount < 1:
        raise ValueError("Discount must be from 0% to below 100%")
    if not np.isfinite(waste) or not 0 <= waste < 1:
        raise ValueError("Waste must be from 0% to below 100%")
    volume = 1 + assumptions.demand_change
    orders = b["transactions"] * volume
    gross_sales = list_sales * volume * (1 + assumptions.price_change)
    revenue = gross_sales * (1 - discount)
    ingredients = b["ingredient_cost"] * volume
    waste_cost = ingredients * waste / (1 - waste)
    hours = b["paid_hours"] * (1 + assumptions.hours_change)
    wage = b["labour_cost"] / b["paid_hours"] * (1 + assumptions.wage_change)
    labour = hours * wage
    # Preserve observed delivery mix and commission rate, charged on net sales.
    commission = revenue * b["commission_cost"] / b["revenue"]
    cogs = ingredients + waste_cost
    contribution = revenue - cogs - commission - labour - b["campaign_cost"]
    profit = contribution - b["overhead_cost"]
    variable_per_order = (cogs + commission) / orders
    net_per_order = revenue / orders
    unit_contribution = net_per_order - variable_per_order
    fixed = labour + b["overhead_cost"] + b["campaign_cost"]
    break_even_orders = fixed / unit_contribution if unit_contribution > 0 else np.nan
    return {
        "revenue": revenue,
        "discounts": gross_sales * discount,
        "transactions": orders,
        "ingredient_cost": ingredients,
        "waste_cost": waste_cost,
        "cogs": cogs,
        "paid_hours": hours,
        "loaded_hourly_wage": wage,
        "labour_cost": labour,
        "commission_cost": commission,
        "campaign_cost": b["campaign_cost"],
        "overhead_cost": b["overhead_cost"],
        "operating_contribution": contribution,
        "operating_profit": profit,
        "operating_margin_pct": profit / revenue,
        "break_even_orders": break_even_orders,
        "break_even_revenue": break_even_orders * net_per_order,
        "discount_rate": discount,
        "waste_rate": waste,
    }


def compare(baseline, assumptions):
    """Return auditable baseline/scenario/delta values at the same period grain."""
    before, after = simulate(baseline), simulate(baseline, assumptions)
    return pd.DataFrame(
        {
            "metric": list(before),
            "baseline": list(before.values()),
            "scenario": list(after.values()),
        }
    ).assign(delta=lambda frame: frame.scenario - frame.baseline)


def sensitivity(baseline, assumptions, width=0.10):
    """Demand uncertainty only; each row is a scenario, not a probability band."""
    if not 0 <= width <= 0.50:
        raise ValueError("Sensitivity width must be between 0% and 50%")
    rows = []
    for label, factor in [
        ("Downside", 1 - width),
        ("Central", 1),
        ("Upside", 1 + width),
    ]:
        case = replace(
            assumptions, demand_change=(1 + assumptions.demand_change) * factor - 1
        )
        rows.append({"case": label, **asdict(case), **simulate(baseline, case)})
    return pd.DataFrame(rows)
