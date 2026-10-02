"""Materialise decision exports and a portable, honest application demo bundle."""

import json
import shutil
from dataclasses import asdict

import pandas as pd

from .app_data import APP_TABLES
from .common import PROCESSED, REPORTS, ROOT, TABLEAU, config, read, save
from .management import aggregate, weekly_brief, weekly_scorecard
from .planning import PlanningAssumptions, hourly_plan, scheduled_hourly
from .scenarios import Scenario, compare, sensitivity


def validate_promotion_method(estimates):
    """Compare estimated order uplift with isolated generator expectations.

    Ground truth contains expected mean demand changes, not realised individual
    counterfactual orders or profit. It is read only after estimation completes.
    """
    path = ROOT / "data/validation/promotion_truth.csv"
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "promotion_id",
                "restaurant_id",
                "known_expected_incremental_orders",
                "estimated_incremental_orders",
                "estimation_error",
                "status",
            ]
        )
    truth = (
        pd.read_csv(path)
        .groupby(["promotion_id", "restaurant_id"])
        .agg(known_expected_incremental_orders=("treatment_expected_orders", "sum"))
        .reset_index()
    )
    joined = truth.merge(
        estimates[["promotion_id", "incremental_orders", "estimate_status"]],
        on="promotion_id",
        validate="one_to_one",
    )
    joined = joined.rename(
        columns={
            "incremental_orders": "estimated_incremental_orders",
            "estimate_status": "status",
        }
    )
    joined["estimation_error"] = (
        joined.estimated_incremental_orders - joined.known_expected_incremental_orders
    )
    return joined


def demo_bundle():
    """Keep 92 recent trading days and exact full-snapshot evaluation summaries."""
    folder = ROOT / "data/demo"
    folder.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((TABLEAU / "app_manifest.json").read_text())
    end = pd.Timestamp(manifest["history_end"])
    start = end - pd.Timedelta(days=91)
    for name in APP_TABLES:
        frame = read(name, TABLEAU)
        if name in ("store_day", "store_hour", "waste_detail"):
            frame = frame[pd.to_datetime(frame.business_date).ge(start)]
        if name in ("store_month_kpis", "product_month"):
            frame = frame[frame.month.ge(start.strftime("%Y-%m"))]
        frame.to_csv(
            folder / f"{name}.csv.gz",
            index=False,
            float_format="%.8f",
            compression={"method": "gzip", "mtime": 0},
        )
        # Remove prior uncompressed generated copies so loading is unambiguous.
        (folder / f"{name}.csv").unlink(missing_ok=True)
    manifest.update(
        {
            "mode": "demo",
            "history_start": start.strftime("%Y-%m-%d"),
            "scope": "Exact recent 92-day aggregates; customer, promotion and forecast evaluation snapshots retain their explicitly labelled original periods. Quality checks describe the full source pipeline, not a fresh audit of raw demo files.",
        }
    )
    (folder / "app_manifest.json").write_text(json.dumps(manifest, indent=2))


