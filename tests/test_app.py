"""Real Streamlit execution against the committed demo, without raw data."""

import os
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.app_views import VIEWS
from src.app_data import load_bundle
from src.common import ROOT


class AppWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ, {"RESTOPS_DATA_DIR": str(ROOT / "data/demo")}
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.app = AppTest.from_file(
            str(ROOT / "streamlit_app.py"), default_timeout=30
        ).run()

    def clean(self):
        self.assertFalse(self.app.exception, [e.message for e in self.app.exception])

    def test_all_views_have_computed_outputs(self):
        for name in VIEWS:
            with self.subTest(view=name):
                self.app.selectbox(key="view").select(name).run()
                self.clean()
                self.assertTrue(len(self.app.metric) > 0)
                self.assertTrue(len(self.app.dataframe) > 0)

    def test_state_filters_and_empty_selection(self):
        self.app.selectbox(key="state").select("QLD").run()
        self.clean()
        names = self.app.multiselect(key="restaurants_QLD").value
        self.assertEqual(len(names), 6)
        self.app.multiselect(key="restaurants_QLD").set_value([]).run()
        self.clean()
        self.assertIn("Select at least one", self.app.info[0].value)

    def test_scenario_controls_change_profit(self):
        self.app.selectbox(key="view").select("Profit scenario simulator").run()
        before = self.app.metric[1].value
        self.app.slider(key="hours_change").set_value(-10).run()
        self.clean()
        self.assertNotEqual(self.app.metric[1].value, before)
        self.assertIn("A$", self.app.metric[1].delta)

    def test_cleared_focus_does_not_crash_workflows(self):
        for view in (
            "Restaurant investigation",
            "Profit scenario simulator",
            "Labour & demand planning",
            "Forecasting",
        ):
            with self.subTest(view=view):
                self.app.selectbox(key="view").select(view).run()
                self.app.selectbox(key="focus_store").select(None).run()
                self.clean()
                # Streamlit may restore its configured default on clear.
                value = self.app.selectbox(key="focus_store").value
                self.assertIn(value, [None, "Wollongong"])
                if value is None:
                    self.assertTrue(
                        any(
                            "Choose a restaurant" in info.value
                            for info in self.app.info
                        )
                    )
                else:
                    self.assertTrue(self.app.metric)

    def test_labour_productivity_changes_hours(self):
        self.app.selectbox(key="view").select("Labour & demand planning").run()
        before = self.app.metric[1].value
        self.app.number_input(key="productivity").set_value(12.0).run()
        self.clean()
        self.assertNotEqual(self.app.metric[1].value, before)

    def test_scenario_resets_when_baseline_period_changes(self):
        self.app.selectbox(key="view").select("Profit scenario simulator").run()
        self.app.slider(key="hours_change").set_value(-10).run()
        self.app.selectbox(key="month").select("2025-11").run()
        self.clean()
        self.assertEqual(self.app.slider(key="hours_change").value, 0)
        self.assertEqual(self.app.metric[1].delta, "A$0")

    def test_campaign_without_controls_shows_unavailable_estimate(self):
        self.app.selectbox(key="view").select("Promotion evaluation").run()
        frames, _ = load_bundle(ROOT / "data/demo")
        row = (
            frames["promotion_effectiveness"]
            .loc[lambda f: f.estimate_status.eq("No eligible control stores")]
            .iloc[0]
        )
        label = f"{row.promotion_id} · {row.campaign_name} · {row.start_date}"
        self.app.selectbox(key="campaign").select(label).run()
        self.clean()
        self.assertIn("No eligible comparison stores", self.app.warning[0].value)
        self.assertEqual(len(self.app.metric), 0)


if __name__ == "__main__":
    unittest.main()
