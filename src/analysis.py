"""Explain operational performance with explicit comparisons and limitations."""

import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from .common import REPORTS, TABLEAU, ratio, read, save
from .kpi_engine import ADDITIVE, calculate


def customer_analysis(orders):
    """RFM segments and fully observed return cohorts for identified customers."""
    identified = orders[orders.customer_id.notna()].copy()
    identified["business_date"] = pd.to_datetime(identified.business_date)
    asof = identified.business_date.max()
    customers = (
        identified.groupby("customer_id")
        .agg(
            first_visit=("business_date", "min"),
            last_visit=("business_date", "max"),
            visits=("business_date", "nunique"),
            orders=("order_id", "size"),
            spend=("revenue", "sum"),
            restaurant_id=("restaurant_id", "first"),
        )
        .reset_index()
    )
    customers["recency_days"] = (asof - customers.last_visit).dt.days
    customers["segment"] = np.select(
        [
            (customers.recency_days <= 30) & (customers.visits >= 12),
            customers.recency_days > 90,
            (customers.visits <= 2) & (customers.recency_days <= 30),
            customers.visits >= 6,
        ],
        ["Champions", "Lapsed", "New / occasional", "Regulars"],
        default="Developing",
    )
    enriched = identified.merge(
        customers[["customer_id", "first_visit"]], on="customer_id"
    )
    enriched["days_since_first"] = (
        enriched.business_date - enriched.first_visit
    ).dt.days
    repeat90 = (
        enriched[enriched.days_since_first.between(1, 90)].groupby("customer_id").size()
    )
    repeat_later = (
        enriched[enriched.days_since_first.between(31, 90)]
        .groupby("customer_id")
        .size()
    )
    early_visits = (
        enriched[enriched.days_since_first.between(0, 30)]
        .groupby("customer_id")
        .business_date.nunique()
    )
    loyalty = read("loyalty")
    redemption = loyalty[loyalty.event_type.eq("Redeem")].merge(
        customers[["customer_id", "first_visit"]], on="customer_id"
    )
    redemption["age"] = (
        pd.to_datetime(redemption.event_date) - redemption.first_visit
    ).dt.days
    early_redeemers = set(redemption.loc[redemption.age.between(0, 30), "customer_id"])
    customers["eligible_90d"] = customers.first_visit.le(asof - pd.Timedelta(days=90))
    customers["repeat_within_90d"] = (
        customers.customer_id.isin(repeat90.index)
        .astype(int)
        .where(customers.eligible_90d)
    )
    customers["return_days31_90"] = (
        customers.customer_id.isin(repeat_later.index)
        .astype(int)
        .where(customers.eligible_90d)
    )
    customers["early_redemption"] = customers.customer_id.isin(early_redeemers)
    customers["early_visits"] = customers.customer_id.map(early_visits).fillna(0)
    customers["early_activity_band"] = pd.cut(
        customers.early_visits,
        bins=[0, 1, 3, float("inf")],
        labels=["1 visit", "2–3 visits", "4+ visits"],
    ).astype(str)
    customers["cohort_month"] = customers.first_visit.dt.strftime("%Y-%m")
    cohorts = (
        customers.groupby(["restaurant_id", "cohort_month"])
        .agg(
            identified_customers=("customer_id", "size"),
            eligible_customers=("eligible_90d", "sum"),
            repeat_customers=("repeat_within_90d", "sum"),
        )
        .reset_index()
    )
    cohorts["repeat_customer_rate"] = ratio(
        cohorts.repeat_customers, cohorts.eligible_customers
    )
    behaviours = (
        customers[customers.eligible_90d]
        .groupby(["early_activity_band", "early_redemption"])
        .agg(
            customers=("customer_id", "size"),
            later_returners=("return_days31_90", "sum"),
        )
        .reset_index()
    )
    behaviours["later_return_rate"] = ratio(
        behaviours.later_returners, behaviours.customers
    )
    save(customers, TABLEAU / "customer_segments.csv")
    save(cohorts, TABLEAU / "customer_cohorts.csv")
    save(behaviours, TABLEAU / "loyalty_behaviours.csv")
    return customers, behaviours


