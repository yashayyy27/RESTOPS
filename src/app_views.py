"""Eight management workflows; calculation logic lives in independent modules."""

import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .app_data import export_csv
from .common import REPORTS, ROOT
from .forecasting import metrics
from .management import (
    COSTS,
    aggregate,
    profit_bridge,
    revenue_bridge,
    weekly_brief,
    weekly_scorecard,
)
from .planning import PlanningAssumptions, hourly_plan
from .scenarios import Scenario, compare, sensitivity, simulate

VIEWS = [
    "Executive overview",
    "Restaurant investigation",
    "Labour & demand planning",
    "Customer & loyalty",
    "Promotion evaluation",
    "Forecasting",
    "Profit scenario simulator",
    "Data quality",
]
COLOURS = ["#ff3b30", "#58d6df", "#ffc16a", "#b0b0bb"]


def money(value):
    if not np.isfinite(value):
        return "Unavailable"
    return f"A${0 if abs(value) < 0.5 else value:,.0f}"


def chart(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#101014",
        plot_bgcolor="#101014",
        font=dict(color="#f4f4f6", family="Arial"),
        margin=dict(l=12, r=12, t=45, b=20),
        legend=dict(orientation="h", y=-0.20),
        height=370,
    )
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def table(frame, name, caption=None):
    if caption:
        st.caption(caption)
    pretty = frame.copy()
    for field in pretty.select_dtypes(include="number"):
        if field.endswith("_pct") or field in [
            "promotion_roi",
            "repeat_customer_rate",
            "revenue_growth",
            "interval_coverage",
            "waste_rate",
            "discount_rate",
        ]:
            pretty[field] *= 100
    pretty = pretty.rename(
        columns={
            c: c.replace("_pct", " (%)").replace("_", " ").capitalize() for c in pretty
        }
    )
    st.dataframe(pretty.round(3), hide_index=True, width="stretch")
    st.download_button(
        f"Download {name} CSV",
        export_csv(frame),
        f"restops_{name}.csv",
        "text/csv",
        key=f"download_{name}",
    )


def focus(daily, ids):
    stores = (
        daily[daily.restaurant_id.isin(ids)][["restaurant_id", "restaurant_name"]]
        .drop_duplicates()
        .sort_values("restaurant_name")
    )
    names = stores.restaurant_name.tolist()
    default = names.index("Wollongong") if "Wollongong" in names else 0
    name = st.selectbox(
        "Investigate restaurant", names, index=default, key="focus_store"
    )
    return int(stores.loc[stores.restaurant_name.eq(name), "restaurant_id"].iloc[0])


def selected(daily, ids, month=None):
    mask = daily.restaurant_id.isin(ids)
    if month:
        mask &= daily.month.eq(month)
    return daily.loc[mask]


def kpi_row(totals):
    cols = st.columns(4)
    for col, (label, value, definition) in zip(
        cols,
        [
            (
                "Net revenue",
                money(totals.revenue),
                "List sales less discounts; GST excluded",
            ),
            (
                "Operating profit",
                money(totals.operating_profit),
                "Revenue less ingredients, waste, labour, commissions, overheads and campaigns",
            ),
            (
                "Operating margin",
                f"{totals.operating_margin_pct:.1%}",
                "Profit / revenue, calculated from period totals",
            ),
            (
                "Orders",
                f"{totals.transactions:,.0f}",
                "Complete baskets; product lines are not separate transactions",
            ),
        ],
    ):
        col.metric(label, value, help=definition)


