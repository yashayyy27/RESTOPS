"""Decision-support tests focus on reconciliation, boundaries and leakage."""

import unittest

import numpy as np
import pandas as pd

from src.management import profit_bridge, revenue_bridge
from src.scenarios import Scenario, simulate, sensitivity
from src.validation import contract_checks


def ledger():
    b = dict(
        revenue=10000.0,
        discounts=500.0,
        transactions=250.0,
        ingredient_cost=3000.0,
        waste_cost=200.0,
        labour_cost=3000.0,
        paid_hours=100.0,
        commission_cost=600.0,
        overhead_cost=1200.0,
        campaign_cost=100.0,
    )
    b["operating_profit"] = 1900.0
    return b


class ScenarioTests(unittest.TestCase):
    def test_identity_preserves_entire_cost_ledger(self):
        b, result = ledger(), simulate(ledger())
        for field in b:
            self.assertAlmostEqual(b[field], result[field], places=7)
        self.assertEqual(result["cogs"], 3200.0)
        self.assertEqual(result["operating_contribution"], 3100.0)

    def test_discounts_are_deducted_once_and_hours_wages_multiply(self):
        result = simulate(
            ledger(), Scenario(hours_change=0.10, wage_change=0.10, discount_rate=0.20)
        )
        self.assertAlmostEqual(result["revenue"], 8400.0)
        self.assertAlmostEqual(result["labour_cost"], 3630.0)
        self.assertAlmostEqual(
            result["operating_profit"], 8400 - 3200 - 3630 - 504 - 1200 - 100
        )

    def test_waste_denominator_and_break_even(self):
        result = simulate(ledger(), Scenario(waste_rate=0.10))
        self.assertAlmostEqual(result["waste_cost"], 3000 / 9)
        at_be = simulate(
            ledger(),
            Scenario(
                waste_rate=0.10, demand_change=result["break_even_orders"] / 250 - 1
            ),
        )
        self.assertAlmostEqual(at_be["operating_profit"], 0, places=6)

    def test_non_viable_margin_and_invalid_inputs_are_visible(self):
        self.assertTrue(
            np.isnan(
                simulate(ledger(), Scenario(discount_rate=0.90))["break_even_orders"]
            )
        )
        for case in [
            Scenario(waste_rate=1),
            Scenario(discount_rate=-0.1),
            Scenario(demand_change=-1),
            Scenario(price_change=np.nan),
        ]:
            with self.assertRaises(ValueError):
                simulate(ledger(), case)
        broken = ledger()
        del broken["ingredient_cost"]
        with self.assertRaises(ValueError):
            simulate(broken)

    def test_sensitivity_keeps_staffing_and_ordering(self):
        cases = sensitivity(ledger(), Scenario(hours_change=0.05), 0.1)
        self.assertTrue(cases.operating_profit.is_monotonic_increasing)
        self.assertEqual(cases.labour_cost.nunique(), 1)


class InvestigationTests(unittest.TestCase):
    def test_bridge_interaction_is_allocated_exactly(self):
        before = ledger()
        after = dict(before, revenue=12000.0, transactions=300.0, labour_cost=3300.0)
        after["operating_profit"] = 3600.0
        self.assertAlmostEqual(revenue_bridge(before, after).amount.sum(), 2000.0)
        self.assertAlmostEqual(profit_bridge(before, after).amount.sum(), 1700.0)

    def test_unreconciled_profit_cannot_pass(self):
        with self.assertRaises(ValueError):
            profit_bridge(ledger(), dict(ledger(), operating_profit=999))


class ContractTests(unittest.TestCase):
    def test_schema_missing_keys_and_relationships_fail(self):
        rows = pd.DataFrame({"id": [1, 1, None], "restaurant_id": [1, 999, 1]})
        checks = contract_checks(rows, "fixture", ["id"], list(rows), set(rows), {1})
        self.assertEqual(
            checks.loc[checks.rule.eq("Unique primary key"), "invalid_rows"].iloc[0], 1
        )
        self.assertEqual(
            checks.loc[checks.rule.eq("Primary key populated"), "invalid_rows"].iloc[0],
            1,
        )
        self.assertEqual(
            checks.loc[checks.rule.eq("Restaurant relationship"), "invalid_rows"].iloc[
                0
            ],
            1,
        )
        self.assertEqual(
            contract_checks(rows, "fixture", ["id"], ["missing"], [], {1}).status.iloc[
                0
            ],
            "FAIL",
        )

    def test_missing_money_and_invalid_date_are_not_zero(self):
        rows = pd.DataFrame(
            {
                "id": [1, 2],
                "business_date": ["2025-01-01", "bad"],
                "amount": [2, np.nan],
            }
        )
        checks = contract_checks(rows, "fixture", ["id"], list(rows), set(rows))
        self.assertEqual(
            checks.loc[checks.rule.eq("Valid amount"), "status"].iloc[0], "FAIL"
        )
        self.assertEqual(
            checks.loc[checks.rule.eq("Valid business_date"), "status"].iloc[0], "FAIL"
        )


if __name__ == "__main__":
    unittest.main()