def promotion_analysis(daily, stores):
    """Matched-location before/during comparisons, with bootstrap uncertainty.

    Counterfactual sales use the treated store's prior same-weekday fortnight
    adjusted for the contemporaneous change at unpromoted location peers.
    This is an observational estimate; parallel trends are not guaranteed.
    """
    rng = np.random.default_rng(42)
    daily = daily.copy()
    daily["business_date"] = pd.to_datetime(daily.business_date)
    # Net contribution after all observed costs; daily fixed-cost allocation labelled.
    rows = []
    campaigns = read("promotions")
    for promo in campaigns.itertuples():
        start, end = pd.Timestamp(promo.start_date), pd.Timestamp(promo.end_date)
        before = daily.business_date.between(
            start - pd.Timedelta(days=14), start - pd.Timedelta(days=1)
        )
        during = daily.business_date.between(start, end)
        treated = daily.restaurant_id.eq(promo.restaurant_id)
        location = stores.set_index("restaurant_id").loc[
            promo.restaurant_id, "location_type"
        ]
        peer_ids = set(
            stores.loc[
                stores.location_type.eq(location)
                & stores.restaurant_id.ne(promo.restaurant_id),
                "restaurant_id",
            ]
        )
        # Eligibility uses campaign dates, including campaigns with no POS
        # attribution; absence of an attributed sale does not mean untreated.
        overlapping = pd.to_datetime(campaigns.start_date).le(end) & pd.to_datetime(
            campaigns.end_date
        ).ge(start - pd.Timedelta(days=14))
        contaminated = set(campaigns.loc[overlapping, "restaurant_id"])
        peer_ids -= contaminated
        if not peer_ids:
            rows.append(
                {
                    "promotion_id": promo.promotion_id,
                    "restaurant_id": promo.restaurant_id,
                    "campaign_name": promo.campaign_name,
                    "start_date": promo.start_date,
                    "end_date": promo.end_date,
                    "discount_rate": promo.discount_rate,
                    "campaign_cost": promo.campaign_cost,
                    "control_stores": 0,
                    "control_restaurant_ids": "[]",
                    "comparison_start": (start - pd.Timedelta(days=14)).strftime(
                        "%Y-%m-%d"
                    ),
                    "estimate_status": "No eligible control stores",
                }
            )
            continue
        treated_before = daily.loc[treated & before].sort_values("business_date")
        treated_during = daily.loc[treated & during].sort_values("business_date")
        control_before = (
            daily.loc[daily.restaurant_id.isin(peer_ids) & before]
            .groupby("business_date")
            .revenue.mean()
            .to_numpy()
        )
        control_during = (
            daily.loc[daily.restaurant_id.isin(peer_ids) & during]
            .groupby("business_date")
            .revenue.mean()
            .to_numpy()
        )
        change = control_during / control_before
        baseline_revenue = treated_before.revenue.to_numpy() * change
        incremental_sales = treated_during.revenue.to_numpy() - baseline_revenue
        control_before_orders = (
            daily.loc[daily.restaurant_id.isin(peer_ids) & before]
            .groupby("business_date")
            .transactions.mean()
            .to_numpy()
        )
        control_during_orders = (
            daily.loc[daily.restaurant_id.isin(peer_ids) & during]
            .groupby("business_date")
            .transactions.mean()
            .to_numpy()
        )
        baseline_orders = (
            treated_before.transactions.to_numpy()
            * control_during_orders
            / control_before_orders
        )
        # For contribution, estimate non-campaign costs by before-period cost ratios.
        variable_ratio = (
            treated_before.ingredient_cost
            + treated_before.waste_cost
            + treated_before.commission_cost
        ).sum() / treated_before.revenue.sum()
        expected_variable_cost = baseline_revenue * variable_ratio
        observed_variable_cost = (
            treated_during.ingredient_cost
            + treated_during.waste_cost
            + treated_during.commission_cost
        ).to_numpy()
        incremental_labour = (
            treated_during.labour_cost.to_numpy()
            - treated_before.labour_cost.to_numpy()
        )
        incremental_before_campaign = (
            incremental_sales
            - (observed_variable_cost - expected_variable_cost)
            - incremental_labour
        )
        net_gain = incremental_before_campaign.sum() - promo.campaign_cost
        samples = (
            rng.choice(incremental_before_campaign, size=(1000, 14), replace=True).sum(
                axis=1
            )
            - promo.campaign_cost
        )
        rows.append(
            {
                "promotion_id": promo.promotion_id,
                "restaurant_id": promo.restaurant_id,
                "campaign_name": promo.campaign_name,
                "discount_rate": promo.discount_rate,
                "start_date": promo.start_date,
                "end_date": promo.end_date,
                "control_stores": len(peer_ids),
                "control_restaurant_ids": json.dumps(
                    sorted(int(sid) for sid in peer_ids)
                ),
                "comparison_start": (start - pd.Timedelta(days=14)).strftime(
                    "%Y-%m-%d"
                ),
                "baseline_revenue": baseline_revenue.sum(),
                "observed_revenue": treated_during.revenue.sum(),
                "incremental_revenue": incremental_sales.sum(),
                "baseline_orders": baseline_orders.sum(),
                "observed_orders": treated_during.transactions.sum(),
                "incremental_orders": treated_during.transactions.sum()
                - baseline_orders.sum(),
                "campaign_cost": promo.campaign_cost,
                "incremental_contribution": net_gain,
                "baseline_variable_cost": expected_variable_cost.sum(),
                "observed_variable_cost": observed_variable_cost.sum(),
                "incremental_variable_cost": (
                    observed_variable_cost - expected_variable_cost
                ).sum(),
                "incremental_labour_cost": incremental_labour.sum(),
                "contribution_before_campaign": incremental_before_campaign.sum(),
                "promotion_roi": net_gain / promo.campaign_cost,
                "contribution_low95": np.quantile(samples, 0.025),
                "contribution_high95": np.quantile(samples, 0.975),
                "estimate_status": "Exploratory matched estimate",
            }
        )
    estimates = pd.DataFrame(rows)
    save(estimates, TABLEAU / "promotion_effectiveness.csv")
    return estimates


