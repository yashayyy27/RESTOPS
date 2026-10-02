"""Prepare typed snapshot data for the optional native Excel export builder."""

import json

import pandas as pd

from .common import REPORTS


def run():
    weekly = pd.read_csv(REPORTS / "exports/weekly_performance.csv")
    labour = pd.read_csv(REPORTS / "exports/labour_plan.csv")
    daily = (
        labour.groupby(["restaurant_id", "business_date"])
        .agg(
            restaurant=("restaurant_name", "first"),
            orders=("forecast_orders", "sum"),
            suggested_hours=("suggested_paid_hours", "sum"),
            template_hours=("scheduled_paid_hours", "sum"),
            suggested_cost=("suggested_labour_cost", "sum"),
            budget_difference=("budget_difference", "sum"),
        )
        .reset_index()
    )
    comparison = pd.read_csv(REPORTS / "exports/scenario_comparison.csv")
    payload = {
        "window_start": weekly.window_start.iloc[0],
        "window_end": weekly.window_end.iloc[0],
        "weekly_headers": [
            "Restaurant",
            "Revenue AUD",
            "Profit AUD",
            "Margin",
            "Labour %",
            "Waste %",
            "Target %",
            "Orders",
            "Revenue growth",
        ],
        "weekly": json.loads(
            weekly[
                [
                    "restaurant_name",
                    "revenue",
                    "operating_profit",
                    "operating_margin_pct",
                    "labour_cost_pct",
                    "waste_pct",
                    "target_achievement_pct",
                    "transactions",
                    "revenue_growth",
                ]
            ].to_json(orient="values")
        ),
        "labour_headers": [
            "Restaurant ID",
            "Date",
            "Restaurant",
            "Expected orders",
            "Suggested hours",
            "Template hours",
            "Suggested cost AUD",
            "Cost difference AUD",
        ],
        "labour": json.loads(daily.to_json(orient="values")),
        "scenario_headers": [
            "Metric",
            "Observed baseline",
            "Scenario estimate",
            "Difference",
        ],
        "scenario": json.loads(comparison.to_json(orient="values")),
        "scenario_note": "Wollongong December 2025. Hours -5%, demand -2%, waste share 4%. Other drivers unchanged. Estimates, not forecasts.",
        "forecast_origin": labour.origin_date.iloc[0],
    }
    (REPORTS / "exports/excel_pack_inputs.json").write_text(
        json.dumps(payload, indent=2)
    )


if __name__ == "__main__":
    run()
