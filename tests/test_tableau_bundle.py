"""Validate the delivered build data without pretending to validate Tableau."""

import hashlib
import io
import json
from zipfile import ZipFile
import unittest

import pandas as pd

from src.common import ROOT
from src.tableau_bundle import validate


class TableauBundleTests(unittest.TestCase):
    def test_packaged_sources_hash_keys_and_financial_identities(self):
        with ZipFile(
            ROOT / "dashboards/tableau_build/restops_tableau_bundle.zip"
        ) as bundle:
            manifest = json.loads(bundle.read("manifest.json"))
            frames = {}
            for spec in manifest["sources"]:
                payload = bundle.read(spec["file"])
                self.assertEqual(hashlib.sha256(payload).hexdigest(), spec["sha256"])
                name = spec["file"].split("/")[-1].removesuffix(".csv")
                frames[name] = pd.read_csv(io.BytesIO(payload))
                self.assertEqual(len(frames[name]), spec["rows"])
            self.assertEqual(len(frames), 13)
            self.assertTrue(all(c["status"] == "PASS" for c in validate(frames)))
            self.assertIn("NATIVE WORKBOOK NOT VERIFIED", manifest["status"])
            self.assertFalse(
                any(path.endswith((".twb", ".twbx")) for path in bundle.namelist())
            )