def executive(f, meta, ids, month):
    st.write("Which restaurants need attention, and what should we review this week?")
    daily = selected(f["store_day"], ids)
    current = daily[daily.month.eq(month)]
    if current.empty:
        st.info("No trading observations in this month.")
        return
    kpi_row(aggregate(current))
    weekly = weekly_scorecard(daily, f["store_month_kpis"], current.business_date.max())
    index = f["store_month_kpis"].loc[
        f["store_month_kpis"].month.eq(month), ["restaurant_id", "performance_index"]
    ]
    weekly = weekly.merge(index, on="restaurant_id", validate="one_to_one")
    st.subheader("Weekly attention queue")
    st.caption(
        f"{weekly.window_start.iloc[0]}–{weekly.window_end.iloc[0]} vs previous seven days. Monthly targets are allocated evenly across calendar days; holidays can affect the comparison."
    )
    table(
        weekly[
            [
                "restaurant_id",
                "restaurant_name",
                "revenue",
                "revenue_growth",
                "operating_profit",
                "operating_margin_pct",
                "target_achievement_pct",
                "labour_cost_pct",
                "waste_pct",
                "satisfaction_score",
                "performance_index",
            ]
        ],
        "weekly_performance",
    )
    left, right = st.columns([1.15, 1])
    with left:
        chart(
            px.bar(
                weekly,
                x="restaurant_name",
                y="operating_margin_pct",
                title="Weekly operating margin · lowest first",
                color_discrete_sequence=COLOURS,
            )
        )
    with right:
        trend = (
            daily.groupby("business_date")[["revenue", "operating_profit"]]
            .sum()
            .reset_index()
        )
        chart(
            px.line(
                trend,
                x="business_date",
                y=["revenue", "operating_profit"],
                title="Selected restaurants · revenue and profit",
                color_discrete_sequence=COLOURS,
            )
        )
    st.subheader("Weekly management brief")
    brief = weekly_brief(weekly)
    for position, item in enumerate(brief.head(3).itertuples()):
        with st.expander(
            f"{item.restaurant_name} · {item.priority} · component opportunity {money(item.estimated_weekly_opportunity)}",
            expanded=position == 0,
        ):
            st.markdown(
                f"**What changed:** {item.what_changed}\n\n**Evidence:** {item.evidence}\n\n**Plausible explanation:** {item.plausible_explanation}\n\n**Estimated impact:** {money(item.estimated_weekly_opportunity)} for this week, conditional on {item.impact_assumption.lower()}.\n\n**Recommended action:** {item.recommended_action}\n\n**Proposed owner:** {item.proposed_owner}\n\n**Success measure:** {item.success_measure}"
            )
    table(
        brief,
        "management_brief",
        "Opportunities are investigation inputs, not committed savings. Do not add them across interventions without modelling overlap.",
    )


def investigation(f, meta, ids, month):
    sid = focus(f["store_day"], ids)
    daily = selected(f["store_day"], [sid])
    current = daily[daily.month.eq(month)]
    if current.empty:
        st.info("No trading observations for this period.")
        return
    after = aggregate(current)
    kpi_row(after)
    target = (
        f["store_month_kpis"]
        .loc[
            f["store_month_kpis"].restaurant_id.eq(sid)
            & f["store_month_kpis"].month.eq(month),
            "revenue_target",
        ]
        .iloc[0]
    )
    st.metric(
        "Monthly revenue target gap",
        money(after.revenue - target),
        help="Actual revenue minus the monthly target. The simulation has no budget for order volume or basket value.",
    )
    prior_month = str(pd.Period(month) - 1)
    prior = daily[daily.month.eq(prior_month)]
    st.subheader("Explain the financial movement")
    st.caption(
        f"Full calendar month {month} vs {prior_month}. Different month lengths are retained. The target gap is separate: no budgeted transactions or mix exists to support a driver-level target bridge."
    )
    if prior.empty:
        st.info(
            "Prior-month observations are unavailable in this dataset; the month-over-month bridge cannot be calculated."
        )
    else:
        before = aggregate(prior)
        bridge = profit_bridge(before, after)
        chart(
            go.Figure(
                go.Waterfall(
                    x=["Prior profit"] + bridge.driver.tolist() + ["Current profit"],
                    y=[before.operating_profit]
                    + bridge.amount.tolist()
                    + [after.operating_profit],
                    measure=["absolute"] + ["relative"] * len(bridge) + ["total"],
                    increasing=dict(marker=dict(color=COLOURS[1])),
                    decreasing=dict(marker=dict(color=COLOURS[0])),
                    totals=dict(marker=dict(color=COLOURS[3])),
                )
            ).update_layout(title="Observed profit bridge · AUD")
        )
        st.caption(
            f"Reconciliation residual: {money(after.operating_profit-before.operating_profit-bridge.amount.sum())}. Order volume and net basket value explain the revenue movement exactly; each cost is counted once."
        )
        table(bridge, "profit_bridge")
        chart(
            px.bar(
                revenue_bridge(before, after),
                x="driver",
                y="amount",
                title="Revenue movement · exact volume / basket decomposition",
                color_discrete_sequence=COLOURS,
            )
        )
    products = f["product_month"]
    products = products[
        products.restaurant_id.eq(sid) & products.month.isin([prior_month, month])
    ]
    mix = (
        products.groupby(["month", "category"])[
            [
                "revenue",
                "ingredient_cost",
                "gross_contribution",
                "units",
                "list_revenue",
                "discount_amount",
            ]
        ]
        .sum()
        .reset_index()
    )
    st.subheader("Product mix and discount investigation")
    chart(
        px.bar(
            mix,
            x="category",
            y="gross_contribution",
            color="month",
            barmode="group",
            color_discrete_sequence=COLOURS,
            title="Product contribution by category · before labour and delivery",
        )
    )
    table(
        mix,
        "product_mix",
        "Mix, discounts and basket value can move together. This view supports investigation; these associations are not additional additive bridge components.",
    )
    waste = f["waste_detail"]
    waste = waste[
        waste.restaurant_id.eq(sid) & waste.business_date.str.startswith(month)
    ]
    reasons = waste.groupby("reason")[["waste_cost", "waste_units"]].sum().reset_index()
    chart(
        px.bar(
            reasons,
            x="reason",
            y="waste_cost",
            title="Waste cost by logged reason",
            color_discrete_sequence=COLOURS,
        )
    )
    table(reasons, "waste_reasons")


