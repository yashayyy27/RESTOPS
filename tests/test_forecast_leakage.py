"""Ensure predictions are unchanged by actual sales beyond their origin."""

import json
import unittest

import numpy as np
import pandas as pd

from src.common import REPORTS, TABLEAU, read
from src.forecasting import MODELS, predict_from_origin, training_rows
from src.generate_data import calendar


class ForecastLeakageTests(unittest.TestCase):
    def test_future_actuals_cannot_change_predictions(self):
        dates = pd.date_range("2024-01-01", periods=80)
        stores = read("restaurants").iloc[:2]
        history = pd.MultiIndex.from_product(
            [stores.restaurant_id, dates], names=["restaurant_id", "business_date"]
        ).to_frame(index=False)
        history["revenue"] = (
            2200 + history.restaurant_id * 100 + history.business_date.dt.dayofweek * 80
        )
        history["business_date"] = history.business_date.dt.strftime("%Y-%m-%d")
        cutoff = dates[64]
        altered = history.copy()
        altered.loc[pd.to_datetime(altered.business_date).gt(cutoff), "revenue"] = 1e9
        cal = calendar(pd.date_range(dates[0], dates[-1] + pd.Timedelta(days=28)))
        cal["business_date"] = cal.business_date.dt.strftime("%Y-%m-%d")
        for model in MODELS:
            expected = predict_from_origin(
                history, cutoff, model, stores, cal, horizon=14
            )
            actual = predict_from_origin(
                altered, cutoff, model, stores, cal, horizon=14
            )
            np.testing.assert_allclose(
                expected.forecast_revenue, actual.forecast_revenue
            )

    def test_lags_exclude_current_target(self):
        dates = pd.date_range("2024-01-01", periods=40)
        history = pd.DataFrame(
            {
                "restaurant_id": 1,
                "business_date": dates.strftime("%Y-%m-%d"),
                "revenue": np.arange(40, dtype=float),
            }
        )
        rows = training_rows(history)
        first = rows.iloc[0]
        self.assertEqual(first.revenue, 28)
        self.assertEqual(first.lag7, 21)
        self.assertEqual(first.lag28, 0)
        self.assertEqual(first.mean28, np.arange(28).mean())

    def test_model_selection_uses_validation_only(self):
        scores = pd.read_csv(REPORTS / "exports/forecast_metrics.csv")
        expected = (
            scores[scores.evaluation_period.eq("Validation")]
            .groupby("model")
            .mae.mean()
            .idxmin()
        )
        summary = json.loads((REPORTS / "forecast_summary.json").read_text())
        self.assertEqual(summary["selected_model"], expected)
        traces = read("forecast_backtests", TABLEAU)
        validation = traces[traces.evaluation_period.eq("Validation")]
        holdout = traces[traces.evaluation_period.eq("Holdout")]
        self.assertLess(validation.business_date.max(), holdout.business_date.min())
        self.assertTrue(
            (
                pd.to_datetime(traces.business_date)
                > pd.to_datetime(traces.origin_date)
            ).all()
        )
        self.assertEqual(validation.fold.nunique(), 3)


if __name__ == "__main__":
    unittest.main()
