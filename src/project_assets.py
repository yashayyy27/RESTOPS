"""Create navigable notebooks, schema dictionaries, previews and recruiter README."""

import json

import nbformat
import pandas as pd

from .clean_data import PRIMARY_KEYS
from .common import PROCESSED, RAW, REPORTS, ROOT, TABLEAU, read, save

GRAINS = {
    "restaurants": "One restaurant",
    "products": "One menu product",
    "transactions": "One product line in a complete customer order",
    "labour": "One employee shift",
    "customer_feedback": "One survey submission",
    "loyalty": "One identified-customer loyalty event",
    "promotions": "One campaign at one restaurant",
    "waste": "One restaurant/product/date waste record",
    "targets": "One restaurant/month budget",
    "operating_costs": "One restaurant/month/cost-category ledger entry",
    "delivery": "One completed delivery order",
    "calendar": "One state/date",
    "manager_assignments": "One manager/store effective period",
}

DESCRIPTIONS = {
    "restaurant_id": "Stable restaurant foreign key (1–18); primary key in the restaurant master",
    "restaurant_name": "Canonical restaurant display name; cleaned from the restaurant master",
    "state": "NSW, VIC or QLD; determines state calendar and timezone",
    "location_type": "CBD, Suburban, Shopping centre or Regional peer group",
    "area": "Fictional management area: East, South or North",
    "timezone": "IANA timezone for local POS and roster timestamps",
    "seats": "Simulated dining capacity; seats",
    "opening_date": "Restaurant opening date; ISO date",
    "open_hour": "Local opening hour, inclusive",
    "close_hour": "Local closing hour, exclusive",
    "product_id": "Stable product foreign key; primary key in product master",
    "product_name": "Menu item name validated against the approved category taxonomy",
    "category": "Canonical category: Mains, Salads, Sides, Drinks or Desserts",
    "menu_price_ex_gst": "2024 base unit menu price; AUD excluding GST",
    "standard_ingredient_cost": "2024 base unit ingredient cost; AUD",
    "transaction_line_id": "Unique exported POS product-line key",
    "order_id": "Basket identifier; multiple lines belong to one order; optional for enrolment/unlinked surveys",
    "timestamp_local": "Store-local order timestamp, YYYY-MM-DD HH:MM:SS; interpret with restaurant timezone",
    "quantity": "Units sold on the line; validated range 1–20",
    "channel": "Dine-in, Takeaway or Delivery",
    "customer_id": "Anonymous store-local customer identifier; null means unidentified order",
    "promotion_id": "Campaign foreign key; null means no attributed campaign",
    "list_revenue": "Line quantity × sale-time menu price before discount; AUD excluding GST",
    "discount_amount": "Line or order discount already deducted from revenue; AUD excluding GST",
    "net_revenue": "Line sales after discount; AUD excluding GST",
    "gst_amount": "Simplified tax component: 10% of net line revenue; AUD",
    "ingredient_cost": "Sale-time ingredient cost for sold units; excludes waste; AUD",
    "business_date": "Local trading date, ISO YYYY-MM-DD",
    "month": "YYYY-MM for facts/budgets; integer 1–12 only in calendar",
    "hour": "Local order hour, 11–21",
    "daypart": "Lunch 11:00–15:59, Dinner 16:00–21:59",
    "shift_id": "Unique employee shift key",
    "employee_id": "Fictional employee identifier; no personal data",
    "role": "Service, Kitchen or Manager",
    "scheduled_start": "Planned shift start in local time",
    "scheduled_end": "Planned shift end in local time",
    "actual_start": "Observed shift start in local time; scheduled=actual in this simulation",
    "actual_end": "Observed shift end in local time",
    "break_hours": "Unpaid break duration; hours",
    "paid_hours": "Actual shift duration less unpaid breaks; hours",
    "hourly_cost": "Simulated loaded cost for role and weekend/holiday class; AUD/hour",
    "rate_imputed": "1 if hourly cost inferred from comparable valid shifts; otherwise 0",
    "labour_cost": "Paid hours × loaded hourly cost; AUD",
    "feedback_id": "Unique survey submission key",
    "overall_score": "Overall satisfaction 1–5; null for unanswered or invalid rating",
    "food_score": "Food satisfaction integer 1–5",
    "service_score": "Service satisfaction integer 1–5",
    "loyalty_event_id": "Unique loyalty event key",
    "event_date": "Local event date; ISO YYYY-MM-DD",
    "event_type": "Enroll, Earn or Redeem; redemption is behavioural, not an extra monetary discount",
    "points": "Points earned (positive), redeemed (negative), or zero on enrolment; no currency conversion",
    "campaign_name": "Local Lunch, Winter Value or Spring Social",
    "start_date": "Campaign or assignment effective start, inclusive; ISO date",
    "end_date": "Campaign or assignment effective end, inclusive; ISO date",
    "discount_rate": "Fraction of pre-discount sales; 0.10 means 10%",
    "eligible_category": "All in this version; campaign applies to every product",
    "campaign_cost": "Unique campaign/store spend, or allocated daily campaign spend in marts; AUD",
    "waste_id": "Unique waste ledger key",
    "waste_units": "Discarded product-equivalent units; non-negative count",
    "waste_cost": "Discarded unit ingredient cost at period prices; AUD",
    "reason": "Over-preparation, Spoilage or Preparation error; illustrative classification",
    "revenue_target": "Independent restaurant/month revenue budget; AUD excluding GST",
    "operating_margin_target": "Budget operating margin fraction",
    "labour_pct_target": "Maximum desired labour-cost/revenue fraction",
    "waste_pct_target": "Desired waste/(sold ingredient cost + waste) fraction",
    "satisfaction_target": "Desired mean score on the 1–5 scale",
    "cost_id": "Unique operating-cost ledger key",
    "cost_category": "Rent, Utilities or Other overhead; labour/ingredients excluded to prevent duplication",
    "amount": "Monthly operating-cost amount; AUD",
    "promised_minutes": "Promised delivery time from order; minutes",
    "actual_minutes": "Observed simulated delivery time; minutes",
    "commission_cost": "Platform commission at 25% of net delivery sales; AUD",
    "delivery_fee": "Restaurant-collected fee; zero in this simulation",
    "status": "Completed; cancellations are not simulated",
    "holiday_name": "State public holiday label from holidays package; blank on ordinary dates",
    "is_public_holiday": "1 for public holiday, else 0",
    "weekday": "Monday=0 through Sunday=6",
    "is_weekend": "1 for Saturday/Sunday, else 0",
    "season": "Australian meteorological season: Summer, Autumn, Winter or Spring",
    "school_holiday_proxy": "Illustrative seasonal proxy, not an official school calendar; 0/1",
    "manager_id": "Anonymous simulated manager; one per store, so manager effect is not separately identifiable",
}