def labour(f, meta, ids, month):
    st.write("What hourly coverage does forecast demand imply, and what would it cost?")
    sid = focus(f["store_day"], ids)
    with st.expander("Productivity, service and budget assumptions", expanded=True):
        c1, c2, c3 = st.columns(3)
        productivity = c1.number_input(
            "Orders per service hour",
            min_value=1.0,
            max_value=30.0,
            value=6.0,
            step=0.5,
            key="productivity",
        )
        utilisation = (
            c2.slider("Target utilisation (%)", 30, 100, 80, key="utilisation") / 100
        )
        minimum = c3.number_input(
            "Minimum service staff per hour",
            min_value=0,
            max_value=10,
            value=1,
            key="minimum",
        )
        c1, c2, c3 = st.columns(3)
        schedule = (
            c1.slider("Scheduled template hours (%)", 0, 200, 100, key="schedule") / 100
        )
        demand = (
            c2.slider("Demand sensitivity (%)", 50, 150, 100, key="planning_demand")
            / 100
        )
        wage = c3.number_input(
            "Loaded hourly wage (AUD)",
            min_value=1.0,
            max_value=200.0,
            value=35.0,
            step=1.0,
            key="planning_wage",
        )
    plan = hourly_plan(
        f["store_day"],
        f["store_hour"],
        f["forecast_daily"][f["forecast_daily"].restaurant_id.eq(sid)],
        PlanningAssumptions(productivity, utilisation, minimum, schedule, demand, wage),
    )
    st.caption(
        f"Forecast {meta['forecast_start']}–{meta['forecast_end']}; history through {meta['forecast_origin']}. Hourly allocation uses prior 84-day weekday order mix and basket value. Scheduled hours repeat the observed weekday template; support hours retain the actual historical pattern."
    )
    cols = st.columns(4)
    cols[0].metric("Expected orders", f"{plan.forecast_orders.sum():,.0f}")
    cols[1].metric("Suggested paid hours", f"{plan.suggested_paid_hours.sum():,.0f}")
    cols[2].metric("Template paid hours", f"{plan.scheduled_paid_hours.sum():,.0f}")
    cols[3].metric(
        "Budget difference",
        money(plan.budget_difference.sum()),
        help="Suggested less template hours × the same loaded wage. Different from actual payroll savings.",
    )
    date = st.selectbox(
        "Planning date", sorted(plan.business_date.unique()), key="planning_date"
    )
    one = plan[plan.business_date.eq(date)]
    chart(
        px.line(
            one,
            x="hour",
            y=[
                "suggested_service_hours",
                "scheduled_service_hours",
                "service_hours_upper",
            ],
            markers=True,
            title="Service coverage · suggested, template and high-demand range",
            color_discrete_sequence=COLOURS,
        )
    )
    view = plan[
        [
            "restaurant_id",
            "business_date",
            "hour",
            "forecast_orders",
            "orders_lower",
            "orders_upper",
            "scheduled_service_hours",
            "suggested_service_hours",
            "service_gap_hours",
            "planning_status",
            "suggested_labour_cost",
            "budget_difference",
        ]
    ]
    table(view[view.business_date.eq(date)], "selected_day_labour")
    st.download_button(
        "Download all 28 days of labour planning CSV",
        export_csv(plan),
        "restops_labour_plan.csv",
        "text/csv",
        key="all_plan",
    )
    st.info(
        "Hourly coverage estimates are decision support. They do not form a legally compliant roster: shift lengths, breaks, award rules, skills, employee availability and contract constraints are not optimised. Confirm service assumptions with managers."
    )


