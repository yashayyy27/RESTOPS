"""Generate executive evidence, clean figures and an offline portfolio overview."""

import html
import json
import os

from .common import ROOT, REPORTS, TABLEAU, read, save
from .report_pages import render_pages

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

# Shared motorsport palette for report charts and notebook figures.
SURFACE, RACING_RED, AMBER, MUTED = "#19191f", "#ff3b30", "#ffc16a", "#b0b0bb"
TEXT, CYAN = "#f4f4f6", "#58d6df"


def money(value):
    """Readable Australian currency for management reports."""
    return f"A${value:,.0f}"


def style():
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.edgecolor": "#44444f",
            "axes.labelcolor": MUTED,
            "text.color": TEXT,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.titlecolor": TEXT,
            "axes.titlepad": 20,
            "savefig.dpi": 150,
        }
    )


def finish(fig, name):
    fig.tight_layout(pad=2)
    fig.savefig(REPORTS / "figures" / name, bbox_inches="tight")
    plt.close(fig)


def promotion_summary(promo):
    """Keep estimated contribution and its campaign-cost denominator aligned."""
    return (
        promo.dropna(subset=["incremental_contribution"])
        .groupby("campaign_name")[
            ["incremental_contribution", "campaign_cost", "incremental_revenue"]
        ]
        .sum()
    )


