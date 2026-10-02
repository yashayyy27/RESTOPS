"""Simulate connected operational exports, then inject auditable defects.

All people, companies and business results are fictional. Latent operating
mechanisms are used only in simulation, never as analytical model features.
"""

import json

import holidays
import numpy as np
import pandas as pd

from .common import RAW, ROOT, config, save


def dimensions():
    """Create Australian restaurant and product master data."""
    locations = [
        ("Sydney Central", "NSW", "CBD"),
        ("Parramatta", "NSW", "Shopping centre"),
        ("Bondi", "NSW", "Suburban"),
        ("Newcastle", "NSW", "Regional"),
        ("Chatswood", "NSW", "Shopping centre"),
        ("Wollongong", "NSW", "Regional"),
        ("Melbourne Central", "VIC", "CBD"),
        ("Richmond", "VIC", "Suburban"),
        ("Chadstone", "VIC", "Shopping centre"),
        ("Geelong", "VIC", "Regional"),
        ("Southbank", "VIC", "CBD"),
        ("Ballarat", "VIC", "Regional"),
        ("Brisbane Central", "QLD", "CBD"),
        ("South Brisbane", "QLD", "Suburban"),
        ("Gold Coast", "QLD", "Suburban"),
        ("Chermside", "QLD", "Shopping centre"),
        ("Toowoomba", "QLD", "Regional"),
        ("Sunshine Coast", "QLD", "Suburban"),
    ]
    stores = pd.DataFrame(
        locations, columns=["restaurant_name", "state", "location_type"]
    )
    stores.insert(0, "restaurant_id", np.arange(1, 19))
    stores["area"] = stores.state.map({"NSW": "East", "VIC": "South", "QLD": "North"})
    stores["timezone"] = stores.state.map(
        {
            "NSW": "Australia/Sydney",
            "VIC": "Australia/Melbourne",
            "QLD": "Australia/Brisbane",
        }
    )
    stores["seats"] = [
        90,
        76,
        64,
        70,
        82,
        65,
        96,
        68,
        88,
        66,
        85,
        60,
        92,
        72,
        78,
        86,
        62,
        74,
    ]
    stores["opening_date"] = "2021-01-01"
    stores["open_hour"] = 11
    stores["close_hour"] = 22
    menu = [
        ("Classic Burger", "Mains", 22, 7.3),
        ("Chicken Burger", "Mains", 23, 7.5),
        ("Veggie Burger", "Mains", 21, 6.3),
        ("Grilled Barramundi", "Mains", 31, 12.8),
        ("Steak Plate", "Mains", 35, 14.5),
        ("Chicken Bowl", "Mains", 24, 7.8),
        ("Pasta Primavera", "Mains", 23, 6.4),
        ("Fish Tacos", "Mains", 25, 9.2),
        ("Garden Salad", "Salads", 17, 4.9),
        ("Chicken Salad", "Salads", 22, 7.1),
        ("Greek Salad", "Salads", 19, 5.5),
        ("Chips", "Sides", 8, 1.8),
        ("Sweet Potato Chips", "Sides", 10, 2.6),
        ("Garlic Bread", "Sides", 7, 1.5),
        ("Coleslaw", "Sides", 6, 1.4),
        ("Flat White", "Drinks", 5, 1.2),
        ("Lemonade", "Drinks", 6, 1.0),
        ("Iced Tea", "Drinks", 6, 1.3),
        ("Sparkling Water", "Drinks", 5, 0.9),
        ("Fresh Juice", "Drinks", 8, 2.2),
        ("Chocolate Brownie", "Desserts", 10, 2.6),
        ("Cheesecake", "Desserts", 12, 3.7),
        ("Ice Cream", "Desserts", 8, 1.9),
        ("Seasonal Tart", "Desserts", 11, 3.4),
    ]
    products = pd.DataFrame(
        menu,
        columns=[
            "product_name",
            "category",
            "menu_price_ex_gst",
            "standard_ingredient_cost",
        ],
    )
    products.insert(0, "product_id", np.arange(1, len(products) + 1))
    return stores, products