def customers(f, meta, ids, month):
    st.write("Which customer and service experiments merit a controlled trial?")
    segments = f["customer_segment_summary"]
    segments = segments[segments.restaurant_id.isin(ids)]
    cohorts = f["customer_cohorts"][f["customer_cohorts"].restaurant_id.isin(ids)]
    eligible, repeats = cohorts.eligible_customers.sum(), cohorts.repeat_customers.sum()
    totals = aggregate(selected(f["store_day"], ids, month))
    cols = st.columns(4)
    cols[0].metric("Identified customers", f"{segments.customers.sum():,.0f}")
    cols[1].metric(
        "Eligible 90-day repeat",
        f"{repeats/eligible:.1%}" if eligible else "Unavailable",
        help="Customers with another visit in days 1–90 / customers with complete 90-day follow-up",
    )
    cols[2].metric(
        "Satisfaction",
        f"{totals.satisfaction_score:.2f}/5",
        help="Selected historical month; summed scores / answered surveys",
    )
    cols[3].metric("Answered surveys", f"{totals.survey_responses:,.0f}")
    st.caption(
        f"Customer segments and cohorts are fixed snapshots as of {meta['customer_asof']}; the reporting-month filter applies only to satisfaction. Anonymous visits are excluded. Customer IDs are store-local and first-observed visits are not proven acquisition dates."
    )
    by_segment = (
        segments.groupby("segment")[["customers", "spend", "visits"]]
        .sum()
        .reset_index()
    )
    chart(
        px.bar(
            by_segment,
            x="segment",
            y="customers",
            title="Identified customer segments",
            color_discrete_sequence=COLOURS,
        )
    )
    table(by_segment, "customer_segments")
    cohort = (
        cohorts.groupby("cohort_month")[["eligible_customers", "repeat_customers"]]
        .sum()
        .reset_index()
    )
    cohort["repeat_customer_rate"] = (
        cohort.repeat_customers / cohort.eligible_customers.replace(0, np.nan)
    )
    chart(
        px.line(
            cohort,
            x="cohort_month",
            y="repeat_customer_rate",
            markers=True,
            title="90-day repeat rate by first-observed cohort",
            color_discrete_sequence=COLOURS,
        )
    )
    table(cohort, "customer_cohorts")
    st.subheader("Company-wide early behaviour comparison")
    table(
        f["loyalty_behaviours"],
        "loyalty_behaviour",
        "This company-wide view does not respond to restaurant or month filters. Early behaviour is measured in days 0–30, return in days 31–90; redemption associations are not causal loyalty effects.",
    )