def charts(daily, monthly, latest, products, promo, customers, forecasts, metrics):
    """Save charts with meaningful labels and consistent visual hierarchy."""
    style()
    fig, ax = plt.subplots(figsize=(12, 3.2))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.axis("off")
    ax.plot(
        [0.015, 0.985],
        [0.98, 0.98],
        color=RACING_RED,
        linewidth=4,
        transform=ax.transAxes,
    )
    ax.plot(
        [0.68, 0.96, 0.96],
        [0.74, 0.74, 0.24],
        color=RACING_RED,
        linewidth=3,
        transform=ax.transAxes,
    )
    ax.text(
        0.02,
        0.75,
        "RESTOPS",
        fontsize=48,
        color="white",
        fontweight="bold",
        fontstyle="italic",
        transform=ax.transAxes,
    )
    ax.text(
        0.025,
        0.47,
        "Restaurant Operations & Profitability Intelligence",
        fontsize=16,
        color="#c5c5ce",
        transform=ax.transAxes,
    )
    ax.text(
        0.025,
        0.15,
        "18 RESTAURANTS     /     24 MONTHS     /     FROM DATA TO WEEKLY DECISIONS",
        fontsize=11,
        color=RACING_RED,
        transform=ax.transAxes,
    )
    finish(fig, "restops_cover.png")

    chain = monthly.groupby("month")[["revenue", "operating_profit"]].sum()
    fig, ax = plt.subplots(figsize=(11, 4.3))
    ax.plot(
        range(len(chain)),
        chain.revenue / 1e6,
        color=RACING_RED,
        linewidth=2.5,
        label="Revenue",
    )
    ax.plot(
        range(len(chain)),
        chain.operating_profit / 1e6,
        color=CYAN,
        linewidth=2.5,
        label="Operating profit",
    )
    ax.set(
        title="Growth needs a profitability check",
        ylabel="AUD millions",
        xlabel="Month",
    )
    ticks = np.arange(0, len(chain), 3)
    ax.set_xticks(ticks, chain.index[ticks], rotation=0)
    ax.grid(axis="y", alpha=0.15)
    ax.legend(frameon=False, ncol=2)
    finish(fig, "executive_trend.png")

    ranked = latest.sort_values("operating_margin_pct")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(
        ranked.restaurant_name,
        ranked.operating_margin_pct * 100,
        color=[AMBER if i < 3 else RACING_RED for i in range(len(ranked))],
    )
    ax.axvline(16, color=MUTED, linestyle="--", linewidth=1, label="16% budget target")
    ax.set(
        title="Where area managers should focus",
        xlabel="Operating margin · Oct–Dec 2025 (%)",
    )
    ax.legend(frameon=False, loc="lower right")
    finish(fig, "restaurant_margins.png")

    hourly = read("store_hour")
    heat = (
        hourly.groupby(["weekday", "hour"])
        .staffing_status.apply(lambda x: x.eq("Pressure").mean())
        .unstack()
    )
    fig, ax = plt.subplots(figsize=(10, 4.5))
    pressure_palette = LinearSegmentedColormap.from_list(
        "service_pressure", ["#202027", "#6c2b25", RACING_RED, "#ffbf85"]
    )
    im = ax.imshow(
        heat.to_numpy() * 100, cmap=pressure_palette, aspect="auto", vmin=0, vmax=100
    )
    ax.set_xticks(range(11), [f"{h}:00" for h in range(11, 22)])
    ax.set_yticks(range(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    ax.set(title="Service pressure concentrates around meal peaks", xlabel="Local hour")
    fig.colorbar(im, ax=ax, label="Share of observed store-hours under pressure (%)")
    finish(fig, "staffing_heatmap.png")

    cat = (
        products.groupby("category")[
            ["revenue", "ingredient_cost", "gross_contribution"]
        ]
        .sum()
        .sort_values("gross_contribution")
    )
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.barh(cat.index, cat.gross_contribution / 1e6, color=RACING_RED)
    ax.set(
        title="Category contribution supports menu decisions",
        xlabel="Gross contribution · 2024–2025 (AUD millions)",
    )
    finish(fig, "product_contribution.png")

    campaign = promotion_summary(promo)
    roi = campaign.incremental_contribution / campaign.campaign_cost
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.bar(roi.index, roi * 100, color=[RACING_RED if v >= 0 else AMBER for v in roi])
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.set(
        title="Discounted volume does not guarantee contribution",
        ylabel="Estimated campaign ROI (%)",
    )
    ax.text(
        0,
        -0.23,
        "Matched observational estimate; campaign-level uncertainty is in the export.",
        transform=ax.transAxes,
        color=MUTED,
        fontsize=9,
    )
    finish(fig, "promotion_roi.png")

    seg = customers.groupby("segment").size().sort_values()
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.barh(seg.index, seg.values, color=RACING_RED)
    ax.set(
        title="A practical customer retention worklist",
        xlabel="Identified customers · snapshot at 31 Dec 2025",
    )
    finish(fig, "customer_segments.png")

    actual = daily.groupby("business_date").revenue.sum().tail(56)
    future = forecasts.groupby("business_date").forecast_revenue.sum()
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.plot(
        pd.to_datetime(actual.index),
        actual.values / 1000,
        color=MUTED,
        label="Historical actual",
    )
    ax.plot(
        pd.to_datetime(future.index),
        future.values / 1000,
        color=RACING_RED,
        label="Selected four-week forecast",
    )
    ax.set(
        title="Plan the next four weeks with a tested baseline",
        ylabel="Chain revenue (AUD thousands)",
        xlabel="Date",
    )
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.15)
    fig.autofmt_xdate()
    finish(fig, "forecast.png")


def findings(daily, latest, products, promo, customers, metrics, summary, forecast):
    """Construct eight evidence-backed findings; never hard-code business outcomes."""
    low = latest.sort_values("operating_margin_pct").iloc[0]
    peers = latest[
        latest.location_type.eq(low.location_type)
        & latest.restaurant_id.ne(low.restaurant_id)
    ]
    peer_margin = peers.operating_profit.sum() / peers.revenue.sum()
    hourly = read("store_hour")
    peak = hourly[hourly.hour.isin([12, 13, 18, 19])]
    offpeak = hourly[hourly.hour.isin([14, 15, 16, 17])]
    high_waste = latest.sort_values(
        "estimated_waste_opportunity", ascending=False
    ).iloc[0]
    campaign = promotion_summary(promo)
    campaign["roi"] = campaign.incremental_contribution / campaign.campaign_cost
    worst = campaign.sort_values("roi").iloc[0]
    worst_name = campaign.sort_values("roi").index[0]
    cat = products.groupby("category")[
        ["revenue", "ingredient_cost", "gross_contribution"]
    ].sum()
    top_cat = cat.gross_contribution.idxmax()
    high_margin_cat = ((cat.revenue - cat.ingredient_cost) / cat.revenue).idxmax()
    cohort = customers[customers.eligible_90d]
    early = cohort.groupby("early_activity_band").return_days31_90.mean()
    staffing = summary["staffing_association"]
    selected = metrics[
        (metrics.evaluation_period.eq("Holdout"))
        & metrics.model.eq(forecast["selected_model"])
    ].iloc[0]
    naive = metrics[
        (metrics.evaluation_period.eq("Holdout")) & metrics.model.eq("Seasonal naive")
    ].iloc[0]
    improvement = (naive.mae - selected.mae) / naive.mae
    return [
        {
            "title": "Prioritise the weakest store's cost structure",
            "what": f"{low.restaurant_name} recorded {low.operating_margin_pct:.1%} operating margin in Q4 versus {peer_margin:.1%} across its location peers.",
            "why": f"Its labour cost was {low.labour_cost_pct:.1%} of sales and waste was {low.waste_pct:.1%}. These are accounting drivers; store and demand differences still matter.",
            "impact": f"Q4 operating profit was {money(low.operating_profit)} on {money(low.revenue)} sales. A peer-margin gap is an investigation signal, not guaranteed recoverable profit.",
            "action": "Area Manager: review four weeks of rosters and waste logs, then pilot a demand-based roster. Monitor margin and service scores together.",
            "priority": "High",
        },
        {
            "title": "Move staffing toward meal peaks",
            "what": f"{peak.staffing_status.eq('Pressure').mean():.1%} of peak-hour observations exceeded modelled service capacity; {offpeak.staffing_status.eq('Spare capacity').mean():.1%} of off-peak observations had spare capacity.",
            "why": "Broad shifts spread paid hours across the day while orders concentrate at lunch and dinner. Capacity is an illustrative six orders per service hour, not a measured service standard.",
            "impact": "Peak pressure can affect experience while spare capacity raises cost per order. The exports identify the store, weekday and hour for a roster trial.",
            "action": "Workforce Planning: trial staggered starts and meal-peak overlap at two stores; keep total hours stable initially and compare service outcomes.",
            "priority": "High",
        },
        {
            "title": "Target excess food waste with preparation controls",
            "what": f"{high_waste.restaurant_name} had Q4 waste of {high_waste.waste_pct:.1%}, versus its location-peer median of {high_waste.waste_peer_median:.1%}.",
            "why": "The synthetic operation links preparation variability and management efficiency to waste. Product and reason exports support investigation of specific preparation practices.",
            "impact": f"Matching the peer rate on the same ingredient-cost base suggests {money(high_waste.estimated_waste_opportunity)} of quarterly waste-cost opportunity; feasibility is untested.",
            "action": "Restaurant Manager: pilot smaller batches and daily waste reason reviews. Track waste cost alongside stock-outs and satisfaction for four weeks.",
            "priority": "High",
        },
        {
            "title": "Review the weakest promotion before repeating it",
            "what": f"{worst_name} produced estimated incremental revenue of {money(worst.incremental_revenue)} and incremental contribution of {money(worst.incremental_contribution)} after campaign costs; ROI was {worst.roi:.0%}.",
            "why": "This summary includes only campaigns with eligible controls; unavailable estimates and their spend are excluded together. Sales uplift must pay for discounts, ingredient costs, commissions, incremental labour and campaign spending. Matched controls provide an imperfect counterfactual.",
            "impact": "Repeating a weak offer can erode contribution despite an attractive sales headline. Campaign-specific confidence ranges may cross zero.",
            "action": "Marketing and Finance: use a randomised store trial to compare a smaller discount or bundle. Make contribution the primary success metric.",
            "priority": "High",
        },
        {
            "title": "Use contribution and margin together in menu decisions",
            "what": f"{top_cat} generated {cat.loc[top_cat, 'gross_contribution'] / cat.gross_contribution.sum():.1%} of gross contribution, while {high_margin_cat} had the highest category ingredient margin.",
            "why": "High-volume mains and lower-cost add-ons play different roles. Revenue alone does not capture ingredient economics.",
            "impact": "Menu placement and attachments can improve mix, but gross contribution excludes additional preparation labour and cannibalisation.",
            "action": "Operations and Marketing: test one complementary add-on bundle; evaluate basket contribution, uptake and service time.",
            "priority": "Medium",
        },
        {
            "title": "Use early activity to prioritise retention experiments",
            "what": f"Among fully observed customers, {early.get('4+ visits', np.nan):.1%} of those with four or more early visits returned in days 31–90, versus {early.get('1 visit', np.nan):.1%} with one early visit.",
            "why": "Early activity reflects customer preference and opportunity to visit. Redemption comparisons are stratified by activity and cannot establish loyalty causation.",
            "impact": f"The eligible identified-customer 90-day repeat rate was {cohort.repeat_within_90d.mean():.1%}. Anonymous visitors are outside this denominator.",
            "action": "Loyalty Manager: test a second-visit message with a random holdout among low-activity new members; measure return rate and contribution.",
            "priority": "Medium",
        },
        {
            "title": "Treat service pressure as an experience warning",
            "what": f"Controlled service-pressure/satisfaction correlation was {staffing['controlled_correlation']:.2f}, with an approximate store-bootstrap interval of [{staffing['ci_low']:.2f}, {staffing['ci_high']:.2f}].",
            "why": "The comparison adjusts for store, weekday, calendar month and order volume. Synthetic staffing mechanisms contribute to the relationship; selective survey responses remain a limitation.",
            "impact": "Service scores provide a guardrail against roster changes that improve labour ratios but overload busy periods.",
            "action": "Area Manager: review pressure and satisfaction together weekly, then evaluate roster pilots with pre-agreed service and cost measures.",
            "priority": "Medium",
        },
        {
            "title": "Use evaluated forecasts for four-week planning",
            "what": f"{forecast['selected_model']} was selected using validation MAE. Final holdout MAE was {money(selected.mae)} per store-day, RMSE {money(selected.rmse)}, and MAPE {selected.mape:.1f}%.",
            "why": f"Its holdout MAE improvement over the seasonal naive comparator was {improvement:.1%}. Calendar and lag features provide information beyond a repeated weekly pattern when useful.",
            "impact": f"The next 28 synthetic planning days total {money(forecast['forecast_total'])}. Forecast error should be considered before committing labour or stock.",
            "action": "Workforce Planning: combine daily forecasts with each store's observed basket value and hourly mix; revisit weekly and record overrides.",
            "priority": "Medium",
        },
    ]


def run():
    daily, monthly = read("store_day"), read("store_month_kpis")
    latest, products = read("latest_store_opportunities", TABLEAU), read(
        "product_month", TABLEAU
    )
    promo, customers = read("promotion_effectiveness", TABLEAU), read(
        "customer_segments", TABLEAU
    )
    forecasts = read("forecast_daily", TABLEAU)
    metrics = pd.read_csv(REPORTS / "exports/forecast_metrics.csv")
    summary = json.loads((REPORTS / "analysis_summary.json").read_text())
    forecast = json.loads((REPORTS / "forecast_summary.json").read_text())
    quality = json.loads((REPORTS / "quality_summary.json").read_text())
    insights = findings(
        daily, latest, products, promo, customers, metrics, summary, forecast
    )
    charts(daily, monthly, latest, products, promo, customers, forecasts, metrics)
    executive = [
        "# RESTOPS · Executive summary",
        "",
        "**Southern Table Hospitality | January 2024–December 2025 | Synthetic portfolio case study**",
        "",
        f"The validated operation contains {quality['clean_orders']:,} orders across 18 restaurants. Revenue was {money(daily.revenue.sum())}, operating profit {money(daily.operating_profit.sum())}, and operating margin {daily.operating_profit.sum()/daily.revenue.sum():.1%}.",
        "",
        "These are fictional outcomes. Recommendations are testable management hypotheses; observational estimates do not establish causal business effects.",
        "",
    ]
    for i, finding in enumerate(insights, 1):
        executive += [
            f"## {i}. {finding['title']}",
            "",
            f"**What happened:** {finding['what']}",
            "",
            f"**Why:** {finding['why']}",
            "",
            f"**Business impact:** {finding['impact']}",
            "",
            f"**Recommended action:** {finding['action']}",
            "",
        ]
    (REPORTS / "executive_summary.md").write_text("\n".join(executive))
    correlations = pd.read_csv(REPORTS / "exports/kpi_correlations.csv").set_index(
        "metric"
    )
    drivers = correlations["operating_margin_pct"].drop("operating_margin_pct")
    drivers = drivers.sort_values(key=lambda values: values.abs(), ascending=False)
    driver_report = [
        "# Profitability relationships",
        "",
        "Business question: which observed operational KPIs have the strongest relationship with operating margin?",
        "",
        "Population: 432 restaurant-month observations across January 2024–December 2025.",
        "",
        "| Operational KPI | Pearson correlation with operating margin |",
        "|---|---:|",
    ]
    driver_report += [
        f"| {name.replace('_', ' ')} | {value:.3f} |" for name, value in drivers.items()
    ]
    driver_report += [
        "",
        "Labour cost %, sales per labour hour and waste share accounting inputs or denominators with profit. Their correlations describe the financial structure and do not isolate independent causal effects.",
        "",
        "Use the cost bridge to quantify recorded financial changes, then investigate roster timing and waste reasons. Satisfaction and delivery correlations are observational and may be confounded by demand, location, channel mix and survey selection.",
        "",
        "A controlled staffing/experience association is reported separately in the executive summary. Proposed interventions should be evaluated with service guardrails and comparable or randomised controls.",
    ]
    (REPORTS / "profitability_drivers.md").write_text("\n".join(driver_report) + "\n")
    save(
        drivers.rename("pearson_correlation")
        .rename_axis("operational_kpi")
        .reset_index(),
        REPORTS / "exports/profitability_drivers.csv",
    )
    recommendations = [
        "# Business recommendations",
        "",
        "Use the first month to run controlled operational pilots. Confirm capacity assumptions with managers before changing rosters. Estimates below are decision inputs, not committed savings.",
        "",
        "| Priority | Workstream | Owner | Timeframe | Success measure |",
        "|---|---|---|---|---|",
    ]
    actions = [
        (
            "High",
            "Peak roster pilot",
            "Area Manager / Workforce Planning",
            "Weeks 1–4",
            "Lower pressure share; satisfaction stable; labour cost controlled",
        ),
        (
            "High",
            "Waste preparation pilot",
            "Restaurant Manager",
            "Weeks 1–4",
            "Waste cost reduction without more stock-outs",
        ),
        (
            "High",
            "Promotion control trial",
            "Marketing / Finance",
            "Next campaign",
            "Positive incremental contribution with a credible interval",
        ),
        (
            "Medium",
            "Menu attachment experiment",
            "Operations / Marketing",
            "Weeks 3–6",
            "Higher basket contribution without slower service",
        ),
        (
            "Medium",
            "Second-visit holdout test",
            "Loyalty Manager",
            "90-day measurement",
            "Incremental return rate and contribution",
        ),
        (
            "Medium",
            "Weekly forecast review",
            "Workforce Planning",
            "Weekly",
            "Forecast WAPE and override accuracy",
        ),
        (
            "High",
            "Source validation controls",
            "Finance / Analyst",
            "Before refresh",
            "No duplicate primary keys; reconciled revenue and complete orders",
        ),
    ]
    recommendations += ["| " + " | ".join(row) + " |" for row in actions]
    recommendations += [
        "",
        "## Weekly management rhythm",
        "",
        "Monday: validate refreshed data and investigate exceptions. Tuesday: review the lowest-performing stores and approve a small action list. Midweek: update rosters and preparation plans. Next Monday: compare outcomes, document overrides, and retain or revise the intervention.",
        "",
        "## Guardrails",
        "",
        "Do not cut staffing solely to improve the performance index. Do not average percentage KPIs across unequal stores. Do not treat estimated promotion uplift, clustering, or correlation as proof of causation. Reassess the synthetic capacity standard before any real-world use.",
    ]
    (REPORTS / "business_recommendations.md").write_text(
        "\n".join(recommendations) + "\n"
    )
    payload = {
        "insights": insights,
        "summary": {
            "revenue": float(daily.revenue.sum()),
            "profit": float(daily.operating_profit.sum()),
            "orders": quality["clean_orders"],
            "repeat_rate": summary["repeat_customer_rate"],
            "selected_model": forecast["selected_model"],
        },
        "stores": json.loads(latest.to_json(orient="records")),
        "monthly": json.loads(
            monthly[["restaurant_id", "month", "revenue", "operating_profit"]].to_json(
                orient="records"
            )
        ),
    }
    (REPORTS / "portfolio_data.json").write_text(json.dumps(payload, indent=2))
    template = (ROOT / "src/portfolio_template.html").read_text()
    (REPORTS / "portfolio.html").write_text(
        template.replace("__RESTOPS_DATA__", json.dumps(payload).replace("</", "<\\/"))
    )
    (REPORTS / "insights.json").write_text(json.dumps(insights, indent=2))
    render_pages()
    # Compact CSVs open in Excel; no expensive raw-basket workbook.
    save(latest, REPORTS / "exports/management_store_scorecard.csv")
    save(promo, REPORTS / "exports/promotion_review.csv")
    save(forecasts, REPORTS / "exports/four_week_forecast.csv")
    print(
        "Created eight executive findings, management exports, charts and portfolio overview.",
        flush=True,
    )


if __name__ == "__main__":
    run()
