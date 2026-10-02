"""Shared KPI formulas and a transparent, bounded performance index."""

import numpy as np

from .common import PROCESSED, TABLEAU, config, ratio, read, save

ADDITIVE = [
    "revenue",
    "ingredient_cost",
    "transactions",
    "discounts",
    "identified_orders",
    "labour_cost",
    "paid_hours",
    "service_hours",
    "waste_cost",
    "score_sum",
    "survey_responses",
    "commission_cost",
    "deliveries",
    "late_deliveries",
    "overhead_cost",
    "campaign_cost",
    "operating_profit",
]


def calculate(frame):
    """Calculate rates from aggregated numerators and denominators."""
    result = frame.copy()
    result["gross_contribution"] = result.revenue - result.ingredient_cost
    result["average_transaction_value"] = ratio(result.revenue, result.transactions)
    result["gross_margin_pct"] = ratio(result.gross_contribution, result.revenue)
    result["operating_margin_pct"] = ratio(result.operating_profit, result.revenue)
    result["labour_cost_pct"] = ratio(result.labour_cost, result.revenue)
    result["sales_per_labour_hour"] = ratio(result.revenue, result.paid_hours)
    result["transactions_per_labour_hour"] = ratio(
        result.transactions, result.paid_hours
    )
    result["waste_pct"] = ratio(
        result.waste_cost, result.ingredient_cost + result.waste_cost
    )
    result["satisfaction_score"] = ratio(result.score_sum, result.survey_responses)
    result["identified_order_share"] = ratio(
        result.identified_orders, result.transactions
    )
    result["late_delivery_pct"] = ratio(result.late_deliveries, result.deliveries)
    return result


def run():
    """Write monthly KPIs and score components for Tableau."""
    monthly = (
        read("store_day")
        .groupby(["restaurant_id", "month"])[ADDITIVE]
        .sum()
        .reset_index()
    )
    monthly = calculate(monthly).merge(
        read("targets"), on=["restaurant_id", "month"], validate="one_to_one"
    )
    monthly = monthly.merge(
        read("restaurants"), on="restaurant_id", validate="many_to_one"
    )
    monthly = monthly.sort_values(["restaurant_id", "month"])
    monthly["revenue_growth_mom"] = monthly.groupby("restaurant_id").revenue.pct_change(
        fill_method=None
    )
    monthly["revenue_growth_yoy"] = monthly.groupby("restaurant_id").revenue.pct_change(
        periods=12, fill_method=None
    )
    monthly["target_achievement_pct"] = ratio(monthly.revenue, monthly.revenue_target)
    # 100 at target; linear shortfall penalties. Every score is visible.
    monthly["score_revenue"] = (100 * monthly.target_achievement_pct).clip(0, 100)
    monthly["score_margin"] = (
        100 * ratio(monthly.operating_margin_pct, monthly.operating_margin_target)
    ).clip(0, 100)
    monthly["score_labour"] = (
        100 * ratio(monthly.labour_pct_target, monthly.labour_cost_pct)
    ).clip(0, 100)
    monthly["score_waste"] = np.where(
        monthly.waste_pct.eq(0),
        100,
        100 * ratio(monthly.waste_pct_target, monthly.waste_pct),
    )
    monthly["score_waste"] = monthly.score_waste.clip(0, 100)
    monthly["score_satisfaction"] = (
        100 * ratio(monthly.satisfaction_score, monthly.satisfaction_target)
    ).clip(0, 100)
    weights = config()["index_weights"]
    if not np.isclose(sum(weights.values()), 1):
        raise ValueError("Performance index weights must sum to one")
    components = [f"score_{name}" for name in weights]
    monthly["index_complete"] = monthly[components].notna().all(axis=1)
    monthly["performance_index"] = sum(
        monthly[f"score_{key}"] * weight for key, weight in weights.items()
    ).where(monthly.index_complete)
    save(monthly, PROCESSED / "store_month_kpis.csv")
    save(monthly, TABLEAU / "store_month_kpis.csv")
    save(monthly, PROCESSED.parent.parent / "reports/exports/store_month_kpis.csv")
    print("Calculated monthly KPIs and Restaurant Performance Index.", flush=True)
    return monthly


if __name__ == "__main__":
    run()
