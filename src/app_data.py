"""Portable app data access; full local marts or a small committed demo bundle."""

import json
import os
from pathlib import Path

import pandas as pd

from .common import ROOT, TABLEAU

APP_TABLES = [
    "store_day",
    "store_month_kpis",
    "store_hour",
    "product_month",
    "waste_detail",
    "customer_segment_summary",
    "customer_cohorts",
    "loyalty_behaviours",
    "promotion_effectiveness",
    "forecast_daily",
    "forecast_backtests",
    "forecast_metrics",
    "forecast_store_metrics",
    "data_quality_audit",
    "validation_checks",
    "missing_values",
    "quarantine_sample",
    "promotion_method_validation",
]


def data_folder(mode="auto"):
    """Explicit RESTOPS_DATA_DIR supports tests and independent demo deployment."""
    override = os.environ.get("RESTOPS_DATA_DIR")
    if override:
        return Path(override)
    if mode == "demo":
        return ROOT / "data/demo"
    ready = all((TABLEAU / f"{name}.csv").exists() for name in APP_TABLES)
    return TABLEAU if ready and mode != "demo" else ROOT / "data/demo"


def load_bundle(folder):
    folder = Path(folder)
    frames = {}
    for name in APP_TABLES:
        path = folder / f"{name}.csv"
        if not path.exists():
            path = folder / f"{name}.csv.gz"
        frames[name] = pd.read_csv(path, low_memory=False)
    meta = json.loads((folder / "app_manifest.json").read_text())
    return frames, meta


def export_csv(frame):
    """Excel-compatible UTF-8 BOM with real numeric values and stable columns."""
    return frame.to_csv(index=False).encode("utf-8-sig")