def calendar(dates):
    """State-level public holidays from the Python holidays package.

    School-holiday indicators use illustrative seasonal windows, not official
    school calendars. They must not be reused for real staffing decisions.
    """
    parts = []
    for state in ("NSW", "VIC", "QLD"):
        cal = pd.DataFrame({"business_date": dates, "state": state})
        public = holidays.Australia(subdiv=state, years=sorted(set(dates.year)))
        cal["holiday_name"] = [public.get(d.date(), "") for d in dates]
        cal["is_public_holiday"] = cal.holiday_name.ne("").astype(int)
        cal["weekday"] = dates.dayofweek
        cal["is_weekend"] = (dates.dayofweek >= 5).astype(int)
        cal["month"] = dates.month
        cal["season"] = np.select(
            [
                dates.month.isin([12, 1, 2]),
                dates.month.isin([3, 4, 5]),
                dates.month.isin([6, 7, 8]),
            ],
            ["Summer", "Autumn", "Winter"],
            default="Spring",
        )
        cal["school_holiday_proxy"] = (
            (dates.month.isin([1, 4, 7, 9, 12]))
            & ((dates.day <= 14) | (dates.month.isin([1, 12])))
        ).astype(int)
        parts.append(cal)
    return pd.concat(parts, ignore_index=True)


def promotions(stores, dates):
    """Create non-overlapping, store-specific campaigns with known costs."""
    rows = []
    for store in stores.itertuples():
        for year in (2024, 2025):
            for campaign, month in enumerate((3, 6, 10)):
                start = pd.Timestamp(year, month, 4) + pd.Timedelta(
                    days=(store.restaurant_id % 3) * 21
                )
                rows.append(
                    {
                        "promotion_id": f"P{store.restaurant_id:02d}{year}{month:02d}",
                        "restaurant_id": store.restaurant_id,
                        "campaign_name": [
                            "Local Lunch",
                            "Winter Value",
                            "Spring Social",
                        ][campaign],
                        "start_date": start,
                        "end_date": start + pd.Timedelta(days=13),
                        "discount_rate": [0.10, 0.20, 0.15][campaign],
                        "eligible_category": "All",
                        "campaign_cost": [420, 650, 520][campaign],
                    }
                )
    return pd.DataFrame(rows)


def inject_defects(tables, rng):
    """Modify raw exports; store defect locations for independent QA only."""
    manifest = []

    def damage(name, column, count, value, kind):
        frame = tables[name]
        idx = rng.choice(len(frame), min(count, len(frame)), replace=False)
        frame.loc[idx, column] = value
        manifest.append(
            {
                "table": name,
                "column": column,
                "type": kind,
                "injected_rows": len(idx),
                "row_indices": idx.tolist(),
            }
        )

    damage(
        "transactions",
        "restaurant_name",
        2600,
        "  SOUTHERN TABLE - SYDNEY  ",
        "name_alias",
    )
    damage("transactions", "product_id", 800, np.nan, "missing_key")
    damage(
        "transactions",
        "timestamp_local",
        650,
        "2025-99-99 25:90:00",
        "invalid_timestamp",
    )
    damage("transactions", "quantity", 350, 999, "quantity_outlier")
    damage("transactions", "net_revenue", 250, -900, "invalid_revenue")
    damage("products", "category", 2, " Main meals ", "category_alias")
    damage("labour", "hourly_cost", 130, np.nan, "missing_rate")
    damage("labour", "paid_hours", 60, 80, "invalid_hours")
    damage("customer_feedback", "overall_score", 300, np.nan, "unanswered_survey")
    damage("customer_feedback", "overall_score", 50, 9, "invalid_rating")
    damage("waste", "waste_units", 70, -5, "invalid_waste")
    for name, count in (
        ("transactions", 2300),
        ("labour", 180),
        ("customer_feedback", 100),
    ):
        sample = tables[name].sample(count, random_state=42)
        tables[name] = pd.concat([tables[name], sample], ignore_index=True)
        manifest.append(
            {"table": name, "type": "exact_duplicate", "injected_rows": count}
        )
    return manifest