def promotions(f, meta, ids, month):
    st.write("Did a campaign add contribution after discounts and campaign spending?")
    data = f["promotion_effectiveness"][
        f["promotion_effectiveness"].restaurant_id.isin(ids)
    ]
    st.caption(
        "Campaign results retain their own full before/during periods. Reporting-month selection does not truncate a campaign. Controls exclude promoted location peers in either window; fixed overheads are assumed unchanged."
    )
    labels = data.promotion_id + " · " + data.campaign_name + " · " + data.start_date
    chosen = st.selectbox("Campaign", labels.tolist(), key="campaign")
    row = data.loc[labels.eq(chosen)].iloc[0]
    if row.estimate_status == "No eligible control stores":
        st.warning(
            "No eligible comparison stores. Incremental sales, contribution and ROI are unavailable for this campaign."
        )
    else:
        cols = st.columns(4)
        cols[0].metric("Incremental net sales", money(row.incremental_revenue))
        cols[1].metric("Incremental contribution", money(row.incremental_contribution))
        cols[2].metric(
            "Promotion ROI",
            f"{row.promotion_roi:.1%}",
            help="Incremental contribution after campaign spend / campaign spend; net ROI",
        )
        cols[3].metric("Control restaurants", f"{row.control_stores:.0f}")
        st.caption(
            f"Approximate contribution range: {money(row.contribution_low95)} to {money(row.contribution_high95)}. Resampled daily differences do not fully capture counterfactual uncertainty or serial dependence."
        )
        view = pd.DataFrame(
            {
                "measure": [
                    "Estimated no-campaign sales",
                    "Observed net sales",
                    "Estimated incremental sales",
                    "Campaign spend",
                    "Net incremental contribution",
                ],
                "amount": [
                    row.baseline_revenue,
                    row.observed_revenue,
                    row.incremental_revenue,
                    row.campaign_cost,
                    row.incremental_contribution,
                ],
            }
        )
        chart(
            px.bar(
                view,
                x="measure",
                y="amount",
                title="Campaign economics · AUD",
                color_discrete_sequence=COLOURS,
            )
        )
        st.info(
            "Discounts are already deducted from net sales. Contribution includes estimated changes in ingredient, waste, commission and labour costs, then deducts campaign spend once. Observational comparison supports a controlled trial; it does not prove causal ROI."
        )
    table(data, "promotion_evaluation")
    with st.expander("Method validation against isolated synthetic truth"):
        validation = f["promotion_method_validation"]
        validation = validation[validation.restaurant_id.isin(ids)]
        st.caption(
            "Generator-only expected order uplift is read after estimation, never supplied to the estimator or forecasting features. It represents expected mean demand, not realised counterfactual orders or true profit. Error combines estimator bias, sampling variation and cleaning exclusions."
        )
        if validation.empty:
            st.info(
                "No generator truth is available. Regenerate the full pipeline to produce method validation."
            )
        else:
            table(validation, "promotion_method_validation")


def forecasting(f, meta, ids, month):
    st.write(
        "What sales should managers expect over the next four weeks, and how much error should they allow?"
    )
    sid = focus(f["store_day"], ids)
    evaluation = f["forecast_store_metrics"][
        f["forecast_store_metrics"].restaurant_id.eq(sid)
    ]
    holdout = evaluation[evaluation.evaluation_period.eq("Holdout")]
    winner = meta["forecast"]["selected_model"]
    score = holdout[holdout.model.eq(winner)].iloc[0]
    cols = st.columns(4)
    cols[0].metric(
        "Holdout MAE", money(score.mae), help="Mean absolute daily revenue error"
    )
    cols[1].metric(
        "Holdout RMSE",
        money(score.rmse),
        help="Root mean squared daily error; more sensitive to large misses",
    )
    cols[2].metric(
        "Holdout WAPE",
        f"{score.wape:.1f}%",
        help="Sum absolute error / sum actual revenue",
    )
    cols[3].metric(
        "Measured band coverage",
        f"{score.interval_coverage:.1%}",
        help="Fraction of selected-store holdout actuals inside approximate nominal 80% bands",
    )
    st.caption(
        f"Selected model: {winner}. Selection uses three rolling validation windows; the final {meta['forecast']['holdout_start']}–{meta['forecast']['holdout_end']} holdout is reporting-only. Metrics here describe this restaurant, not the whole chain."
    )
    future = f["forecast_daily"][f["forecast_daily"].restaurant_id.eq(sid)]
    history = f["store_day"][f["store_day"].restaurant_id.eq(sid)].tail(56)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history.business_date,
            y=history.revenue,
            name="Observed",
            line=dict(color=COLOURS[3]),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=future.business_date,
            y=future.upper_80,
            name="Upper range",
            line=dict(width=0),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=future.business_date,
            y=future.lower_80,
            name="Approximate 80% band",
            fill="tonexty",
            fillcolor="rgba(255,59,48,.16)",
            line=dict(width=0),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=future.business_date,
            y=future.forecast_revenue,
            name=winner,
            line=dict(color=COLOURS[0]),
        )
    )
    chart(fig.update_layout(title="Four-week revenue forecast · selected restaurant"))
    table(
        evaluation,
        "forecast_accuracy",
        "Validation rows combine three folds at the restaurant/model grain. Dollar errors and WAPE are computed from all corresponding daily errors; bands use 84 pre-holdout errors per restaurant.",
    )
    st.subheader("Compare against the weekly baseline")
    traces = f["forecast_backtests"]
    traces = traces[
        traces.restaurant_id.eq(sid) & traces.evaluation_period.eq("Holdout")
    ]
    baseline = holdout.loc[holdout.model.eq("Seasonal naive"), "mae"].iloc[0]
    st.write(
        f"Selected-model holdout MAE difference vs seasonal naive: {(baseline-score.mae)/baseline:.1%}. This can vary by restaurant; a chain-level winner need not win at every store."
    )
    chart(
        px.line(
            traces,
            x="business_date",
            y="forecast_revenue",
            color="model",
            color_discrete_sequence=COLOURS,
            title="Holdout predictions · models fixed before evaluation",
        )
    )
    table(future, "four_week_forecast")
    st.info(
        "Forecasts are a January 2026 continuation of synthetic history. Future promotion plans, weather, events and operational changes are not known. Empirical bands are approximate, not guaranteed probabilities; store intervals must not be added to claim a chain interval."
    )


