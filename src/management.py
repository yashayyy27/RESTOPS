"""Reconciled restaurant investigation and weekly management decisions."""

import numpy as np
import pandas as pd

from .kpi_engine import ADDITIVE, calculate

COSTS = [
    "ingredient_cost",
    "waste_cost",
    "labour_cost",
    "commission_cost",
    "overhead_cost",
    "campaign_cost",
]


def aggregate(daily):
    """Recalculate rates from period totals; never average financial ratios."""
    if daily.empty:
        raise ValueError("No observations in the selected period")
    return calculate(pd.DataFrame([daily[ADDITIVE].sum()])).iloc[0]


def revenue_bridge(before, after):
    """Exact two-factor decomposition; interaction assigned to basket value."""
    if before["transactions"] <= 0 or after["transactions"] <= 0:
        raise ValueError("Both bridge periods require positive order counts")
    atv0 = before["revenue"] / before["transactions"]
    atv1 = after["revenue"] / after["transactions"]
    return pd.DataFrame(
        [
            {
                "driver": "Order volume",
                "amount": (after["transactions"] - before["transactions"]) * atv0,
            },
            {
                "driver": "Basket value (net)",
                "amount": (atv1 - atv0) * after["transactions"],
            },
        ]
    )


def profit_bridge(before, after):
    """Revenue drivers + each observed cost change reconcile to profit change."""
    rows = revenue_bridge(before, after).to_dict("records")
    rows += [
        {"driver": name.replace("_", " ").title(), "amount": before[name] - after[name]}
        for name in COSTS
    ]
    result = pd.DataFrame(rows)
    expected = after["operating_profit"] - before["operating_profit"]
    if not np.isclose(result.amount.sum(), expected, atol=0.01, rtol=0):
        raise ValueError("Profit bridge does not reconcile to the ledger")
    return result


def weekly_scorecard(daily, monthly, end=None):
    """Rolling seven-day comparison; monthly targets prorated by calendar days."""
    end = pd.Timestamp(end or daily.business_date.max())
    dates = pd.to_datetime(daily.business_date)
    frames = []
    for period, start, stop in [
        ("current", end - pd.Timedelta(days=6), end),
        ("previous", end - pd.Timedelta(days=13), end - pd.Timedelta(days=7)),
    ]:
        part = daily.loc[dates.between(start, stop)].copy()
        if (
            part.groupby("restaurant_id")
            .business_date.nunique()
            .reindex(daily.restaurant_id.unique(), fill_value=0)
            .ne(7)
            .any()
            or part.empty
        ):
            raise ValueError(
                "Each selected restaurant needs two complete seven-day windows"
            )
        target = monthly[["restaurant_id", "month", "revenue_target"]].copy()
        part = part.merge(target, on=["restaurant_id", "month"], validate="many_to_one")
        if part.revenue_target.isna().any():
            raise ValueError("Monthly target missing for a reporting date")
        part["allocated_revenue_target"] = (
            part.revenue_target / pd.to_datetime(part.business_date).dt.days_in_month
        )
        grouped = (
            part.groupby("restaurant_id")[ADDITIVE + ["allocated_revenue_target"]]
            .sum()
            .reset_index()
        )
        grouped = calculate(grouped)
        names = part[
            ["restaurant_id", "restaurant_name", "state", "area"]
        ].drop_duplicates()
        grouped = grouped.merge(names, on="restaurant_id", validate="one_to_one")
        grouped["window_start"], grouped["window_end"] = start.strftime(
            "%Y-%m-%d"
        ), stop.strftime("%Y-%m-%d")
        grouped["period"] = period
        frames.append(grouped)
    current, previous = frames
    previous = previous.rename(
        columns={c: "prior_" + c for c in previous if c != "restaurant_id"}
    )
    result = current.merge(previous, on="restaurant_id", validate="one_to_one")
    result["revenue_change"] = result.revenue - result.prior_revenue
    result["profit_change"] = result.operating_profit - result.prior_operating_profit
    result["revenue_growth"] = result.revenue_change / result.prior_revenue.replace(
        0, np.nan
    )
    result["target_gap"] = result.revenue - result.allocated_revenue_target
    result["target_achievement_pct"] = result.revenue / result.allocated_revenue_target
    return result.sort_values("operating_margin_pct").reset_index(drop=True)


def weekly_brief(scorecard):
    """Compute a prioritised decision register with traceable, conditional impact."""
    rows = []
    for r in scorecard.itertuples():
        # Largest adverse ledger movement supports a plausible investigation.
        changes = {
            name: getattr(r, name) - getattr(r, "prior_" + name) for name in COSTS
        }
        driver = max(changes, key=changes.get)
        prior_food = r.prior_ingredient_cost + r.prior_waste_cost
        prior_waste = r.prior_waste_cost / prior_food if prior_food else np.nan
        excess_waste = (
            max(0, r.waste_cost - r.ingredient_cost * prior_waste / (1 - prior_waste))
            if np.isfinite(prior_waste) and prior_waste < 1
            else 0
        )
        labour_share_gap = max(0, r.labour_cost - r.revenue * r.prior_labour_cost_pct)
        if excess_waste >= labour_share_gap and excess_waste > 0:
            action, owner = (
                "Trial smaller preparation batches; monitor stock-outs alongside waste.",
                "Restaurant Manager",
            )
            impact, measure = (
                excess_waste,
                "Waste % vs prior week; stock-outs and satisfaction stable",
            )
            basis = "Waste cost at the prior week's waste rate, on current sold-ingredient cost"
        else:
            action, owner = (
                "Review meal-peak coverage and trial staggered starts; preserve service guardrails.",
                "Area Manager / Workforce Planning",
            )
            impact, measure = (
                labour_share_gap,
                "Labour cost % vs prior week; peak pressure and satisfaction stable",
            )
            basis = "Labour cost at the prior week's labour/revenue ratio; feasibility untested"
        rows.append(
            {
                "restaurant_id": r.restaurant_id,
                "restaurant_name": r.restaurant_name,
                "window_start": r.window_start,
                "window_end": r.window_end,
                "what_changed": f"Revenue {r.revenue_change:+,.0f} AUD; operating profit {r.profit_change:+,.0f} AUD vs previous seven days",
                "evidence": f"Margin {r.operating_margin_pct:.1%}; target achievement {r.target_achievement_pct:.1%}; {driver} change {changes[driver]:+,.0f} AUD",
                "plausible_explanation": f"Review {driver.replace('_',' ')} and order/basket movements. Ledger movements describe observed drivers, not proven causes.",
                "estimated_weekly_opportunity": impact,
                "impact_assumption": basis,
                "recommended_action": action,
                "proposed_owner": owner,
                "success_measure": measure,
                "priority": (
                    "High"
                    if r.target_gap < 0 or r.operating_margin_pct < 0.10
                    else "Review"
                ),
                "source": "store_day; store_month_kpis; preceding seven-day comparison",
            }
        )
    return pd.DataFrame(rows)