def run():
    """Write all simulated source-system exports using one random seed."""
    cfg = config()
    rng = np.random.default_rng(cfg["seed"])
    stores, products = dimensions()
    dates = pd.date_range(cfg["start_date"], cfg["end_date"])
    cal = calendar(dates)
    promo = promotions(stores, dates)
    daily = pd.MultiIndex.from_product(
        [stores.restaurant_id, dates], names=["restaurant_id", "business_date"]
    ).to_frame(index=False)
    daily = daily.merge(stores, on="restaurant_id").merge(
        cal, on=["business_date", "state"]
    )
    sidx = daily.restaurant_id.to_numpy() - 1
    scale = np.array(
        [
            1.28,
            1.10,
            0.96,
            0.88,
            1.08,
            0.82,
            1.32,
            1.03,
            1.15,
            0.87,
            1.12,
            0.79,
            1.25,
            0.99,
            1.07,
            1.16,
            0.83,
            1.02,
        ]
    )
    efficiency = np.array(
        [
            1.02,
            0.97,
            1.04,
            0.91,
            1.00,
            0.86,
            1.05,
            0.98,
            0.99,
            0.92,
            0.96,
            0.90,
            1.02,
            0.94,
            0.88,
            1.01,
            0.91,
            0.96,
        ]
    )
    promo_map = {}
    for row in promo.itertuples():
        for date in pd.date_range(row.start_date, row.end_date):
            promo_map[(row.restaurant_id, date)] = (row.promotion_id, row.discount_rate)
    pairs = [
        promo_map.get((r, d), ("", 0.0))
        for r, d in zip(daily.restaurant_id, daily.business_date)
    ]
    daily["promotion_id"] = [p[0] for p in pairs]
    daily["discount_rate"] = [p[1] for p in pairs]
    day_number = (daily.business_date - dates[0]).dt.days.to_numpy()
    weekly = np.array([0.82, 0.84, 0.94, 1.02, 1.21, 1.39, 1.16])[daily.weekday]
    cbd = daily.location_type.eq("CBD").to_numpy()
    weekly *= np.where(cbd & daily.is_weekend.eq(1), 0.70, 1.0)
    seasonal = 1 + 0.11 * np.cos(2 * np.pi * day_number / 365.25)
    drift = 1 + 0.07 * day_number / 730
    # A mid-2025 scheduling deterioration at two stores is observable, not labelled.
    deterioration = daily.restaurant_id.isin([6, 15]) & daily.business_date.ge(
        "2025-06-01"
    )
    daily["efficiency"] = efficiency[sidx] - 0.12 * deterioration
    # Discounts may increase volumes; large discounts can still destroy contribution.
    uplift = np.where(
        daily.discount_rate.eq(0.20), 0.08, np.where(daily.discount_rate.gt(0), 0.17, 0)
    )
    demand = cfg["base_daily_orders"] * scale[sidx] * weekly * seasonal * drift
    demand *= np.where(daily.is_public_holiday.eq(1), np.where(cbd, 0.76, 1.18), 1)
    demand *= 1 - 0.045 * deterioration
    # Evaluation-only expected treatment mechanism, isolated from source exports.
    truth = daily[["restaurant_id", "business_date", "promotion_id"]].copy()
    truth["baseline_expected_orders"] = demand
    truth["treatment_expected_orders"] = demand * uplift
    truth["known_order_uplift"] = uplift
    truth["business_date"] = truth.business_date.dt.strftime("%Y-%m-%d")
    save(
        truth[truth.promotion_id.notna()], ROOT / "data/validation/promotion_truth.csv"
    )
    demand *= 1 + uplift
    daily["expected_orders"] = demand
    daily["orders"] = rng.poisson(
        demand * rng.lognormal(-0.5 * 0.10**2, 0.10, len(daily))
    )
    orders = daily.loc[daily.index.repeat(daily.orders)].reset_index(drop=True)
    n = len(orders)
    order_ids = np.arange(1, n + 1)
    hours = rng.choice(
        [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
        n,
        p=[0.05, 0.15, 0.13, 0.07, 0.03, 0.03, 0.05, 0.14, 0.19, 0.11, 0.05],
    )
    timestamps = (
        orders.business_date
        + pd.to_timedelta(hours, unit="h")
        + pd.to_timedelta(rng.integers(0, 3600, n), unit="s")
    )
    channels = rng.choice(["Dine-in", "Takeaway", "Delivery"], n, p=[0.58, 0.21, 0.21])
    identified = rng.random(n) < 0.62
    # Anonymous store-local customers; uneven visit frequency creates useful cohorts.
    weights = 1 / np.arange(1, 3001, dtype=float) ** 0.58
    weights /= weights.sum()
    local_customer = rng.choice(3000, n, p=weights) + 1
    customers = (orders.restaurant_id.to_numpy() - 1) * 3000 + local_customer
    customers = np.where(identified, customers, 0)
    counts = 1 + rng.binomial(3, 0.55, n)
    parent = np.repeat(np.arange(n), counts)
    product_weights = np.array(
        [10, 9, 5, 4, 3, 8, 6, 6, 4, 4, 3, 8, 5, 4, 2, 7, 7, 5, 3, 4, 4, 3, 3, 2],
        dtype=float,
    )
    pids = rng.choice(
        len(products), len(parent), p=product_weights / product_weights.sum()
    )
    qty = rng.choice([1, 2], len(parent), p=[0.90, 0.10])
    price = products.menu_price_ex_gst.to_numpy()[pids] * (
        1 + 0.025 * (orders.business_date.dt.year.to_numpy()[parent] - 2024)
    )
    cost = products.standard_ingredient_cost.to_numpy()[pids] * (
        1 + 0.035 * (orders.business_date.dt.year.to_numpy()[parent] - 2024)
    )
    list_sales = np.round(price * qty, 2)
    discount = np.round(list_sales * orders.discount_rate.to_numpy()[parent], 2)
    net = list_sales - discount
    tx = pd.DataFrame(
        {
            "transaction_line_id": np.arange(1, len(parent) + 1),
            "order_id": order_ids[parent],
            "restaurant_id": orders.restaurant_id.to_numpy()[parent],
            "restaurant_name": orders.restaurant_name.to_numpy()[parent],
            "timestamp_local": timestamps.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy()[
                parent
            ],
            "product_id": pids + 1,
            "quantity": qty,
            "channel": channels[parent],
            "customer_id": np.where(customers[parent] == 0, np.nan, customers[parent]),
            "promotion_id": orders.promotion_id.to_numpy()[parent],
            "list_revenue": list_sales,
            "discount_amount": discount,
            "net_revenue": net,
            "gst_amount": np.round(net * 0.10, 2),
            "ingredient_cost": np.round(cost * qty, 2),
        }
    )
    order_revenue = np.bincount(parent, weights=net, minlength=n)
    # Roster capacity differs by role; service pressure affects simulated experience.
    labour_rows = []
    daily_paid = np.zeros(len(daily))
    for i, row in enumerate(daily.itertuples()):
        for part, hour, duration, share in [
            ("Lunch", 11, 5, 0.43),
            ("Dinner", 16, 6, 0.57),
        ]:
            planned = row.expected_orders * share
            service = max(1, int(np.ceil(planned / (duration * 6 * row.efficiency))))
            if row.restaurant_id in (6, 15):
                service += int(row.weekday < 4)  # Static rosters on quiet weekdays.
                service -= int(row.weekday >= 4 and service > 1)
            kitchen = max(1, int(np.ceil(planned / (duration * 8))))
            for role, headcount, rate in [
                ("Service", service, 30),
                ("Kitchen", kitchen, 34),
                ("Manager", 1, 39),
            ]:
                for person in range(headcount):
                    hours_paid = duration - 0.5 if role != "Manager" else 2.0
                    multiplier = (
                        1.6
                        if row.is_public_holiday
                        else (1.25 if row.weekday >= 5 else 1)
                    )
                    start = row.business_date + pd.Timedelta(hours=hour)
                    shift_duration = 2.0 if role == "Manager" else duration
                    labour_rows.append(
                        {
                            "shift_id": len(labour_rows) + 1,
                            "restaurant_id": row.restaurant_id,
                            "employee_id": f"E{row.restaurant_id:02d}{role[0]}{person:02d}",
                            "role": role,
                            "business_date": row.business_date,
                            "daypart": part,
                            "scheduled_start": start,
                            "scheduled_end": start + pd.Timedelta(hours=shift_duration),
                            "actual_start": start,
                            "actual_end": start + pd.Timedelta(hours=shift_duration),
                            "break_hours": shift_duration - hours_paid,
                            "paid_hours": hours_paid,
                            "hourly_cost": rate * multiplier,
                        }
                    )
                    daily_paid[i] += hours_paid
    labour = pd.DataFrame(labour_rows)
    daily["paid_hours"] = daily_paid
    daily["service_hours"] = (
        labour[labour.role.eq("Service")]
        .groupby(["restaurant_id", "business_date"])
        .paid_hours.sum()
        .to_numpy()
    )
    order_daily = np.repeat(np.arange(len(daily)), daily.orders)
    pressure = orders.orders.to_numpy() / (
        daily.service_hours.to_numpy()[order_daily] * 6
    )
    base_score = (
        4.45
        - 0.68 * np.maximum(pressure - 0.75, 0)
        - 1.2 * (1 - orders.efficiency.to_numpy())
    )
    feedback_idx = np.flatnonzero(rng.random(n) < 0.075)
    feedback = pd.DataFrame(
        {
            "feedback_id": np.arange(1, len(feedback_idx) + 1),
            "order_id": order_ids[feedback_idx],
            "restaurant_id": orders.restaurant_id.to_numpy()[feedback_idx],
            "business_date": orders.business_date.to_numpy()[feedback_idx],
            "overall_score": np.clip(
                np.rint(
                    base_score[feedback_idx] + rng.normal(0, 0.65, len(feedback_idx))
                ),
                1,
                5,
            ),
            "food_score": np.clip(
                np.rint(4.25 + rng.normal(0, 0.6, len(feedback_idx))), 1, 5
            ),
            "service_score": np.clip(
                np.rint(
                    base_score[feedback_idx] + rng.normal(0, 0.6, len(feedback_idx))
                ),
                1,
                5,
            ),
        }
    )
    member = np.flatnonzero(identified)
    loyalty = pd.DataFrame(
        {
            "customer_id": customers[member],
            "restaurant_id": orders.restaurant_id.to_numpy()[member],
            "order_id": order_ids[member],
            "event_date": orders.business_date.to_numpy()[member],
            "event_type": "Earn",
            "points": np.floor(order_revenue[member]).astype(int),
        }
    )
    enrol = (
        loyalty.sort_values(["event_date", "order_id"])
        .drop_duplicates("customer_id")
        .copy()
    )
    enrol["event_type"] = "Enroll"
    enrol["order_id"] = np.nan
    enrol["points"] = 0
    redeem = loyalty.sample(frac=0.08, random_state=42).copy()
    redeem["event_type"] = "Redeem"
    redeem["points"] = -100
    loyalty = pd.concat([enrol, loyalty, redeem], ignore_index=True)
    loyalty.insert(0, "loyalty_event_id", np.arange(1, len(loyalty) + 1))
    deliveries = np.flatnonzero(channels == "Delivery")
    delivery_delay = np.maximum(0, pressure[deliveries] - 0.8) * 18 + rng.normal(
        1, 7, len(deliveries)
    )
    delivery = pd.DataFrame(
        {
            "order_id": order_ids[deliveries],
            "restaurant_id": orders.restaurant_id.to_numpy()[deliveries],
            "promised_minutes": 40,
            "actual_minutes": np.maximum(18, 40 + delivery_delay).round(1),
            "commission_cost": np.round(order_revenue[deliveries] * 0.25, 2),
            "delivery_fee": 0.0,
            "status": "Completed",
        }
    )
    sold = (
        tx.groupby(["restaurant_id", "product_id", tx.timestamp_local.str[:10]])
        .quantity.sum()
        .reset_index()
    )
    sold.columns = ["restaurant_id", "product_id", "business_date", "sold_units"]
    waste = sold.merge(products, on="product_id").merge(
        daily[["restaurant_id", "business_date", "efficiency"]].assign(
            business_date=lambda x: x.business_date.dt.strftime("%Y-%m-%d")
        ),
        on=["restaurant_id", "business_date"],
    )
    rate = (
        0.025
        + (1 - waste.efficiency) * 0.20
        + 0.012 * waste.category.isin(["Salads", "Mains"])
    )
    waste["waste_units"] = rng.poisson(waste.sold_units * rate)
    waste["waste_cost"] = (
        waste.waste_units
        * waste.standard_ingredient_cost
        * np.where(waste.business_date.str[:4].eq("2025"), 1.035, 1)
    ).round(2)
    waste["reason"] = rng.choice(
        ["Over-preparation", "Spoilage", "Preparation error"],
        len(waste),
        p=[0.55, 0.30, 0.15],
    )
    waste = waste[
        [
            "restaurant_id",
            "product_id",
            "business_date",
            "waste_units",
            "waste_cost",
            "reason",
        ]
    ]
    waste.insert(0, "waste_id", np.arange(1, len(waste) + 1))
    months = pd.date_range(dates[0], dates[-1], freq="MS")
    costs_rows, target_rows = [], []
    for store in stores.itertuples():
        for month in months:
            for category, amount in [
                ("Rent", 6400),
                ("Utilities", 1500),
                ("Other overhead", 2000),
            ]:
                costs_rows.append(
                    {
                        "restaurant_id": store.restaurant_id,
                        "month": month.strftime("%Y-%m"),
                        "cost_category": category,
                        "amount": round(
                            amount
                            * scale[store.restaurant_id - 1]
                            * rng.uniform(0.94, 1.06),
                            2,
                        ),
                    }
                )
            # Independent budget assumptions, not targets reverse-engineered from results.
            budget = (
                cfg["base_daily_orders"]
                * scale[store.restaurant_id - 1]
                * month.days_in_month
                * 52
                * (1.06 if month.year == 2025 else 1)
            )
            target_rows.append(
                {
                    "restaurant_id": store.restaurant_id,
                    "month": month.strftime("%Y-%m"),
                    "revenue_target": round(budget, 2),
                    "operating_margin_target": 0.16,
                    "labour_pct_target": 0.30,
                    "waste_pct_target": 0.04,
                    "satisfaction_target": 4.2,
                }
            )
    costs = pd.DataFrame(costs_rows)
    costs.insert(0, "cost_id", np.arange(1, len(costs) + 1))
    assignments = pd.DataFrame(
        {
            "restaurant_id": stores.restaurant_id,
            "manager_id": [f"M{i:02d}" for i in range(1, 19)],
            "start_date": cfg["start_date"],
            "end_date": cfg["end_date"],
        }
    )
    tables = dict(
        restaurants=stores,
        products=products,
        transactions=tx,
        labour=labour,
        customer_feedback=feedback,
        loyalty=loyalty,
        promotions=promo,
        waste=waste,
        targets=pd.DataFrame(target_rows),
        operating_costs=costs,
        delivery=delivery,
        calendar=cal,
        manager_assignments=assignments,
    )
    manifest = inject_defects(tables, rng)
    for name, frame in tables.items():
        save(frame, RAW / f"{name}.csv")
    metadata = {
        "seed": cfg["seed"],
        "configuration": cfg,
        "orders_before_defects": n,
        "lines_before_defects": len(tx),
        "raw_rows": {name: len(frame) for name, frame in tables.items()},
        "defects": manifest,
    }
    (RAW / "generation_manifest.json").write_text(json.dumps(metadata, indent=2))
    print(
        f"Generated {n:,} orders / {len(tx):,} lines across {len(dates)} days.",
        flush=True,
    )
    return metadata


if __name__ == "__main__":
    run()