def scenario(f, meta, ids, month):
    st.write(
        "What could a proposed operating change do to profit under explicit assumptions?"
    )
    sid = focus(f["store_day"], ids)
    baseline = aggregate(selected(f["store_day"], [sid], month))
    base = simulate(baseline)
    context = (sid, month, meta["mode"])
    if st.session_state.get("scenario_context") != context:
        for key in (
            "hours_change",
            "wage_change",
            "price_change",
            "demand_change",
            "discount_rate",
            "waste_rate",
        ):
            st.session_state.pop(key, None)
        st.session_state["scenario_context"] = context
    st.caption(
        f"Baseline is the observed calendar month {month}. This is a what-if estimate for the same duration, separate from statistical forecasts. No automatic price elasticity or staffing effect on demand is assumed."
    )
    c1, c2, c3 = st.columns(3)
    hours = c1.slider("Staffing hours change (%)", -40, 40, 0, key="hours_change") / 100
    wage = c2.slider("Loaded wage change (%)", -20, 40, 0, key="wage_change") / 100
    price = c3.slider("Menu price change (%)", -20, 30, 0, key="price_change") / 100
    c1, c2, c3 = st.columns(3)
    demand = c1.slider("Order demand change (%)", -50, 50, 0, key="demand_change") / 100
    discount = (
        c2.number_input(
            "Discount on list sales (%)",
            min_value=0.0,
            max_value=60.0,
            value=float(base["discount_rate"] * 100),
            step=0.5,
            format="%.2f",
            key="discount_rate",
        )
        / 100
    )
    waste = (
        c3.number_input(
            "Waste share of total food cost (%)",
            min_value=0.0,
            max_value=30.0,
            value=float(base["waste_rate"] * 100),
            step=0.5,
            format="%.2f",
            key="waste_rate",
        )
        / 100
    )
    assumptions = Scenario(hours, wage, price, demand, discount, waste)
    after = simulate(baseline, assumptions)
    cols = st.columns(4)
    cols[0].metric(
        "Scenario revenue",
        money(after["revenue"]),
        money(after["revenue"] - base["revenue"]),
    )
    cols[1].metric(
        "Scenario operating profit",
        money(after["operating_profit"]),
        money(after["operating_profit"] - base["operating_profit"]),
    )
    cols[2].metric(
        "Scenario margin",
        f"{after['operating_margin_pct']:.1%}",
        f"{(after['operating_margin_pct']-base['operating_margin_pct'])*100:+.1f} pp",
    )
    cols[3].metric(
        "Break-even revenue",
        money(after["break_even_revenue"]),
        help="At this staffing level: fixed labour, overheads and campaign spending / unit contribution; variable ingredients, waste and commission per order stay constant",
    )
    comparison = compare(baseline, assumptions)
    wanted = [
        "revenue",
        "cogs",
        "labour_cost",
        "commission_cost",
        "campaign_cost",
        "overhead_cost",
        "operating_contribution",
        "operating_profit",
        "operating_margin_pct",
        "transactions",
        "paid_hours",
        "break_even_orders",
        "break_even_revenue",
    ]
    comparison["restaurant_id"] = sid
    comparison["baseline_month"] = month
    table(comparison[comparison.metric.isin(wanted)], "scenario_comparison")
    if not np.isfinite(after["break_even_revenue"]):
        st.warning(
            "No finite break-even: contribution per order is zero or negative under these assumptions."
        )
    width = (
        st.slider("Demand sensitivity range (±%)", 0, 30, 10, key="sensitivity") / 100
    )
    ranges = sensitivity(baseline, assumptions, width)
    chart(
        px.bar(
            ranges,
            x="case",
            y="operating_profit",
            title="Demand sensitivity · conditional operating profit",
            color_discrete_sequence=COLOURS,
        )
    )
    table(
        ranges[
            [
                "case",
                "demand_change",
                "revenue",
                "cogs",
                "labour_cost",
                "operating_profit",
                "operating_margin_pct",
            ]
        ],
        "scenario_sensitivity",
    )
    st.download_button(
        "Download scenario assumptions JSON",
        json.dumps(
            {
                "restaurant_id": sid,
                "month": month,
                "assumptions": assumptions.__dict__,
                "demand_sensitivity_width": width,
            },
            indent=2,
        ),
        "restops_scenario_assumptions.json",
        "application/json",
    )
    with st.expander("Accounting and operating assumptions", expanded=True):
        st.markdown(
            "- COGS includes sold ingredients and discarded food. Waste is not deducted again.\n- Discounts reduce list sales once. Loaded wages include simulated payroll loadings. Hours and wage changes multiply.\n- Order volume drives sold-ingredient cost; prices change revenue, not ingredient unit costs. Delivery mix and commission rate remain fixed.\n- Operating contribution deducts variable food, commission, labour and campaign spend; operating profit also deducts overheads. Margin means operating profit / revenue.\n- Overheads and campaign spend remain fixed. Break-even treats chosen labour hours as fixed within this period; step costs and capacity limits are absent.\n- Demand sensitivity is an assumption range, not a confidence interval. Validate price response, service outcomes and operational feasibility before adopting a change."
        )


