"""Promotion cost identities and comparison eligibility are auditable."""

import json
import unittest

import numpy as np
import pandas as pd

from src.app_data import load_bundle
from src.common import ROOT
from src.reporting import promotion_summary


class PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames, cls.meta = load_bundle(ROOT / "data/demo")

    def test_incremental_contribution_reconciles(self):
        campaigns = self.frames["promotion_effectiveness"].dropna(
            subset=["incremental_contribution"]
        )
        expected = (
            campaigns.incremental_revenue
            - campaigns.incremental_variable_cost
            - campaigns.incremental_labour_cost
            - campaigns.campaign_cost
        )
        np.testing.assert_allclose(
            expected, campaigns.incremental_contribution, atol=0.01
        )
        np.testing.assert_allclose(
            campaigns.incremental_contribution / campaigns.campaign_cost,
            campaigns.promotion_roi,
        )

    def test_controls_do_not_overlap_any_campaign_in_comparison_window(self):
        campaigns = self.frames["promotion_effectiveness"]
        dates = campaigns.dropna(subset=["incremental_contribution"])
        for campaign in dates.itertuples():
            control_ids = json.loads(campaign.control_restaurant_ids)
            self.assertNotIn(campaign.restaurant_id, control_ids)
            for control in campaigns[
                campaigns.restaurant_id.isin(control_ids)
            ].itertuples():
                overlap = max(
                    pd.Timestamp(campaign.comparison_start),
                    pd.Timestamp(control.start_date),
                ) <= min(
                    pd.Timestamp(campaign.end_date), pd.Timestamp(control.end_date)
                )
                self.assertFalse(overlap)

    def test_truth_is_post_estimation_evidence(self):
        truth = self.frames["promotion_method_validation"].dropna(
            subset=["estimated_incremental_orders"]
        )
        np.testing.assert_allclose(
            truth.estimated_incremental_orders
            - truth.known_expected_incremental_orders,
            truth.estimation_error,
            atol=0.001,
        )
        for source in [
            "analysis.py",
            "forecasting.py",
            "feature_engineering.py",
            "clean_data.py",
        ]:
            text = (ROOT / "src" / source).read_text()
            self.assertNotIn("promotion_truth.csv", text)
            self.assertNotIn("known_order_uplift", text)
        self.assertGreater(len(truth), 0)

    def test_unestimated_campaign_spend_cannot_dilute_reported_roi(self):
        campaigns = self.frames["promotion_effectiveness"].copy()
        before = promotion_summary(campaigns)
        unavailable = campaigns.incremental_contribution.isna()
        self.assertTrue(unavailable.any())
        campaigns.loc[unavailable, "campaign_cost"] *= 100
        pd.testing.assert_frame_equal(before, promotion_summary(campaigns))


if __name__ == "__main__":
    unittest.main()