def staffing_association(daily):
    """Residualised staffing/satisfaction association with store-cluster bootstrap."""
    sample = daily[daily.survey_responses.ge(3)].copy().reset_index(drop=True)
    sample["service_pressure"] = sample.transactions / (sample.service_hours * 6)
    controls = pd.get_dummies(
        sample[["restaurant_id", "weekday", "month"]].astype(str), dtype=float
    )
    controls["log_orders"] = np.log1p(sample.transactions)
    # Remove demand, store, weekday and calendar-month effects from both series.
    x = sample.service_pressure.to_numpy()
    y = sample.satisfaction_score.to_numpy()
    x_res = x - Ridge(alpha=1).fit(controls, x).predict(controls)
    y_res = y - Ridge(alpha=1).fit(controls, y).predict(controls)
    correlation = float(np.corrcoef(x_res, y_res)[0, 1])
    sample["x_res"], sample["y_res"] = x_res, y_res
    rng = np.random.default_rng(42)
    groups = [
        g[["x_res", "y_res"]].to_numpy() for _, g in sample.groupby("restaurant_id")
    ]
    estimates = []
    for _ in range(400):
        values = np.concatenate(
            [groups[i] for i in rng.integers(0, len(groups), len(groups))]
        )
        estimates.append(np.corrcoef(values[:, 0], values[:, 1])[0, 1])
    return {
        "controlled_correlation": correlation,
        "ci_low": float(np.quantile(estimates, 0.025)),
        "ci_high": float(np.quantile(estimates, 0.975)),
        "store_days": len(sample),
        "method": "Ridge residualisation; approximate store-cluster bootstrap with fixed residuals",
        "interpretation": "Association, not a causal effect; survey responses are selective",
    }


