"""Rule-based source validation with complete-order quarantine and audit logs."""

import json

import numpy as np
import pandas as pd

from .common import PROCESSED, RAW, REPORTS, ROOT, config, read, save

PRIMARY_KEYS = {
    "restaurants": ["restaurant_id"],
    "products": ["product_id"],
    "transactions": ["transaction_line_id"],
    "labour": ["shift_id"],
    "customer_feedback": ["feedback_id"],
    "loyalty": ["loyalty_event_id"],
    "promotions": ["promotion_id"],
    "waste": ["waste_id"],
    "targets": ["restaurant_id", "month"],
    "operating_costs": ["cost_id"],
    "delivery": ["order_id"],
    "calendar": ["business_date", "state"],
    "manager_assignments": ["restaurant_id", "start_date"],
}


def run():
    """Produce cleaned tables without consulting the defect manifest."""
    cfg = config()
    audit = []
    tables = {}

    def log(table, rule, count, action):
        audit.append(
            {
                "table": table,
                "rule": rule,
                "affected_rows": int(count),
                "action": action,
            }
        )

    for name, keys in PRIMARY_KEYS.items():
        frame = read(name, RAW)
        count = len(frame)
        frame = frame.drop_duplicates().reset_index(drop=True)
        log(name, "Exact duplicate records", count - len(frame), "Removed")
        if frame.duplicated(keys).any():
            raise ValueError(
                f"Conflicting primary keys in {name}; manual resolution required"
            )
        if frame[keys].isna().any().any():
            raise ValueError(f"Null primary key in {name}")
        tables[name] = frame

    products = tables["products"]
    aliases = {
        "main meals": "Mains",
        "mains": "Mains",
        "salads": "Salads",
        "sides": "Sides",
        "drinks": "Drinks",
        "desserts": "Desserts",
    }
    fixed = products.category.str.strip().str.lower().map(aliases)
    if fixed.isna().any():
        raise ValueError("Unknown product category requires explicit mapping")
    log(
        "products",
        "Category aliases",
        fixed.ne(products.category).sum(),
        "Mapped to canonical categories",
    )
    products["category"] = fixed
    approved_catalog = json.loads((ROOT / "config/product_categories.json").read_text())
    expected_category = products.product_name.map(approved_catalog)
    if expected_category.isna().any():
        raise ValueError("Product absent from approved menu taxonomy")
    log(
        "products",
        "Category inconsistent with approved menu taxonomy",
        expected_category.ne(products.category).sum(),
        "Corrected using checked-in business reference",
    )
    products["category"] = expected_category
    stores = tables["restaurants"]
    valid_stores, valid_products = set(stores.restaurant_id), set(products.product_id)
    # Validate foreign keys before any aggregation.
    for name, frame in tables.items():
        if (
            "restaurant_id" in frame
            and not frame.restaurant_id.isin(valid_stores).all()
        ):
            raise ValueError(f"Unknown restaurant reference in {name}")
        if (
            "product_id" in frame
            and name != "transactions"
            and not frame.product_id.isin(valid_products).all()
        ):
            raise ValueError(f"Unknown product reference in {name}")

    tx = tables["transactions"]
    canonical = tx.restaurant_id.map(stores.set_index("restaurant_id").restaurant_name)
    log(
        "transactions",
        "Store name inconsistent with restaurant_id",
        canonical.ne(tx.restaurant_name).sum(),
        "Replaced from restaurant master",
    )
    tx["restaurant_name"] = canonical
    ts = pd.to_datetime(tx.timestamp_local, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    rules = {
        "Missing order identifier": tx.order_id.isna(),
        "Invalid product foreign key": ~tx.product_id.isin(valid_products),
        "Invalid timestamp": ts.isna()
        | ~ts.between(
            pd.Timestamp(cfg["start_date"]),
            pd.Timestamp(cfg["end_date"])
            + pd.Timedelta(hours=23, minutes=59, seconds=59),
        ),
        "Outside trading hours": ts.notna() & ~ts.dt.hour.between(11, 21),
        "Invalid quantity": ~tx.quantity.between(1, 20),
        "Invalid monetary values": ~np.isfinite(
            tx[
                [
                    "net_revenue",
                    "list_revenue",
                    "discount_amount",
                    "gst_amount",
                    "ingredient_cost",
                ]
            ]
        ).all(axis=1)
        | tx[
            [
                "net_revenue",
                "list_revenue",
                "discount_amount",
                "gst_amount",
                "ingredient_cost",
            ]
        ]
        .lt(0)
        .any(axis=1)
        | tx.discount_amount.gt(tx.list_revenue),
        "Invalid channel category": ~tx.channel.isin(
            ["Dine-in", "Takeaway", "Delivery"]
        ),
        "Revenue reconciliation": (
            tx.list_revenue - tx.discount_amount - tx.net_revenue
        ).abs()
        > 0.011,
        "GST reconciliation": (tx.net_revenue * 0.10 - tx.gst_amount).abs() > 0.011,
    }
    invalid = pd.Series(False, index=tx.index)
    reasons = pd.Series("", index=tx.index)
    for rule, mask in rules.items():
        mask = mask.fillna(True)
        invalid |= mask
        reasons.loc[mask] += rule + "; "
        log("transactions", rule, mask.sum(), "Quarantine complete affected order")
    bad_orders = set(tx.loc[invalid, "order_id"])
    rejected = tx.order_id.isin(bad_orders)
    quarantined = tx.loc[rejected].copy()
    quarantined["quality_reason"] = reasons.loc[rejected].replace(
        "", "Companion line in rejected order"
    )
    save(quarantined, PROCESSED / "quarantine_transactions.csv")
    log(
        "transactions",
        "Complete-order quarantine (including companion lines)",
        rejected.sum(),
        "Excluded from financial and order KPIs",
    )
    tx = tx.loc[~rejected].copy()
    tx["product_id"] = tx.product_id.astype(int)
    tx["timestamp_local"] = ts.loc[~rejected].dt.strftime("%Y-%m-%d %H:%M:%S")
    tx["business_date"] = ts.loc[~rejected].dt.strftime("%Y-%m-%d")
    tx["month"] = tx.business_date.str[:7]
    tx["hour"] = ts.loc[~rejected].dt.hour
    tx["daypart"] = np.where(tx.hour < 16, "Lunch", "Dinner")
    tables["transactions"] = tx
    valid_orders = set(tx.order_id)
    # Preserve surveys but explicitly unlink lost orders; never imply a matched survey.
    fb = tables["customer_feedback"]
    invalid_score = fb.overall_score.notna() & ~fb.overall_score.between(1, 5)
    log(
        "customer_feedback",
        "Invalid satisfaction score",
        invalid_score.sum(),
        "Set null; retained survey",
    )
    fb.loc[invalid_score, "overall_score"] = np.nan
    missing_link = fb.order_id.notna() & ~fb.order_id.isin(valid_orders)
    log(
        "customer_feedback",
        "Order quarantined",
        missing_link.sum(),
        "Order link set null",
    )
    fb.loc[missing_link, "order_id"] = np.nan
    for name in ("delivery", "loyalty"):
        frame = tables[name]
        lost = frame.order_id.notna() & ~frame.order_id.isin(valid_orders)
        save(frame.loc[lost], PROCESSED / f"quarantine_{name}.csv")
        log(name, "Order quarantined", lost.sum(), "Linked event excluded")
        tables[name] = frame.loc[~lost].copy()

    labour = tables["labour"]
    duration = (
        pd.to_datetime(labour.actual_end) - pd.to_datetime(labour.actual_start)
    ).dt.total_seconds() / 3600
    expected_paid = duration - labour.break_hours
    bad_hours = ~labour.paid_hours.between(0, 16) | (
        labour.paid_hours - expected_paid
    ).abs().gt(0.01)
    if (~expected_paid.between(0, 16)).any():
        raise ValueError("Unrecoverable shift timestamps")
    labour.loc[bad_hours, "paid_hours"] = expected_paid.loc[bad_hours]
    log(
        "labour",
        "Paid hours inconsistent with shift duration and break",
        bad_hours.sum(),
        "Recomputed from actual timestamps",
    )
    lookup = labour.merge(stores[["restaurant_id", "state"]], on="restaurant_id").merge(
        tables["calendar"][["business_date", "state", "weekday", "is_public_holiday"]],
        on=["business_date", "state"],
    )
    lookup["is_weekend"] = lookup.weekday.ge(5)
    group_keys = ["role", "is_weekend", "is_public_holiday"]
    median_rate = lookup.groupby(group_keys).hourly_cost.transform("median")
    missing_rate = lookup.hourly_cost.isna()
    if median_rate.loc[missing_rate].isna().any():
        raise ValueError("Hourly rate cannot be inferred from comparable shifts")
    lookup.loc[missing_rate, "hourly_cost"] = median_rate.loc[missing_rate]
    repaired = lookup.set_index("shift_id").hourly_cost
    labour["rate_imputed"] = labour.hourly_cost.isna().astype(int)
    labour["hourly_cost"] = labour.shift_id.map(repaired)
    labour["labour_cost"] = (labour.paid_hours * labour.hourly_cost).round(2)
    log(
        "labour",
        "Missing hourly cost",
        missing_rate.sum(),
        "Median of same role/weekend/holiday class; flagged",
    )
    waste = tables["waste"]
    bad_waste = waste.waste_units.lt(0) | waste.waste_cost.lt(0)
    save(waste.loc[bad_waste], PROCESSED / "quarantine_waste.csv")
    tables["waste"] = waste.loc[~bad_waste].copy()
    log(
        "waste",
        "Negative waste quantities",
        bad_waste.sum(),
        "Quarantined; not silently converted to zero",
    )
    # All optional missing values remain meaningful; no global fillna(0).
    for name, frame in tables.items():
        save(frame, PROCESSED / f"{name}.csv")
    quality = pd.DataFrame(audit)
    save(quality, REPORTS / "exports/data_quality_audit.csv")
    summary = {
        "raw_lines_after_dedup": len(rejected),
        "clean_lines": len(tx),
        "clean_orders": tx.order_id.nunique(),
        "quarantined_orders": len(bad_orders),
        "clean_revenue": round(tx.net_revenue.sum(), 2),
        "quarantined_revenue": round(quarantined.net_revenue.sum(), 2),
        "clean_rows": {name: len(frame) for name, frame in tables.items()},
    }
    (REPORTS / "quality_summary.json").write_text(json.dumps(summary, indent=2))
    lines = [
        "# Data quality report",
        "",
        "Generated from rule checks; the cleaning pipeline does not use hidden generation truth.",
        "",
        f"Retained **{summary['clean_orders']:,} complete orders** and **{len(tx):,} lines**. Quarantined {len(bad_orders):,} complete orders to avoid partial baskets.",
        "",
        "| Table | Rule | Rows | Action |",
        "|---|---|---:|---|",
    ]
    lines += [
        f"| {r.table} | {r.rule} | {r.affected_rows:,} | {r.action} |"
        for r in quality.itertuples()
        if r.affected_rows
    ]
    lines += [
        "",
        "Counts can overlap across rules. The final quarantine row is the union, including companion lines. Raw exports remain unchanged. Null customer IDs represent anonymous orders, not errors. Missing survey answers remain null. Lost-order surveys remain in store satisfaction but are excluded from matched order analyses.",
        "",
        "Labour-rate inference is appropriate only for this synthetic roster's known rate classes. A production system would require an authoritative payroll rate table.",
    ]
    (REPORTS / "data_quality_report.md").write_text("\n".join(lines) + "\n")
    print(
        f"Cleaned: {summary['clean_orders']:,} orders; quarantined {len(bad_orders):,} orders.",
        flush=True,
    )
    return summary


if __name__ == "__main__":
    run()
