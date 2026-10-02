"""Hourly coverage must reconcile and exclude post-origin observations."""

import unittest

import numpy as np
import pandas as pd

from src.app_data import load_bundle
from src.common import ROOT
from src.management import weekly_scorecard, weekly_brief
from src.planning import PlanningAssumptions, hourly_plan, scheduled_hourly


class PlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames, cls.meta = load_bundle(ROOT / "data/demo")
        cls.forecast = cls.frames["forecast_daily"].query("restaurant_id == 6")

    def plan(self, settings=PlanningAssumptions(), daily=None, hourly=None):
        return hourly_plan(
            self.frames["store_day"] if daily is None else daily,
            self.frames["store_hour"] if hourly is None else hourly,
            self.forecast,
            settings,
        )

    def test_hour_allocation_conserves_daily_order_estimate(self):
        plan = self.plan()
        self.assertEqual(len(plan), 28 * 11)
        daily = plan.groupby("business_date").agg(
            orders=("forecast_orders", "sum"),
            revenue=("forecast_revenue", "first"),
            atv=("reference_atv", "first"),
        )
        np.testing.assert_allclose(daily.orders, daily.revenue / daily.atv)
        self.assertFalse(
            plan.duplicated(["restaurant_id", "business_date", "hour"]).any()
        )

    def test_future_history_cannot_change_hourly_plan(self):
        daily = self.frames["store_day"].copy()
        hourly = self.frames["store_hour"].copy()
        new_day, new_hour = daily.tail(30).copy(), hourly.tail(30).copy()
        new_day["business_date"] = new_hour["business_date"] = "2026-01-15"
        new_day[["transactions", "revenue"]] = 1e9
        new_hour[
            ["transactions", "scheduled_paid_hours", "scheduled_service_hours"]
        ] = 1e9
        actual = self.plan(
            daily=pd.concat([daily, new_day]), hourly=pd.concat([hourly, new_hour])
        )
        pd.testing.assert_frame_equal(actual, self.plan())

    def test_productivity_and_zero_schedule(self):
        before, after = self.plan(), self.plan(
            PlanningAssumptions(orders_per_service_hour=8, schedule_multiplier=0)
        )
        self.assertLessEqual(
            after.suggested_service_hours.sum(), before.suggested_service_hours.sum()
        )
        self.assertEqual(after.scheduled_paid_hours.sum(), 0)
        self.assertGreater(after.budget_difference.sum(), 0)
        with self.assertRaises(ValueError):
            self.plan(PlanningAssumptions(utilisation=0))

    def test_scheduled_shift_breaks_reconcile(self):
        shift = pd.DataFrame(
            {
                "restaurant_id": [1],
                "business_date": ["2025-12-01"],
                "scheduled_start": ["2025-12-01 11:00:00"],
                "scheduled_end": ["2025-12-01 14:00:00"],
                "break_hours": [0.5],
                "role": ["Service"],
            }
        )
        hourly = scheduled_hourly(shift)
        self.assertAlmostEqual(hourly.scheduled_paid_hours.sum(), 2.5)
        self.assertAlmostEqual(hourly.scheduled_service_hours.sum(), 2.5)

    def test_weekly_target_crosses_calendar_month_without_duplication(self):
        daily = self.frames["store_day"].query("restaurant_id == 6")
        score = weekly_scorecard(daily, self.frames["store_month_kpis"], "2025-12-03")
        targets = (
            self.frames["store_month_kpis"]
            .query("restaurant_id == 6")
            .set_index("month")
            .revenue_target
        )
        expected = targets["2025-11"] / 30 * 4 + targets["2025-12"] / 31 * 3
        self.assertAlmostEqual(score.allocated_revenue_target.iloc[0], expected)
        missing = daily[~daily.business_date.between("2025-11-20", "2025-11-26")]
        with self.assertRaises(ValueError):
            weekly_scorecard(missing, self.frames["store_month_kpis"], "2025-12-03")

    def test_brief_retains_evidence_and_conditional_impact(self):
        score = weekly_scorecard(
            self.frames["store_day"], self.frames["store_month_kpis"]
        )
        brief = weekly_brief(score)
        self.assertEqual(len(brief), 18)
        self.assertTrue(brief.estimated_weekly_opportunity.ge(0).all())
        self.assertTrue(
            brief[["source", "impact_assumption", "success_measure", "window_end"]]
            .notna()
            .all()
            .all()
        )


if __name__ == "__main__":
    unittest.main()