def run():
    """Build planning-ready marts, weekly register and documented export contracts."""
    daily, monthly = read("store_day"), read("store_month_kpis")
    hourly = read("store_hour", TABLEAU).drop(
        columns=["scheduled_paid_hours", "scheduled_service_hours"], errors="ignore"
    )
    hourly = hourly.merge(
        scheduled_hourly(read("labour")),
        on=["restaurant_id", "business_date", "hour"],
        validate="one_to_one",
    )
    save(hourly, TABLEAU / "store_hour.csv")
    customers = read("customer_segments", TABLEAU)
    segments = (
        customers.groupby(["restaurant_id", "segment"])
        .agg(
            customers=("customer_id", "size"),
            spend=("spend", "sum"),
            visits=("visits", "sum"),
            eligible_customers=("eligible_90d", "sum"),
            repeat_customers=("repeat_within_90d", "sum"),
        )
        .reset_index()
    )
    save(segments, TABLEAU / "customer_segment_summary.csv")
    for name in ("data_quality_audit", "validation_checks", "missing_values"):
        shutil.copyfile(REPORTS / f"exports/{name}.csv", TABLEAU / f"{name}.csv")
    quarantine = read("quarantine_transactions")
    save(quarantine.head(100), TABLEAU / "quarantine_sample.csv")
    method_validation = validate_promotion_method(
        read("promotion_effectiveness", TABLEAU)
    )
    save(method_validation, TABLEAU / "promotion_method_validation.csv")
    scorecard = weekly_scorecard(daily, monthly)
    brief = weekly_brief(scorecard)
    save(scorecard, REPORTS / "exports/weekly_performance.csv")
    save(brief, REPORTS / "exports/weekly_management_brief.csv")
    save(scorecard, TABLEAU / "weekly_performance.csv")
    save(brief, TABLEAU / "weekly_management_brief.csv")
    assumptions = PlanningAssumptions()
    plan = hourly_plan(daily, hourly, read("forecast_daily", TABLEAU), assumptions)
    save(plan, TABLEAU / "labour_plan.csv")
    save(plan, REPORTS / "exports/labour_plan.csv")
    latest_month = monthly.month.max()
    # A named, reproducible illustration rather than an optimised recommendation.
    baseline = aggregate(
        daily[daily.restaurant_id.eq(6) & daily.month.eq(latest_month)]
    )
    scenario = Scenario(hours_change=-0.05, demand_change=-0.02, waste_rate=0.04)
    comparison = compare(baseline, scenario)
    ranges = sensitivity(baseline, scenario)
    save(comparison, REPORTS / "exports/scenario_comparison.csv")
    save(ranges, REPORTS / "exports/scenario_sensitivity.csv")
    week_start, week_end = scorecard.window_start.iloc[0], scorecard.window_end.iloc[0]
    lines = [
        "# Weekly management brief",
        "",
        f"**Fictional operation | {week_start}–{week_end} vs preceding seven days | AUD excluding GST**",
        "",
        "Rolling seven-day windows are used, including holidays. Monthly targets are allocated evenly by calendar day. Explanations are hypotheses. Impact estimates compare one component to the prior-week rate and are not committed savings or additive across interventions.",
        "",
    ]
    for item in brief.itertuples():
        lines += [
            f"## {item.restaurant_name} · {item.priority}",
            "",
            f"**What changed:** {item.what_changed}",
            "",
            f"**Evidence:** {item.evidence}",
            "",
            f"**Plausible explanation:** {item.plausible_explanation}",
            "",
            f"**Estimated impact:** A${item.estimated_weekly_opportunity:,.0f} per selected week. {item.impact_assumption}.",
            "",
            f"**Action:** {item.recommended_action}",
            "",
            f"**Proposed owner / measure:** {item.proposed_owner}. {item.success_measure}.",
            "",
            "**Trace:** `weekly_performance.csv` restaurant_id / window_start / window_end, sourced from `store_day` and `store_month_kpis`.",
            "",
        ]
    (REPORTS / "weekly_management_brief.md").write_text("\n".join(lines))
    manifest = {
        "mode": "full",
        "company": config()["company"],
        "history_start": daily.business_date.min(),
        "history_end": daily.business_date.max(),
        "forecast_origin": plan.origin_date.iloc[0],
        "forecast_start": plan.business_date.min(),
        "forecast_end": plan.business_date.max(),
        "customer_asof": daily.business_date.max(),
        "quality": json.loads((REPORTS / "quality_summary.json").read_text()),
        "forecast": json.loads((REPORTS / "forecast_summary.json").read_text()),
        "planning_defaults": asdict(assumptions),
        "scope": "Full generated historical marts; source validation recorded after cleaning.",
        "lineage": "Stable order/line/shift/campaign IDs in processed CSV and SQLite; SHA256 source_manifest.json; repair rules in data_quality_audit.csv",
    }
    (TABLEAU / "app_manifest.json").write_text(json.dumps(manifest, indent=2))
    catalog = {
        "store_day": (
            ["restaurant_id", "business_date"],
            "Restaurant/trading date",
            "Independent source facts aggregated before joining",
        ),
        "store_hour": (
            ["restaurant_id", "business_date", "hour"],
            "Restaurant/local date/hour",
            "Orders; actual and scheduled shifts, breaks allocated uniformly",
        ),
        "store_month_kpis": (
            ["restaurant_id", "month"],
            "Restaurant/calendar month",
            "Daily totals and monthly targets",
        ),
        "product_month": (
            ["restaurant_id", "month", "product_id", "channel"],
            "Restaurant/month/product/channel",
            "Validated product lines; orders_with_product is not additive across products",
        ),
        "waste_detail": (
            ["restaurant_id", "business_date", "product_id", "reason"],
            "Restaurant/date/product/waste reason",
            "Validated waste ledger",
        ),
        "forecast_daily": (
            ["restaurant_id", "business_date"],
            "Restaurant/future date at a single origin",
            "Validation-selected model; origin-date labelled",
        ),
        "forecast_backtests": (
            ["restaurant_id", "business_date", "model", "origin_date"],
            "Restaurant/date/model/origin",
            "Chronological validation and holdout; filter one model before summing",
        ),
        "forecast_store_metrics": (
            ["restaurant_id", "evaluation_period", "model"],
            "Restaurant/evaluation/model",
            "Metrics recomputed from forecast errors; WAPE is 0–100",
        ),
        "promotion_effectiveness": (
            ["promotion_id"],
            "Campaign/restaurant",
            "Observed before/during and eligible location peer comparisons",
        ),
        "customer_segment_summary": (
            ["restaurant_id", "segment"],
            "Restaurant/segment at fixed snapshot",
            "Anonymous IDs; complete lifetime snapshot, not reporting-month activity",
        ),
        "customer_cohorts": (
            ["restaurant_id", "cohort_month"],
            "Restaurant/first-observed month",
            "Full 90-day eligible follow-up; not proven acquisition date",
        ),
        "loyalty_behaviours": (
            ["early_activity_band", "early_redemption"],
            "Company activity/redemption group",
            "Company-wide view unaffected by store selection",
        ),
        "labour_plan": (
            ["restaurant_id", "business_date", "hour"],
            "Restaurant/future date/hour/default assumptions",
            "Derived from pre-origin weekday mix and forecast; repeated schedule template",
        ),
        "weekly_performance": (
            ["restaurant_id", "window_end"],
            "Restaurant/rolling seven-day window",
            "Daily facts and prorated monthly revenue targets",
        ),
        "weekly_management_brief": (
            ["restaurant_id", "window_end"],
            "Restaurant/rolling seven-day decision",
            "Calculated component opportunities and proposed pilots",
        ),
    }
    catalog_rows = [
        {
            "dataset": name,
            "keys": keys,
            "grain": grain,
            "source": source,
            "join_guidance": "Use separate Tableau logical sources. Never join different fact grains on restaurant_id alone; aggregate first. Ratios recalculate from summed numerators/denominators.",
        }
        for name, (keys, grain, source) in catalog.items()
    ]
    (ROOT / "docs/tableau_catalog.json").write_text(json.dumps(catalog_rows, indent=2))
    demo_bundle()
    print(
        "Created weekly decisions, hourly planning, scenario exports and demo bundle.",
        flush=True,
    )


if __name__ == "__main__":
    run()
