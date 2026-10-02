"""Shared paths, configuration and stable CSV conventions."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TABLEAU = ROOT / "data" / "tableau"
REPORTS = ROOT / "reports"


def config():
    """Read the small, user-editable project configuration."""
    return json.loads((ROOT / "config/project_config.json").read_text())


def save(frame, path):
    """Write interoperable UTF-8 CSVs without an accidental index."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep allocated costs precise so daily-to-monthly reconciliation survives
    # CSV round trips. Presentation layers apply readable display formatting.
    frame.to_csv(path, index=False, float_format="%.8f")


def read(name, folder=PROCESSED):
    """Load a named project CSV. Empty identifiers remain missing."""
    return pd.read_csv(folder / f"{name}.csv", low_memory=False)


def ratio(numerator, denominator):
    """Return undefined for zero denominators instead of misleading zeros."""
    return numerator.div(denominator.where(denominator.ne(0)))
