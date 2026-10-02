"""Hourly demand allocation and configurable staffing decision support."""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PlanningAssumptions:
    orders_per_service_hour: float = 6.0
    utilisation: float = 0.80
    minimum_service_staff: int = 1
    schedule_multiplier: float = 1.0
    demand_multiplier: float = 1.0
    loaded_hourly_wage: float = 35.0


def scheduled_hourly(labour):
    """Allocate scheduled paid hours, retaining actual hourly time separately."""
    start = pd.to_datetime(labour.scheduled_start)
    end = pd.to_datetime(labour.scheduled_end)
    duration = (end - start).dt.total_seconds() / 3600
    paid = duration - labour.break_hours
    if (duration <= 0).any() or (paid < 0).any():
        raise ValueError("Invalid scheduled shift or break")
    rows = []
    for hour in range(11, 22):
        left = pd.to_datetime(labour.business_date) + pd.Timedelta(hours=hour)
        overlap = (
            (
                end.clip(upper=left + pd.Timedelta(hours=1)) - start.clip(lower=left)
            ).dt.total_seconds()
            / 3600
        ).clip(lower=0)
        part = labour[["restaurant_id", "business_date"]].copy()
        part["hour"] = hour
        part["scheduled_paid_hours"] = overlap * paid / duration
        part["scheduled_service_hours"] = part.scheduled_paid_hours.where(
            labour.role.eq("Service"), 0
        )
        rows.append(part)
    result = (
        pd.concat(rows)
        .groupby(["restaurant_id", "business_date", "hour"])[
            ["scheduled_paid_hours", "scheduled_service_hours"]
        ]
        .sum()
        .reset_index()
    )
    if not np.isclose(result.scheduled_paid_hours.sum(), paid.sum(), atol=0.01):
        raise ValueError("Scheduled hours extend outside supported trading hours")
    return result


def hourly_plan(
    history_daily, history_hourly, forecasts, assumptions=PlanningAssumptions()
):
    """Disaggregate daily revenue using pre-origin basket value and weekday mix.

    Future schedule is a repeated historical weekday template, not a submitted
    roster. Empirical revenue bands become conditional demand ranges. Neither
    staffing estimates nor fractional allocations define compliant shifts.
    """
    a = assumptions
    if not 1 <= a.orders_per_service_hour <= 30 or not 0.3 <= a.utilisation <= 1:
        raise ValueError("Productivity must be 1–30; utilisation 30–100%")
    if (
        not 0 <= a.minimum_service_staff <= 10
        or int(a.minimum_service_staff) != a.minimum_service_staff
    ):
        raise ValueError("Minimum staffing must be an integer from 0 to 10")
    if (
        not 0 <= a.schedule_multiplier <= 3
        or not 0.1 <= a.demand_multiplier <= 3
        or not 1 <= a.loaded_hourly_wage <= 200
    ):
        raise ValueError("Invalid schedule, demand or wage assumption")
    if forecasts.empty:
        raise ValueError("Forecast rows are required")
    origins = forecasts.origin_date.unique()
    if len(origins) != 1:
        raise ValueError("Choose forecasts from a single origin")
    origin = pd.Timestamp(origins[0])
    if pd.to_datetime(forecasts.business_date).le(origin).any():
        raise ValueError("Forecast dates must follow origin")
    cutoff = origin - pd.Timedelta(days=83)
    daily = history_daily.loc[
        pd.to_datetime(history_daily.business_date).between(cutoff, origin)
    ].copy()
    hourly = history_hourly.loc[
        pd.to_datetime(history_hourly.business_date).between(cutoff, origin)
    ].copy()
    daily["weekday"] = pd.to_datetime(daily.business_date).dt.dayofweek
    hourly["weekday"] = pd.to_datetime(hourly.business_date).dt.dayofweek
    basket = daily.groupby(["restaurant_id", "weekday"])[
        ["revenue", "transactions"]
    ].sum()
    basket["reference_atv"] = basket.revenue / basket.transactions.replace(0, np.nan)
    keys = ["restaurant_id", "weekday", "hour"]
    profile = (
        hourly.groupby(keys)
        .agg(
            historical_orders=("transactions", "sum"),
            scheduled_service_hours=("scheduled_service_hours", "mean"),
            scheduled_paid_hours=("scheduled_paid_hours", "mean"),
            historical_total_hours=("paid_hours", "mean"),
            historical_service_hours=("service_hours", "mean"),
            observations=("business_date", "nunique"),
        )
        .reset_index()
    )
    totals = profile.groupby(["restaurant_id", "weekday"]).historical_orders.transform(
        "sum"
    )
    profile["hour_share"] = profile.historical_orders / totals.replace(0, np.nan)
    profile = profile.merge(
        basket[["reference_atv"]].reset_index(),
        on=["restaurant_id", "weekday"],
        validate="many_to_one",
    )
    profile["support_hours"] = (
        profile.historical_total_hours - profile.historical_service_hours
    ).clip(lower=0)
    future = forecasts.copy()
    future["weekday"] = pd.to_datetime(future.business_date).dt.dayofweek
    result = future.merge(
        profile, on=["restaurant_id", "weekday"], validate="many_to_many"
    )
    if (
        len(result) != len(forecasts) * 11
        or result[["reference_atv", "hour_share"]].isna().any().any()
    ):
        raise ValueError("Insufficient prior weekday demand/schedule history")
    for source, target in [
        ("forecast_revenue", "forecast_orders"),
        ("lower_80", "orders_lower"),
        ("upper_80", "orders_upper"),
    ]:
        result[target] = (
            result[source]
            / result.reference_atv
            * result.hour_share
            * a.demand_multiplier
        )
    capacity = a.orders_per_service_hour * a.utilisation
    for demand, staffing in [
        ("forecast_orders", "suggested_service_hours"),
        ("orders_lower", "service_hours_lower"),
        ("orders_upper", "service_hours_upper"),
    ]:
        result[staffing] = np.maximum(
            a.minimum_service_staff, np.ceil(result[demand] / capacity)
        )
    result["scheduled_service_hours"] *= a.schedule_multiplier
    result["scheduled_paid_hours"] *= a.schedule_multiplier
    result["suggested_paid_hours"] = (
        result.suggested_service_hours + result.support_hours
    )
    result["service_gap_hours"] = (
        result.suggested_service_hours - result.scheduled_service_hours
    )
    result["planning_status"] = np.select(
        [result.service_gap_hours > 0.5, result.service_gap_hours < -0.5],
        ["Potential under-coverage", "Potential spare capacity"],
        default="Within tolerance",
    )
    result["suggested_labour_cost"] = result.suggested_paid_hours * a.loaded_hourly_wage
    result["template_labour_cost"] = result.scheduled_paid_hours * a.loaded_hourly_wage
    result["budget_difference"] = (
        result.suggested_labour_cost - result.template_labour_cost
    )
    result["schedule_basis"] = (
        "Prior 84-day scheduled weekday template; support hours from actual history"
    )
    for name, value in asdict(a).items():
        result[name] = value
    return result.sort_values(["restaurant_id", "business_date", "hour"]).reset_index(
        drop=True
    )
