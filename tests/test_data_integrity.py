"""Integration contracts against the generated RESTOPS analytical database."""

import json
import sqlite3
import unittest

import pandas as pd

from src.common import PROCESSED, REPORTS, ROOT, TABLEAU, read


class DataIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(PROCESSED / "restops.sqlite")

    def tearDown(self):
        self.connection.close()

    def test_volume_keys_and_foreign_keys(self):
        stores, orders, lines = self.connection.execute(
            "SELECT (SELECT COUNT(*) FROM restaurants), (SELECT COUNT(*) FROM orders), (SELECT COUNT(*) FROM transactions)"
        ).fetchone()
        self.assertEqual(stores, 18)
        self.assertGreaterEqual(orders, 500000)
        self.assertGreater(lines, orders)
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_key_check").fetchall(), []
        )
        self.assertEqual(
            self.connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
        )

    def test_complete_order_quarantine(self):
        bad_orders = (
            pd.read_csv(PROCESSED / "quarantine_transactions.csv")
            .order_id.unique()
            .tolist()
        )
        placeholders = ",".join("?" for _ in bad_orders)
        count = self.connection.execute(
            f"SELECT COUNT(*) FROM orders WHERE order_id IN ({placeholders})",
            bad_orders,
        ).fetchone()[0]
        self.assertEqual(count, 0)
        inconsistent = self.connection.execute(
            "SELECT COUNT(*) FROM (SELECT order_id FROM transactions GROUP BY order_id "
            "HAVING COUNT(DISTINCT restaurant_id) > 1 OR COUNT(DISTINCT timestamp_local) > 1 OR COUNT(DISTINCT channel) > 1)"
        ).fetchone()[0]
        self.assertEqual(inconsistent, 0)

    def test_observation_coverage_and_category_reference(self):
        daily = read("store_day")
        self.assertEqual(len(daily), 18 * 731)
        self.assertFalse(daily.duplicated(["restaurant_id", "business_date"]).any())
        categories = json.loads((ROOT / "config/product_categories.json").read_text())
        products = read("products")
        self.assertTrue(
            products.category.eq(products.product_name.map(categories)).all()
        )

    def test_customer_followup_and_forecast_shape(self):
        customers = read("customer_segments", TABLEAU)
        eligible = pd.to_datetime(customers.first_visit).le(
            pd.Timestamp("2025-12-31") - pd.Timedelta(days=90)
        )
        self.assertTrue(customers.eligible_90d.eq(eligible).all())
        self.assertTrue(customers.loc[~eligible, "repeat_within_90d"].isna().all())
        future = read("forecast_daily", TABLEAU)
        self.assertEqual(len(future), 18 * 28)
        self.assertFalse(future.duplicated(["restaurant_id", "business_date"]).any())
        self.assertTrue(
            future.forecast_revenue.between(future.lower_80, future.upper_80).all()
        )


if __name__ == "__main__":
    unittest.main()
