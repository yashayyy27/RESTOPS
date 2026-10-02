"""Build analysis tables at explicit grains; aggregate facts before joining."""

import numpy as np
import pandas as pd

from .common import PROCESSED, TABLEAU, config, read, save


def run():
    """Materialise orders, store-day financials, products and hourly capacity."""
    tx = read("transactions")
    orders = (
        tx.groupby("order_id", sort=False)
        .agg(
            restaurant_id=("restaurant_id", "first"),
            business_date=("business_date", "first"),
            timestamp_local=("timestamp_local", "first"),
            hour=("hour", "first"),
            daypart=("daypart", "first"),
            channel=("channel", "first"),
            customer_id=("customer_id", "first"),
            promotion_id=("promotion_id", "first"),
            revenue=("net_revenue", "sum"),
            ingredient_cost=("ingredient_cost", "sum"),
            discount_amount=("discount_amount", "sum"),
            units=("quantity", "sum"),
        )
        .reset_index()
    )
    save(orders, PROCESSED / "orders.csv")
    product = (
        tx.groupby(["restaurant_id", "month", "product_id", "channel"])
        .agg(
            revenue=("net_revenue", "sum"),
            ingredient_cost=("ingredient_cost", "sum"),
            list_revenue=("list_revenue", "sum"),
            discount_amount=("discount_amount", "sum"),
            units=("quantity", "sum"),
            orders_with_product=("order_id", "nunique"),
        )
        .reset_index()
        .merge(read("products"), on="product_id")
    )
    product["gross_contribution"] = product.revenue - product.ingredient_cost
    save(product, TABLEAU / "product_month.csv")
    del tx
    stores, cal = read("restaurants"), read("calendar")
    daily = stores.merge(cal, on="state")
    keys = ["restaurant_id", "business_date"]
    sales = (
        orders.groupby(keys)
        .agg(
            revenue=("revenue", "sum"),
            ingredient_cost=("ingredient_cost", "sum"),
            transactions=("order_id", "size"),
            discounts=("discount_amount", "sum"),
            identified_orders=("customer_id", "count"),
        )
        .reset_index()
    )
    daily = daily.merge(sales, on=keys, how="left")
    labour = read("labour")
    roster = (
        labour.groupby(keys)
        .agg(labour_cost=("labour_cost", "sum"), paid_hours=("paid_hours", "sum"))
        .reset_index()
    )
    service = (
        labour[labour.role.eq("Service")]
        .groupby(keys)
        .paid_hours.sum()
        .rename("service_hours")
        .reset_index()
    )
    daily = daily.merge(roster, on=keys, how="left").merge(service, on=keys, how="left")
    waste = read("waste").groupby(keys).waste_cost.sum().reset_index()
    waste_detail = (
        read("waste")
        .groupby(keys + ["product_id", "reason"])[["waste_units", "waste_cost"]]
        .sum()
        .reset_index()
    )
    waste_detail = waste_detail.merge(
        read("products")[["product_id", "product_name", "category"]],
        on="product_id",
        validate="many_to_one",
    )
    save(waste_detail, TABLEAU / "waste_detail.csv")
    daily = daily.merge(waste, on=keys, how="left")
    fb = (
        read("customer_feedback")
        .groupby(keys)
        .agg(
            score_sum=("overall_score", "sum"),
            survey_responses=("overall_score", "count"),
        )
        .reset_index()
    )
    daily = daily.merge(fb, on=keys, how="left")
    delivery = read("delivery").merge(
        orders[["order_id", "business_date"]], on="order_id", validate="one_to_one"
    )
    delivery["late_delivery"] = delivery.actual_minutes.gt(
        delivery.promised_minutes
    ).astype(int)
    delivery_daily = (
        delivery.groupby(keys)
        .agg(
            commission_cost=("commission_cost", "sum"),
            deliveries=("order_id", "count"),
            late_deliveries=("late_delivery", "sum"),
        )
        .reset_index()
    )
    daily = daily.merge(delivery_daily, on=keys, how="left")
    daily["month"] = daily.business_date.str[:7]
    monthly_cost = (
        read("operating_costs")
        .groupby(["restaurant_id", "month"])
        .amount.sum()
        .rename("monthly_overheads")
        .reset_index()
    )
    daily = daily.merge(monthly_cost, on=["restaurant_id", "month"], how="left")
    daily["overhead_cost"] = (
        daily.monthly_overheads / pd.to_datetime(daily.business_date).dt.days_in_month
    )
    daily["campaign_cost"] = 0.0
    daily["promotion_id"] = None
    for promo in read("promotions").itertuples():
        mask = daily.restaurant_id.eq(
            promo.restaurant_id
        ) & daily.business_date.between(promo.start_date, promo.end_date)
        length = (
            pd.Timestamp(promo.end_date) - pd.Timestamp(promo.start_date)
        ).days + 1
        daily.loc[mask, "campaign_cost"] = promo.campaign_cost / length
        daily.loc[mask, "promotion_id"] = promo.promotion_id
    additive = [
        "revenue",
        "ingredient_cost",
        "transactions",
        "discounts",
        "identified_orders",
        "labour_cost",
        "paid_hours",
        "service_hours",
        "waste_cost",
        "score_sum",
        "survey_responses",
        "commission_cost",
        "deliveries",
        "late_deliveries",
    ]
    daily[additive] = daily[additive].fillna(0)
    daily["operating_profit"] = daily.revenue - daily[
        [
            "ingredient_cost",
            "labour_cost",
            "waste_cost",
            "commission_cost",
            "overhead_cost",
            "campaign_cost",
        ]
    ].sum(axis=1)
    daily["satisfaction_score"] = daily.score_sum / daily.survey_responses.replace(
        0, np.nan
    )
    save(daily, PROCESSED / "store_day.csv")
    save(daily, TABLEAU / "store_day.csv")
    # Paid time is spread uniformly within each observed shift; break timing unknown.
    hourly = (
        stores[["restaurant_id", "restaurant_name", "state", "area"]]
        .merge(
            pd.DataFrame({"business_date": sorted(daily.business_date.unique())}),
            how="cross",
        )
        .merge(pd.DataFrame({"hour": range(11, 22)}), how="cross")
    )
    hourly_sales = (
        orders.groupby(keys + ["hour"])
        .agg(transactions=("order_id", "size"), revenue=("revenue", "sum"))
        .reset_index()
    )
    hourly = hourly.merge(hourly_sales, on=keys + ["hour"], how="left")
    expanded = []
    for hour in range(11, 22):
        start = pd.to_datetime(labour.actual_start)
        end = pd.to_datetime(labour.actual_end)
        hour_start = pd.to_datetime(labour.business_date) + pd.Timedelta(hours=hour)
        overlap = (
            (
                end.clip(upper=hour_start + pd.Timedelta(hours=1))
                - start.clip(lower=hour_start)
            ).dt.total_seconds()
            / 3600
        ).clip(lower=0)
        duration = (end - start).dt.total_seconds() / 3600
        temp = labour[keys].copy()
        temp["hour"] = hour
        temp["paid_hours"] = overlap * labour.paid_hours / duration
        temp["service_hours"] = temp.paid_hours.where(labour.role.eq("Service"), 0)
        temp["labour_cost"] = temp.paid_hours * labour.hourly_cost
        expanded.append(temp)
    capacity = (
        pd.concat(expanded)
        .groupby(keys + ["hour"])[["paid_hours", "service_hours", "labour_cost"]]
        .sum()
        .reset_index()
    )
    hourly = hourly.merge(capacity, on=keys + ["hour"], how="left")
    hourly[["transactions", "revenue"]] = hourly[["transactions", "revenue"]].fillna(0)
    hourly["service_capacity_orders"] = hourly.service_hours * 6
    hourly["capacity_gap_orders"] = hourly.transactions - hourly.service_capacity_orders
    hourly["staffing_status"] = np.select(
        [
            hourly.capacity_gap_orders > 2,
            hourly.transactions < hourly.service_capacity_orders * 0.45,
        ],
        ["Pressure", "Spare capacity"],
        default="Balanced",
    )
    hourly["weekday"] = pd.to_datetime(hourly.business_date).dt.dayofweek
    hourly["daypart"] = np.where(hourly.hour < 16, "Lunch", "Dinner")
    save(hourly, PROCESSED / "store_hour.csv")
    save(hourly, TABLEAU / "store_hour.csv")
    print(
        "Built orders, daily finance, product mix and hourly capacity tables.",
        flush=True,
    )


if __name__ == "__main__":
    run()