def dictionary():
    """Document every cleaned source column and the analytical output grains."""
    lines = [
        "# Data dictionary",
        "",
        "**Company:** Southern Table Hospitality (fictional). **Currency:** AUD. **Dates:** local ISO dates; money excludes GST except `gst_amount`. Ratios are 0–1 unless stated otherwise.",
        "",
        "Tables are generated for 2024–2025. Cleaned source tables preserve source grain; derived fields are marked by their definitions. Primary keys must be unique/non-null. Restaurant/product foreign keys must resolve. Anonymous customer IDs, non-promoted campaign IDs, unanswered survey scores and optional order links can be null.",
        "",
    ]
    rows = []
    for name, grain in GRAINS.items():
        preview = pd.read_csv(PROCESSED / f"{name}.csv", nrows=100)
        keys = ", ".join(PRIMARY_KEYS[name])
        lines += [
            f"## {name}.csv",
            "",
            f"**Grain:** {grain}. **Primary key:** `{keys}`.",
            "",
            "| Field | Definition / units |",
            "|---|---|",
        ]
        for column in preview.columns:
            desc = DESCRIPTIONS[column]
            lines.append(f"| `{column}` | {desc} |")
            rows.append(
                {
                    "table": name,
                    "grain": grain,
                    "field": column,
                    "definition": desc,
                    "primary_key": column in PRIMARY_KEYS[name],
                }
            )
        lines.append("")
    lines += [
        "## Analytical tables",
        "",
        "| File | Grain | Important semantics |",
        "|---|---|---|",
        "| orders | Complete order | Revenue and ingredient cost sum the full basket; channel and customer are consistent across lines |",
        "| store_day | Restaurant/business date | Independent fact aggregates; daily fixed-cost allocations; score sum and answer count support weighting |",
        "| store_hour | Restaurant/business date/hour | Uniform paid-time allocation; six orders/service-hour capacity; Pressure/Spare capacity/Balanced are modelled flags |",
        "| store_month_kpis | Restaurant/month | Additive finance + recalculated rates, budgets, growth, index components and completeness |",
        "| product_month | Restaurant/month/product/channel | Orders-with-product is not additive across products; gross contribution excludes labour |",
        "| customer_segments | Identified customer/snapshot | Recency in days, frequency in distinct visit dates, monetary spend in AUD; eligibility and return flags |",
        "| customer_cohorts | Restaurant/first-observed month | Eligible 90-day denominator and returning customer numerator |",
        "| loyalty_behaviours | Early activity band/redemption flag | Early behaviour days 0–30; return outcome days 31–90 |",
        "| store_segments | Restaurant/full history | Standardised K-means features; exploratory three-cluster label |",
        "| promotion_effectiveness | Campaign/store | Observed and counterfactual revenue, controls, net incremental contribution, ROI fraction, approximate 95% ranges |",
        "| sales_anomalies | Flagged restaurant/date | Prior weekday median, robust z-score, holiday/campaign context |",
        "| staffing_patterns | Restaurant/weekday/hour | Average demand/capacity and pressure/spare counts over observed hours |",
        "| latest_store_opportunities | Restaurant/Q4 2025 | Weighted finance, mean monthly index, location-peer waste median and hypothetical waste-cost gap |",
        "| forecast_daily | Restaurant/future date | Predicted AUD revenue, horizon 1–28, origin, selected model and approximate empirical lower/upper 80% bands |",
        "| forecast_backtests | Restaurant/date/model/origin | Actual/predicted AUD, Validation/Holdout, fold; holdout bands use selected-model validation errors |",
        "| forecast_metrics | Evaluation period/fold/model | MAE/RMSE AUD; MAPE/WAPE in 0–100 percentage units; selected-model holdout coverage fraction |",
        "",
        "Analytical KPI definitions are in `kpi_definitions.md`; uncertainty, segmentation thresholds and assumptions are in `methodology.md`. `quality_reason` is the rejection explanation in quarantine exports. Null derived rates mean no valid denominator, not zero performance.",
    ]
    (ROOT / "docs/data_dictionary.md").write_text("\n".join(lines) + "\n")
    save(pd.DataFrame(rows), ROOT / "docs/data_dictionary.csv")