def quality(f, meta, ids, month):
    st.write("Can we trust the inputs, and which records were repaired or excluded?")
    q = meta["quality"]
    checks = f["validation_checks"]
    cols = st.columns(4)
    cols[0].metric("Validated source orders", f"{q['clean_orders']:,}")
    cols[1].metric("Quarantined orders", f"{q['quarantined_orders']:,}")
    cols[2].metric("Failed validation rules", str(int(checks.status.eq("FAIL").sum())))
    cols[3].metric("Contract checks", str(len(checks)))
    st.caption(
        "Quality monitoring describes the full source-pipeline snapshot, not just the selected restaurant/month. Checks cover schema, primary keys, relationships, categories, dates, monetary values and independent SQL reconciliation. Rule counts can overlap."
    )
    if meta["mode"] == "demo":
        st.info(
            "Demo mode contains precomputed full-pipeline audit evidence and a 100-line quarantine preview. It does not include the raw transaction ledger for a fresh source audit."
        )
    table(checks, "validation_checks")
    table(
        f["data_quality_audit"],
        "cleaning_audit",
        "Repairs use explicit business references or comparable rate classes; raw exports remain immutable during cleaning.",
    )
    missing = f["missing_values"]
    table(
        missing[missing.missing_rows.gt(0)],
        "missing_values",
        "Optional anonymous IDs and unanswered surveys remain missing. Missing required data must fail the contract rather than appear as zero.",
    )
    table(
        f["quarantine_sample"],
        "quarantine_preview",
        "Preview only: complete affected baskets are excluded, including companion lines. Invalid net values are not interpretable as lost business revenue.",
    )
    st.markdown(
        "**Trace a result:** restaurant/month KPI → daily additive inputs → source order/line, shift, waste, campaign and cost IDs in SQLite or processed CSV. `reports/source_manifest.json` records SHA256 hashes of raw and cleaned sources. The audit records rule-level counts; individual repaired cells are not fully versioned."
    )


FUNCTIONS = dict(
    zip(
        VIEWS,
        [
            executive,
            investigation,
            labour,
            customers,
            promotions,
            forecasting,
            scenario,
            quality,
        ],
    )
)


def render_view(view, frames, meta, ids, month):
    FUNCTIONS[view](frames, meta, ids, month)
    pack = ROOT / "reports/exports/weekly_management_pack.xlsx"
    if pack.exists():
        st.download_button(
            "Download prepared Excel management pack",
            pack.read_bytes(),
            pack.name,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="xlsx_pack",
        )
        st.caption(
            "Prepared snapshot: latest historical seven days, default 28-day planning assumptions and the labelled illustrative Wollongong scenario. It does not reflect unsaved app filters or slider changes; use each view's CSV/JSON download for current selections."
        )
