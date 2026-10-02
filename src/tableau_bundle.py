"""Minimal Tableau build bundle with explicit grains and reconciliation evidence.

This exports data and instructions, never a fabricated native Tableau workbook.
"""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import numpy as np
import pandas as pd

from .app_data import load_bundle
from .common import ROOT
from .management import weekly_scorecard
from .planning import hourly_plan

KEYS = {
    "store_dimension": ["restaurant_id"],
    "store_month_kpis": ["restaurant_id", "month"],
    "store_day": ["restaurant_id", "business_date"],
    "store_hour": ["restaurant_id", "business_date", "hour"],
    "product_month": ["restaurant_id", "month", "product_id", "channel"],
    "customer_segment_summary": ["restaurant_id", "segment"],
    "customer_cohorts": ["restaurant_id", "cohort_month"],
    "promotion_effectiveness": ["promotion_id"],
    "forecast_daily": ["restaurant_id", "business_date"],
    "forecast_backtests": ["restaurant_id", "business_date", "model", "origin_date"],
    "forecast_plot": ["restaurant_id", "business_date"],
    "labour_plan": ["restaurant_id", "business_date", "hour"],
    "weekly_performance": ["restaurant_id", "window_end"],
}


def validate(frames):
    """Independent data-file checks; does not validate a Tableau rendering."""
    checks = []

    def record(name, passed):
        checks.append({"check": name, "status": "PASS" if passed else "FAIL"})

    ids = set(frames["store_dimension"].restaurant_id)
    for name, keys in KEYS.items():
        frame = frames[name]
        record(
            f"{name}: complete unique key",
            not frame[keys].isna().any().any() and not frame.duplicated(keys).any(),
        )
        record(f"{name}: store relationship", set(frame.restaurant_id).issubset(ids))
    daily = frames["store_day"]
    monthly = frames["store_month_kpis"]
    for field in (
        "revenue",
        "operating_profit",
        "labour_cost",
        "waste_cost",
        "transactions",
    ):
        grouped = daily.groupby(["restaurant_id", "month"])[field].sum().rename("daily")
        paired = monthly.set_index(["restaurant_id", "month"])[[field]].join(
            grouped, how="outer"
        )
        record(
            f"Monthly {field} reconciles to daily ledger (AUD .01/count exact)",
            bool(
                np.isclose(
                    paired[field],
                    paired.daily,
                    rtol=0,
                    atol=0.01 if field != "transactions" else 0,
                ).all()
            ),
        )
    for name, field in (
        ("product_month", "revenue"),
        ("store_hour", "revenue"),
        ("store_hour", "paid_hours"),
    ):
        record(
            f"{name} {field} reconciles to daily totals",
            bool(
                np.isclose(
                    frames[name][field].sum(), daily[field].sum(), rtol=0, atol=0.01
                )
            ),
        )
    traces = frames["forecast_backtests"]
    record(
        "Every backtest date follows origin",
        bool(
            (
                pd.to_datetime(traces.business_date)
                > pd.to_datetime(traces.origin_date)
            ).all()
        ),
    )
    record(
        "Validation dates precede final holdout",
        traces.loc[traces.evaluation_period.eq("Validation"), "business_date"].max()
        < traces.loc[traces.evaluation_period.eq("Holdout"), "business_date"].min(),
    )
    if any(c["status"] != "PASS" for c in checks):
        raise ValueError(f"Tableau build data failed reconciliation: {checks}")
    return checks


def build():
    frames, meta = load_bundle(ROOT / "data/demo")
    data = {name: frames[name].copy() for name in KEYS if name in frames}
    data["store_dimension"] = frames["store_day"][
        ["restaurant_id", "restaurant_name", "state", "area", "location_type"]
    ].drop_duplicates()
    data["labour_plan"] = hourly_plan(
        frames["store_day"], frames["store_hour"], frames["forecast_daily"]
    )
    data["weekly_performance"] = weekly_scorecard(
        frames["store_day"], frames["store_month_kpis"]
    )
    history = frames["store_day"][["restaurant_id", "business_date", "revenue"]].copy()
    history["record_kind"] = "Synthetic history"
    future = frames["forecast_daily"][
        ["restaurant_id", "business_date", "forecast_revenue", "lower_80", "upper_80"]
    ].rename(columns={"forecast_revenue": "revenue"})
    future["record_kind"] = "Forecast estimate"
    data["forecast_plot"] = pd.concat([history, future], ignore_index=True)
    checks = validate(data)
    manifest = {
        "status": "DATA BUNDLE VERIFIED; NATIVE WORKBOOK NOT VERIFIED",
        "synthetic": True,
        "history_start": meta["history_start"],
        "history_end": meta["history_end"],
        "forecast_origin": meta["forecast_origin"],
        "forecast_model": meta["forecast"]["selected_model"],
        "customer_asof": meta["customer_asof"],
        "campaign_scope": "Full 2024–2025 campaign windows, independent of Oct–Dec reporting filters",
        "checks": checks,
        "sources": [],
    }
    files = {}
    for name, frame in data.items():
        contents = frame.to_csv(index=False, float_format="%.8f").encode()
        files[f"data/{name}.csv"] = contents
        manifest["sources"].append(
            {
                "file": f"data/{name}.csv",
                "rows": len(frame),
                "keys": KEYS[name],
                "sha256": hashlib.sha256(contents).hexdigest(),
                "columns": {key: str(value) for key, value in frame.dtypes.items()},
            }
        )
    # Calculated exact workbook acceptance reference for one repeatable case.
    row = (
        data["store_month_kpis"]
        .loc[lambda f: f.restaurant_name.eq("Wollongong") & f.month.eq("2025-12")]
        .iloc[0]
    )
    manifest["acceptance_reference"] = {
        "restaurant": "Wollongong",
        "month": "2025-12",
        **{
            key: float(row[key])
            for key in (
                "revenue",
                "operating_profit",
                "transactions",
                "labour_cost",
                "labour_cost_pct",
                "waste_pct",
                "satisfaction_score",
                "target_achievement_pct",
            )
        },
    }
    files["manifest.json"] = json.dumps(manifest, indent=2, allow_nan=False).encode()
    for filename in ("BUILD.md", "calculations.md", "verification_checklist.md"):
        files[filename] = (ROOT / "dashboards/tableau_build" / filename).read_bytes()
    target = ROOT / "dashboards/tableau_build/restops_tableau_bundle.zip"
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = ZipInfo(name, date_time=(2026, 10, 2, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, content)
    (target.parent / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(
        f"Verified {len(data)} explicit-grain sources / {len(checks)} data checks; wrote {target.name} ({target.stat().st_size:,} bytes). No native workbook created."
    )
    return manifest


if __name__ == "__main__":
    build()