SETUP = """from pathlib import Path
import json
import os
import sys

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image, display
from src.common import read, TABLEAU, REPORTS
from src.reporting import style
style()
pd.set_option("display.max_columns", 12)
"""


def notebooks():
    """Six guided, output-bearing notebooks with reusable implementation."""
    specs = [
        (
            "01_data_generation",
            "Design a connected synthetic restaurant operation",
            [
                (
                    "m",
                    "**Business question:** What data does management need to diagnose restaurant performance?\n\nWe generate customer orders before product lines, link operational exports by stable identifiers, and introduce controlled export defects. No real company or customer data is used.",
                ),
                (
                    "c",
                    'REGENERATE = False  # Set True only when deliberately rebuilding raw exports.\nif REGENERATE:\n    from src.generate_data import run\n    run()\nmanifest = json.loads((ROOT / "data/raw/generation_manifest.json").read_text())\npd.Series({k: manifest[k] for k in ["seed", "orders_before_defects", "lines_before_defects"]})',
                ),
                (
                    "c",
                    'pd.DataFrame({"dataset": list(manifest["raw_rows"]), "raw_rows": list(manifest["raw_rows"].values())})',
                ),
                (
                    "c",
                    'read("restaurants").loc[:, ["restaurant_name", "state", "location_type", "seats"]]',
                ),
                (
                    "m",
                    "### Inspect the source grain\nA POS row is a product line, not an order. Null customer IDs are valid anonymous visits. Local timestamps require the restaurant timezone.",
                ),
                ("c", 'pd.read_csv(ROOT / "data/raw/transactions.csv", nrows=8)'),
                (
                    "c",
                    'pd.DataFrame([{k:v for k,v in defect.items() if k != "row_indices"} for defect in manifest["defects"]])',
                ),
                (
                    "m",
                    "**Decision:** Keep restaurant, product, order and date identifiers consistent across exports. Require both finance costs and operating context to explain profitability. The generation manifest is for independent QA; the cleaning module does not consume it.",
                ),
            ],
        ),
        (
            "02_data_cleaning",
            "Make metrics reliable before explaining performance",
            [
                (
                    "m",
                    "**Business question:** Can Finance trust the sales and cost populations?\n\nReview the cleaning audit and complete-order quarantine. Repairs require visible business rules; missing answers and unidentified customers retain their meaning.",
                ),
                (
                    "c",
                    'audit = pd.read_csv(REPORTS / "exports/data_quality_audit.csv")\naudit[audit.affected_rows > 0]',
                ),
                (
                    "c",
                    'quality = json.loads((REPORTS / "quality_summary.json").read_text())\npd.Series({k:v for k,v in quality.items() if k != "clean_rows"})',
                ),
                (
                    "m",
                    "### Quarantine full baskets\nRemoving only damaged product lines would retain incomplete orders and distort transaction value and product mix. Companion lines therefore leave the analytical sales population too.",
                ),
                (
                    "c",
                    'pd.read_csv(ROOT / "data/processed/quarantine_transactions.csv", nrows=6)[["order_id", "product_id", "quantity", "quality_reason"]]',
                ),
                (
                    "c",
                    'labour = read("labour")\nlabour.groupby("rate_imputed").agg(shifts=("shift_id", "size"), paid_hours=("paid_hours", "sum"))',
                ),
                (
                    "c",
                    'products = read("products")\nproducts.groupby("category").product_id.count()',
                ),
                (
                    "m",
                    "**Decision:** Investigate source exceptions before refreshing management reports. Category repairs use the checked-in approved menu taxonomy, not a hidden clean dataset. Retained survey nulls are excluded from score denominators.",
                ),
            ],
        ),
        (
            "03_exploratory_analysis",
            "Find financial trends and product economics",
            [
                (
                    "m",
                    "**Business question:** Where do sales and contribution come from, and does growth translate to profit?\n\nRecalculate rates from summed inputs. Use location peers and comparable periods rather than treating all stores as identical.",
                ),
                (
                    "c",
                    'monthly = read("store_month_kpis")\nchain = monthly.groupby("month")[["revenue", "operating_profit", "transactions", "labour_cost"]].sum()\nchain["margin"] = chain.operating_profit / chain.revenue\nchain.tail(6)',
                ),
                (
                    "c",
                    'display(Image(filename=str(REPORTS / "figures/executive_trend.png")))',
                ),
                (
                    "c",
                    'products = read("product_month", TABLEAU)\ncategory = products.groupby("category")[["revenue", "ingredient_cost", "gross_contribution", "units"]].sum()\ncategory["gross_margin"] = category.gross_contribution / category.revenue\ncategory.sort_values("gross_contribution", ascending=False)',
                ),
                (
                    "c",
                    'display(Image(filename=str(REPORTS / "figures/product_contribution.png")))',
                ),
                (
                    "m",
                    "### Verify through SQL\nThis query aggregates independent facts before joining; it is a useful safeguard against repeated labour and waste costs.",
                ),
                (
                    "c",
                    'import sqlite3\nwith sqlite3.connect(ROOT / "data/processed/restops.sqlite") as connection:\n    sql_kpis = pd.read_sql_query((ROOT / "sql/kpi_queries.sql").read_text(), connection)\nsql_kpis.head()',
                ),
                (
                    "c",
                    'insights = json.loads((REPORTS / "insights.json").read_text())\nprint(insights[4]["what"])\nprint(insights[4]["action"])',
                ),
                (
                    "m",
                    "**Decision:** Evaluate menu changes using contribution as well as sales. Ingredient margin alone does not capture preparation labour, delivery commissions or cannibalisation.",
                ),
            ],
        ),
        (
            "04_operational_analysis",
            "Explain staffing, waste and promotion exceptions",
            [
                (
                    "m",
                    "**Business question:** Which operational interventions deserve a pilot?\n\nCombine financial cost drivers with demand timing, peer waste rates, promotion contribution and customer-service guardrails.",
                ),
                (
                    "c",
                    'stores = read("latest_store_opportunities", TABLEAU)\nstores.sort_values("operating_margin_pct")[["restaurant_name", "operating_margin_pct", "labour_cost_pct", "waste_pct", "satisfaction_score"]].head(6)',
                ),
                (
                    "c",
                    'display(Image(filename=str(REPORTS / "figures/staffing_heatmap.png")))',
                ),
                (
                    "c",
                    'patterns = read("staffing_patterns", TABLEAU)\npatterns.sort_values("pressure_share", ascending=False).head(8)',
                ),
                (
                    "c",
                    'stores.sort_values("estimated_waste_opportunity", ascending=False)[["restaurant_name", "waste_pct", "waste_peer_median", "estimated_waste_opportunity"]].head(5)',
                ),
                (
                    "c",
                    'promos = read("promotion_effectiveness", TABLEAU)\npromos.dropna(subset=["incremental_contribution"]).groupby("campaign_name")[["incremental_revenue", "incremental_contribution", "campaign_cost"]].sum()',
                ),
                (
                    "c",
                    'display(Image(filename=str(REPORTS / "figures/promotion_roi.png")))',
                ),
                ("c", 'pd.read_csv(REPORTS / "exports/kpi_correlations.csv")'),
                ("c", 'read("sales_anomalies", TABLEAU).head(6)'),
                (
                    "c",
                    'summary = json.loads((REPORTS / "analysis_summary.json").read_text())\npd.Series(summary["staffing_association"])',
                ),
                (
                    "m",
                    "**Decision:** Pilot roster timing and waste controls with service guardrails. KPI profitability correlations share accounting inputs, and promotion controls are observational. Neither demonstrates a causal intervention effect. Anomalies are investigation flags, not automatic deletions.",
                ),
            ],
        ),
        (
            "05_customer_analysis",
            "Turn identified visits into a retention worklist",
            [
                (
                    "m",
                    "**Business question:** Which customer behaviours justify a retention experiment?\n\nSeparate the RFM snapshot from acquisition-style cohorts. First observed visit is not proven first-ever visit, and anonymous visitors remain outside these rates.",
                ),
                (
                    "c",
                    'customers = read("customer_segments", TABLEAU)\ncustomers.groupby("segment").agg(customers=("customer_id", "size"), mean_recency=("recency_days", "mean"), mean_visits=("visits", "mean"), spend=("spend", "sum"))',
                ),
                (
                    "c",
                    'display(Image(filename=str(REPORTS / "figures/customer_segments.png")))',
                ),
                (
                    "c",
                    'cohorts = read("customer_cohorts", TABLEAU)\ncohort_summary = cohorts.groupby("cohort_month")[["eligible_customers", "repeat_customers"]].sum()\ncohort_summary["repeat_rate"] = cohort_summary.repeat_customers / cohort_summary.eligible_customers.replace(0, float("nan"))\ncohort_summary.tail(8)',
                ),
                ("c", 'read("loyalty_behaviours", TABLEAU)'),
                (
                    "c",
                    'summary = json.loads((REPORTS / "analysis_summary.json").read_text())\nprint(f"Eligible customers: {summary["eligible_customers"]:,}")\nprint(f"90-day repeat rate: {summary["repeat_customer_rate"]:.1%}")',
                ),
                (
                    "m",
                    "**Decision:** Test a second-visit intervention with a random holdout among low-activity customers. Early visits/redemption in days 0–30 are compared with return outcomes in days 31–90, stratified by activity. Redemption is an association, not evidence of loyalty causation.",
                ),
            ],
        ),
        (
            "06_forecasting",
            "Evaluate a four-week demand planning forecast",
            [
                (
                    "m",
                    "**Business question:** What daily sales should managers expect over the next 28 days?\n\nCompare seasonal naive, calendar ridge and gradient boosting. Select by three rolling validation folds, then report a separate final-month holdout. Future lag values are recursive predictions.",
                ),
                (
                    "c",
                    'metrics = pd.read_csv(REPORTS / "exports/forecast_metrics.csv")\nmetrics[metrics.evaluation_period.eq("Validation")].groupby("model")[["mae", "rmse", "mape", "wape"]].mean().sort_values("mae")',
                ),
                (
                    "c",
                    'metrics[metrics.evaluation_period.eq("Holdout")][["model", "mae", "rmse", "mape", "wape", "interval_coverage"]]',
                ),
                (
                    "c",
                    'summary = json.loads((REPORTS / "forecast_summary.json").read_text())\npd.Series(summary)',
                ),
                ("c", 'display(Image(filename=str(REPORTS / "figures/forecast.png")))'),
                (
                    "c",
                    'future = read("forecast_daily", TABLEAU)\nfuture.groupby("restaurant_name").forecast_revenue.sum().sort_values(ascending=False).head(8)',
                ),
                (
                    "c",
                    'future[["restaurant_name", "business_date", "forecast_revenue", "lower_80", "upper_80", "horizon_day"]].head(8)',
                ),
                (
                    "m",
                    "**Decision:** Use store forecasts with hourly demand mix to discuss labour and preparation, while monitoring error and recording overrides. Empirical store bands are approximate, and must not be summed into a chain interval. January 2026 is a synthetic continuation of this historical case study.",
                ),
            ],
        ),
    ]
    for filename, title, cells in specs:
        notebook = nbformat.v4.new_notebook()
        notebook.cells = [
            nbformat.v4.new_markdown_cell(f"# RESTOPS · {title}"),
            nbformat.v4.new_code_cell(SETUP),
        ]
        notebook.cells += [
            (
                nbformat.v4.new_markdown_cell(text)
                if kind == "m"
                else nbformat.v4.new_code_cell(text)
            )
            for kind, text in cells
        ]
        notebook.metadata["kernelspec"] = {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        }
        notebook.metadata["language_info"] = {"name": "python"}
        nbformat.write(notebook, ROOT / "notebooks" / f"{filename}.ipynb")


