"""Independent source SQL and time allocations must agree with analytical marts."""

import sqlite3
import unittest

import numpy as np
import pandas as pd

from src.common import PROCESSED, REPORTS, ROOT, read


class ReconciliationTests(unittest.TestCase):
    def test_source_sql_matches_python_kpis(self):
        with sqlite3.connect(PROCESSED / "restops.sqlite") as connection:
            sql = pd.read_sql_query(
                (ROOT / "sql/kpi_queries.sql").read_text(), connection
            )
        python = read("store_month_kpis")
        joined = sql.merge(
            python,
            on=["restaurant_id", "month"],
            suffixes=("_sql", "_python"),
            validate="one_to_one",
        )
        self.assertEqual(len(joined), 18 * 24)
        for field in [
            "revenue",
            "transactions",
            "average_transaction_value",
            "gross_margin_pct",
            "labour_cost_pct",
            "sales_per_labour_hour",
            "waste_pct",
            "satisfaction_score",
            "target_achievement_pct",
        ]:
            np.testing.assert_allclose(
                joined[f"{field}_sql"],
                joined[f"{field}_python"],
                atol=0.0002,
                rtol=1e-8,
            )

    def test_hourly_allocation_reconciles_to_roster(self):
        roster = (
            read("labour")
            .groupby(["restaurant_id", "business_date"])[["paid_hours", "labour_cost"]]
            .sum()
        )
        hourly = (
            read("store_hour")
            .groupby(["restaurant_id", "business_date"])[["paid_hours", "labour_cost"]]
            .sum()
        )
        np.testing.assert_allclose(
            roster.sort_index(), hourly.sort_index(), atol=0.002, rtol=1e-8
        )

    def test_profit_bridge_and_index_bounds(self):
        monthly = read("store_month_kpis")
        costs = monthly[
            [
                "ingredient_cost",
                "waste_cost",
                "labour_cost",
                "commission_cost",
                "overhead_cost",
                "campaign_cost",
            ]
        ].sum(axis=1)
        np.testing.assert_allclose(
            monthly.revenue - costs, monthly.operating_profit, atol=0.001
        )
        self.assertTrue(monthly.performance_index.between(0, 100).all())
        for field in ["revenue", "margin", "labour", "waste", "satisfaction"]:
            self.assertTrue(monthly[f"score_{field}"].between(0, 100).all())
        operating = read("operating_costs").amount.sum()
        self.assertAlmostEqual(operating, monthly.overhead_cost.sum(), places=2)
        self.assertAlmostEqual(
            read("promotions").campaign_cost.sum(),
            monthly.campaign_cost.sum(),
            places=2,
        )

    def test_all_business_queries_and_independent_repeat_rate(self):
        statements, buffer = [], ""
        for line in (
            (ROOT / "sql/business_queries.sql").read_text().splitlines(keepends=True)
        ):
            buffer += line
            if sqlite3.complete_statement(buffer):
                statements.append(buffer)
                buffer = ""
        self.assertEqual(len(statements), 6)
        with sqlite3.connect(PROCESSED / "restops.sqlite") as connection:
            outputs = [
                pd.read_sql_query(statement, connection) for statement in statements
            ]
        self.assertTrue(all(len(frame) > 0 for frame in outputs))
        summary = pd.read_json(REPORTS / "analysis_summary.json", typ="series")
        self.assertEqual(
            int(outputs[4].eligible_customers.iloc[0]), summary.eligible_customers
        )
        self.assertAlmostEqual(
            outputs[4].repeat_rate.iloc[0], summary.repeat_customer_rate, places=8
        )


if __name__ == "__main__":
    unittest.main()