def run():
    """Export traceable segments, exceptions, correlations and comparisons."""
    stores, daily, monthly = (
        read("restaurants"),
        read("store_day"),
        read("store_month_kpis"),
    )
    orders = read("orders")
    customers, behaviours = customer_analysis(orders)
    promotions = promotion_analysis(daily, stores)
    performance = calculate(
        daily.groupby("restaurant_id")[ADDITIVE].sum().reset_index()
    ).merge(stores, on="restaurant_id")
    segment_features = [
        "operating_margin_pct",
        "labour_cost_pct",
        "waste_pct",
        "satisfaction_score",
        "sales_per_labour_hour",
    ]
    scaler = StandardScaler()
    labels = KMeans(n_clusters=3, n_init=20, random_state=42).fit_predict(
        scaler.fit_transform(performance[segment_features])
    )
    performance["cluster_id"] = labels
    ranking = (
        performance.groupby("cluster_id")
        .operating_margin_pct.mean()
        .sort_values()
        .index
    )
    names = dict(zip(ranking, ["Needs support", "Stable", "Efficient"]))
    performance["store_segment"] = performance.cluster_id.map(names)
    save(performance, TABLEAU / "store_segments.csv")
    corr_fields = [
        "operating_margin_pct",
        "labour_cost_pct",
        "waste_pct",
        "satisfaction_score",
        "sales_per_labour_hour",
        "average_transaction_value",
        "late_delivery_pct",
    ]
    correlation = monthly[corr_fields].corr().rename_axis("metric").reset_index()
    save(correlation, REPORTS / "exports/kpi_correlations.csv")
    # This diagnostic is intentionally separate from financial identity correlations.
    staffing = staffing_association(daily)
    # Robust within-store/day-of-week sales anomalies with a rolling, prior-only baseline.
    anomalies = daily.sort_values(["restaurant_id", "weekday", "business_date"]).copy()
    group = anomalies.groupby(["restaurant_id", "weekday"]).revenue
    anomalies["prior_median"] = group.transform(
        lambda s: s.shift(1).rolling(12, min_periods=8).median()
    )
    anomalies["prior_mad"] = group.transform(
        lambda s: s.shift(1)
        .rolling(12, min_periods=8)
        .apply(lambda values: np.median(np.abs(values - np.median(values))), raw=True)
    )
    anomalies["robust_z"] = (
        0.6745
        * (anomalies.revenue - anomalies.prior_median)
        / anomalies.prior_mad.replace(0, np.nan)
    )
    anomalies["is_anomaly"] = anomalies.robust_z.abs().gt(3.5)
    save(
        anomalies.loc[
            anomalies.is_anomaly,
            [
                "restaurant_id",
                "restaurant_name",
                "business_date",
                "revenue",
                "prior_median",
                "robust_z",
                "is_public_holiday",
                "promotion_id",
            ],
        ],
        TABLEAU / "sales_anomalies.csv",
    )
    latest = monthly[monthly.month.ge("2025-10")]
    latest_perf = calculate(
        latest.groupby("restaurant_id")[ADDITIVE].sum().reset_index()
    ).merge(stores, on="restaurant_id")
    latest_perf = latest_perf.merge(
        latest.groupby("restaurant_id").performance_index.mean().reset_index(),
        on="restaurant_id",
    )
    latest_perf["waste_peer_median"] = latest_perf.groupby(
        "location_type"
    ).waste_pct.transform("median")
    latest_perf["estimated_waste_opportunity"] = (
        latest_perf.waste_pct - latest_perf.waste_peer_median
    ).clip(lower=0) * (latest_perf.ingredient_cost + latest_perf.waste_cost)
    save(latest_perf, TABLEAU / "latest_store_opportunities.csv")
    hourly = read("store_hour")
    staffing_week = (
        hourly.groupby(["restaurant_id", "weekday", "hour"])
        .agg(
            transactions=("transactions", "mean"),
            capacity=("service_capacity_orders", "mean"),
            pressure_hours=("staffing_status", lambda x: x.eq("Pressure").sum()),
            observations=("staffing_status", "size"),
            spare_hours=("staffing_status", lambda x: x.eq("Spare capacity").sum()),
        )
        .reset_index()
    )
    staffing_week["pressure_share"] = (
        staffing_week.pressure_hours / staffing_week.observations
    )
    save(staffing_week, TABLEAU / "staffing_patterns.csv")
    summary = {
        "staffing_association": staffing,
        "eligible_customers": int(customers.eligible_90d.sum()),
        "repeat_customer_rate": float(customers.repeat_within_90d.mean()),
        "anomaly_count": int(anomalies.is_anomaly.sum()),
        "customers": len(customers),
        "promotion_estimates": int(promotions.incremental_contribution.notna().sum()),
        "pressure_hour_share": float(hourly.staffing_status.eq("Pressure").mean()),
    }
    (REPORTS / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
    print(
        "Completed customer/store segmentation, promotion estimates and diagnostic analysis.",
        flush=True,
    )
    return summary


if __name__ == "__main__":
    run()
