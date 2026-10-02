# Business requirements

**Project:** RESTOPS — Restaurant Operations & Profitability Intelligence Platform  
**Company:** Southern Table Hospitality (fictional)  
**Scope:** 18 Australian restaurants, January 2024–December 2025  
**Primary users:** Area Managers and Operations Managers

## Problem statement

Management receives disconnected sales, roster, finance, customer and promotion
exports. Revenue movements are visible, but the causes and appropriate actions
are unclear. Inconsistent definitions and manual joins can duplicate costs and
create conflicting versions of performance.

## Objectives

1. Explain which restaurants underperform and which factors merit investigation.
2. Match staffing and preparation decisions to the timing of demand.
3. Evaluate product, waste, promotion and customer economics consistently.
4. Provide tested four-week sales forecasts and a weekly management worklist.
5. Make every result traceable to a definition, input and reproducible calculation.

## Current and future process

**Current:** download exports → reconcile manually → compare revenue → discuss
possible causes → adjust operations with limited measurement.

**Future:** validate exports → quarantine exceptions → refresh financial and
operational marts → review comparable stores → investigate drivers → choose a
small intervention → monitor a named success measure → retain or revise it.

## Requirements and traceability

| ID | Business requirement | Delivery | Acceptance criterion |
|---|---|---|---|
| BR01 | Explain restaurant performance | Store-month KPIs, segmentation, executive report | 18 stores, weighted margins, documented cost bridge |
| BR02 | Assess staffing efficiency | Store-hour capacity and daypart SQL | Actual paid hours reconcile to shifts; pressure and spare capacity visible |
| BR03 | Evaluate products | Product-month mart and category analysis | Revenue and ingredient contribution reconcile to the sales ledger |
| BR04 | Identify excess waste | Waste rates, reasons and peer opportunity table | Definition and comparable peer base visible |
| BR05 | Assess staffing/customer relationship | Residualised association and bootstrap interval | Demand, store and calendar controls; no causal claim |
| BR06 | Assess promotions | Matched promotion estimates | Counterfactual, cost inclusion, controls and uncertainty documented |
| BR07 | Understand loyalty | RFM segments, cohorts, early behaviour analysis | Identified denominator and 90-day eligibility explicit |
| BR08 | Forecast four weeks | Model comparison and daily forecast export | Three validation folds, separate holdout, MAE/RMSE/MAPE/WAPE |
| BR09 | Support weekly action | Four-page Tableau spec and management reports | Findings state what, why, impact, action and owner |
| BR10 | Reproduce and audit results | Pipeline, SQL, tests, quality audit | One-command rebuild and Python/SQL reconciliation |

## Functional requirements

- FR01: Seeded generation of connected, fictional source exports.
- FR02: Immutable raw exports during cleaning, explicit keys, and auditable repairs.
- FR03: Whole-order exclusion when an unrecoverable basket line is damaged.
- FR04: Separate aggregation of facts before combining financial results.
- FR05: Shared KPI definitions, target comparisons and visible index components.
- FR06: Transparent customer/store segments and prior-only anomaly baselines.
- FR07: Time-based forecasting with recursive future features and baseline comparison.
- FR08: UTF-8 CSV exports for Tableau and Excel, without accidental row indexes.
- FR09: Six notebooks delegating implementation to reusable Python modules.
- FR10: Clear management reporting, assumptions, limitations and action measures.

## Data requirements

Every table has an explicit grain and primary key. Facts reference stable
restaurant, product and order identifiers. Money is AUD; operational sales and
margins exclude GST. Local timestamps belong to the restaurant timezone and are
not incorrectly treated as a single national UTC time. Null anonymous customers
and unanswered surveys are allowed; null primary keys are not.

Source period completeness is assumed for zero-order trading hours. Stores are
open daily from 11:00–22:00 in the simulation. Monthly overhead allocations are
labelled when used for daily diagnostics. See `data_dictionary.md` and
`kpi_definitions.md` for table contracts and metric semantics.

## Scope boundaries

The project supplies an analytical pipeline, SQLite database, executed notebooks,
Tableau-ready marts, management exports, an eight-workflow local Streamlit app,
profit scenarios, hourly planning, a local visual overview and a Tableau
build specification. It does not include live POS integration, production payroll,
an operational rostering engine, a published Tableau workbook or causal proof of
intervention benefits.

Expanded requirements FR11–FR20, user stories, non-functional criteria and
measurement responsibilities are in [the BA delivery pack](ba_delivery_pack.md).
See [requirements traceability](requirements_traceability.md) and the actual
developer/agent validation record; stakeholder acceptance is not claimed.

## Delivery acceptance

- At least 500,000 clean distinct orders across 18 stores and 24 months.
- All requested source datasets plus finance, delivery, calendar and management data.
- Quality defects detected, recovered where justified, or explicitly quarantined.
- No primary/foreign-key violations in the loaded database.
- Financial and product aggregates reconcile; hourly paid time matches the roster.
- Eight evidence-based findings and a prioritised management action plan.
- Reproduction instructions, tested modules and six executable notebooks.
