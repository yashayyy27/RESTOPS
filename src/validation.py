"""Post-clean data contracts, relationships, coverage and source provenance."""

import hashlib
import json
import sqlite3

import numpy as np
import pandas as pd

from .clean_data import PRIMARY_KEYS
from .common import PROCESSED, RAW, REPORTS, ROOT, read, save
from .management import COSTS

OPTIONAL = {
    "customer_id",
    "promotion_id",
    "order_id",
    "holiday_name",
    "overall_score",
    "food_score",
    "service_score",
}


def contract_checks(frame, table, keys, columns, required, store_ids=None):
    """Return explicit failed counts; missing columns cannot appear as PASS."""
    rows = []

    def check(rule, count, detail):
        rows.append(
            {
                "table": table,
                "rule": rule,
                "invalid_rows": int(count),
                "status": "FAIL" if count else "PASS",
                "detail": detail,
            }
        )

    missing = set(columns) - set(frame)
    check(
        "Schema columns",
        len(missing),
        (
            "Missing: " + ", ".join(sorted(missing))
            if missing
            else "Required schema columns present"
        ),
    )
    if missing:
        return pd.DataFrame(rows)
    check("Unique primary key", frame.duplicated(keys).sum(), ", ".join(keys))
    check(
        "Primary key populated",
        frame[keys].isna().any(axis=1).sum(),
        "Null primary keys prohibited",
    )
    check(
        "Required values",
        frame[list(required)].isna().any(axis=1).sum(),
        ", ".join(sorted(required)),
    )
    if store_ids is not None and "restaurant_id" in frame:
        check(
            "Restaurant relationship",
            (~frame.restaurant_id.isin(store_ids)).sum(),
            "Stable restaurant_id master reference",
        )
    for field in (
        "business_date",
        "event_date",
        "start_date",
        "end_date",
        "timestamp_local",
        "actual_start",
        "actual_end",
        "scheduled_start",
        "scheduled_end",
    ):
        if field in frame:
            parsed = pd.to_datetime(frame[field], errors="coerce")
            check(f"Valid {field}", parsed.isna().sum(), "Parseable date/timestamp")
    for field in (
        "net_revenue",
        "list_revenue",
        "ingredient_cost",
        "discount_amount",
        "gst_amount",
        "waste_cost",
        "labour_cost",
        "hourly_cost",
        "amount",
        "campaign_cost",
        "revenue_target",
    ):
        if field in frame:
            values = pd.to_numeric(frame[field], errors="coerce")
            check(
                f"Valid {field}",
                (~np.isfinite(values) | values.lt(0)).sum(),
                "Finite non-negative monetary value",
            )
    if table == "transactions":
        check(
            "Net sales reconciliation",
            (frame.list_revenue - frame.discount_amount - frame.net_revenue)
            .abs()
            .gt(0.011)
            .sum(),
            "List sales less discounts equals net sales",
        )
        check(
            "GST reconciliation",
            (frame.net_revenue * 0.10 - frame.gst_amount).abs().gt(0.011).sum(),
            "Simplified synthetic 10% GST",
        )
        check(
            "Channel category",
            (~frame.channel.isin(["Dine-in", "Takeaway", "Delivery"])).sum(),
            "Approved channels only",
        )
    if table == "products":
        approved = json.loads((ROOT / "config/product_categories.json").read_text())
        check(
            "Product taxonomy",
            frame.category.ne(frame.product_name.map(approved)).sum(),
            "Versioned menu reference",
        )
    return pd.DataFrame(rows)


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run():
    """Audit processed sources and independent SQLite financial reconciliation."""
    checks, missing, manifest = [], [], []
    stores = set(read("restaurants").restaurant_id)
    with sqlite3.connect(PROCESSED / "restops.sqlite") as db:
        for name, keys in PRIMARY_KEYS.items():
            schema = db.execute(f"PRAGMA table_info({name})").fetchall()
            columns = [row[1] for row in schema]
            required = set(columns) - OPTIONAL | set(keys)
            if name == "transactions":
                required.add("order_id")
            frame = read(name)
            checks.append(contract_checks(frame, name, keys, columns, required, stores))
            for field in frame:
                missing.append(
                    {
                        "table": name,
                        "column": field,
                        "missing_rows": int(frame[field].isna().sum()),
                        "total_rows": len(frame),
                        "required": field in required,
                        "interpretation": (
                            "Required"
                            if field in required
                            else "Optional or not part of source contract"
                        ),
                    }
                )
            for layer, folder in [("raw", RAW), ("processed", PROCESSED)]:
                path = folder / f"{name}.csv"
                manifest.append(
                    {
                        "layer": layer,
                        "table": name,
                        "path": str(path.relative_to(ROOT)),
                        "bytes": path.stat().st_size,
                        "sha256": file_hash(path),
                    }
                )
        fk = len(db.execute("PRAGMA foreign_key_check").fetchall())
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        ledger = pd.read_sql_query((ROOT / "sql/kpi_queries.sql").read_text(), db)
    monthly = read("store_month_kpis")
    joined = ledger.merge(
        monthly,
        on=["restaurant_id", "month"],
        suffixes=("_sql", "_python"),
        validate="one_to_one",
    )
    mismatch = ~np.isclose(joined.revenue_sql, joined.revenue_python, atol=0.01)
    daily = read("store_day")
    bridge_error = (
        (daily.revenue - daily[COSTS].sum(axis=1) - daily.operating_profit)
        .abs()
        .gt(0.01)
    )
    extra = [
        {
            "table": "database",
            "rule": "Foreign-key integrity",
            "invalid_rows": fk,
            "status": "FAIL" if fk else "PASS",
            "detail": "SQLite source fact relationships",
        },
        {
            "table": "database",
            "rule": "Database integrity",
            "invalid_rows": int(integrity != "ok"),
            "status": "PASS" if integrity == "ok" else "FAIL",
            "detail": integrity,
        },
        {
            "table": "store_month_kpis",
            "rule": "Independent SQL revenue",
            "invalid_rows": int(mismatch.sum()),
            "status": "FAIL" if mismatch.any() else "PASS",
            "detail": "Source POS SQL vs Python restaurant/month totals; tolerance AUD 0.01",
        },
        {
            "table": "store_day",
            "rule": "Complete cost ledger",
            "invalid_rows": int(bridge_error.sum()),
            "status": "FAIL" if bridge_error.any() else "PASS",
            "detail": "Revenue less six cost components reconciles to operating profit",
        },
    ]
    audit = pd.concat(checks + [pd.DataFrame(extra)], ignore_index=True)
    save(audit, REPORTS / "exports/validation_checks.csv")
    save(pd.DataFrame(missing), REPORTS / "exports/missing_values.csv")
    (REPORTS / "source_manifest.json").write_text(json.dumps(manifest, indent=2))
    if audit.status.eq("FAIL").any():
        raise ValueError("Post-clean validation failed; inspect validation_checks.csv")
    print(f"Passed {len(audit)} source/relationship/financial checks.", flush=True)
    return audit


if __name__ == "__main__":
    run()