def execute_notebooks():
    """Use this Python's kernel without installing a global kernelspec."""
    import os
    import sys
    from jupyter_client import KernelManager
    from nbclient import NotebookClient

    runtime = ROOT / ".cache/jupyter"
    runtime.mkdir(parents=True, exist_ok=True)
    os.environ["JUPYTER_RUNTIME_DIR"] = str(runtime)
    os.environ["JUPYTER_CONFIG_DIR"] = str(runtime)
    os.environ["JUPYTER_DATA_DIR"] = str(runtime)
    os.environ["IPYTHONDIR"] = str(ROOT / ".cache/ipython")
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path, as_version=4)
        manager = KernelManager(kernel_name="python3")
        manager.kernel_spec.argv = [
            sys.executable,
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
        client = NotebookClient(
            notebook,
            timeout=180,
            km=manager,
            resources={"metadata": {"path": str(ROOT)}},
        )
        try:
            client.execute()
        finally:
            # A supplied KernelManager is owned by us, so close it explicitly.
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
            manager.cleanup_resources()
        nbformat.write(notebook, path)
        print(f"Executed {path.name}", flush=True)


def samples():
    """Write small clearly labelled previews, not a misleading full dataset."""
    folder = ROOT / "data/sample"
    folder.mkdir(exist_ok=True)
    for name in (
        "restaurants",
        "products",
        "transactions",
        "labour",
        "customer_feedback",
        "loyalty",
        "promotions",
        "waste",
        "targets",
    ):
        frame = pd.read_csv(PROCESSED / f"{name}.csv", nrows=100)
        save(frame, folder / f"{name}_preview.csv")
    (folder / "README.md").write_text(
        "# Small data previews\n\nFirst 100 clean rows per requested source table (all rows for small dimensions). These previews are not a complete relational dataset and must not be used to reproduce the analysis. Run the pipeline for complete exports.\n"
    )


def readme():
    """Refresh measured evidence while preserving the curated application README."""
    quality = json.loads((REPORTS / "quality_summary.json").read_text())
    forecast = json.loads((REPORTS / "forecast_summary.json").read_text())
    insights = json.loads((REPORTS / "insights.json").read_text())
    metrics = pd.read_csv(REPORTS / "exports/forecast_metrics.csv")
    selected = metrics[
        metrics.evaluation_period.eq("Holdout")
        & metrics.model.eq(forecast["selected_model"])
    ].iloc[0]
    lines = [
        "# Generated analysis snapshot",
        "",
        "Synthetic fixed-seed evidence. The curated [portfolio README](../README.md) describes the working application and demonstration.",
        "",
        f"Validated orders: {quality['clean_orders']:,}; product lines: {quality['clean_lines']:,}; quarantined orders: {quality['quarantined_orders']:,}.",
        "",
        f"Selected model: {forecast['selected_model']}. Holdout MAE A${selected.mae:,.2f}; RMSE A${selected.rmse:,.2f}; WAPE {selected.wape:.2f}%.",
        "",
        "## Computed findings",
        "",
    ]
    lines += [f"- **{item['title']}:** {item['what']}" for item in insights]
    lines += [
        "",
        "Read the [executive summary](executive_summary.md), [action plan](business_recommendations.md), [weekly brief](weekly_management_brief.md) and [actual validation record](../docs/validation_results.md) for assumptions, proposed owners, success measures and limitations.",
    ]
    (REPORTS / "generated_portfolio_summary.md").write_text("\n".join(lines) + "\n")


def run():
    dictionary()
    samples()
    notebooks()
    readme()


if __name__ == "__main__":
    run()
