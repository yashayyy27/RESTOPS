"""Independent checks for export keys, forecast scoring and native workbook data."""

import json
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pandas as pd

from src.app_data import load_bundle
from src.common import ROOT
from src.management import weekly_scorecard


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames, cls.meta = load_bundle(ROOT / "data/demo")

    def test_documented_tableau_keys_are_unique(self):
        catalog = json.loads((ROOT / "docs/tableau_catalog.json").read_text())
        checked = 0
        for spec in catalog:
            frame = self.frames.get(spec["dataset"])
            if frame is None:
                continue
            with self.subTest(dataset=spec["dataset"]):
                keys = spec["keys"]
                self.assertFalse(frame[keys].isna().any().any())
                self.assertFalse(frame.duplicated(keys).any())
                checked += 1
        self.assertGreaterEqual(checked, 10)

    def test_restaurant_forecast_scores_match_daily_errors(self):
        predictions = self.frames["forecast_backtests"]
        for score in self.frames["forecast_store_metrics"].itertuples():
            subset = predictions[
                predictions.restaurant_id.eq(score.restaurant_id)
                & predictions.model.eq(score.model)
                & predictions.evaluation_period.eq(score.evaluation_period)
            ]
            errors = subset.actual_revenue - subset.forecast_revenue
            self.assertAlmostEqual(np.abs(errors).mean(), score.mae, places=3)
            self.assertAlmostEqual(
                np.sqrt(np.square(errors).mean()), score.rmse, places=3
            )
            self.assertAlmostEqual(
                100 * np.abs(errors).sum() / subset.actual_revenue.sum(),
                score.wape,
                places=3,
            )

    def test_excel_revenue_matches_weekly_decision_ledger(self):
        # Read OOXML directly: verifies exported values without an authoring engine.
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        with ZipFile(ROOT / "reports/exports/weekly_management_pack.xlsx") as book:
            shared = ET.fromstring(book.read("xl/sharedStrings.xml"))
            strings = ["".join(node.itertext()) for node in shared]
            sheet = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
            cells = {}
            for cell in sheet.findall(".//x:c", ns):
                value = cell.find("x:v", ns)
                if value is not None:
                    kind = cell.attrib.get("t")
                    if kind == "s":
                        parsed = strings[int(value.text)]
                    elif kind == "str":
                        parsed = value.text
                    else:
                        parsed = float(value.text)
                    cells[cell.attrib["r"]] = parsed
        expected = weekly_scorecard(
            self.frames["store_day"], self.frames["store_month_kpis"]
        )
        expected = expected.set_index("restaurant_name").revenue
        self.assertEqual(len(expected), 18)
        for row in range(7, 25):
            self.assertAlmostEqual(
                cells[f"B{row}"], expected.loc[cells[f"A{row}"]], places=2
            )


if __name__ == "__main__":
    unittest.main()
