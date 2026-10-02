# Business Analyst delivery pack

RESTOPS is a fictional case study for Southern Table Hospitality. The stakeholder
roles and scenarios below are analytical design assumptions. No interviews,
stakeholder approvals, operational pilots or user research have been conducted.

## Problem and intended value

An Area Manager needs to decide which restaurants need attention, investigate the
commercial drivers, choose a feasible action and agree how to measure it.
Disconnected exports and inconsistent grains make revenue headlines unreliable
guides to contribution, labour coverage or customer experience.

The implemented system joins independently aggregated source facts, reconciles
financial totals and provides an interactive investigation, forecast and
scenario workflow. Value is demonstrated through reproducible calculations and
decision support. Financial benefits are conditional estimates, not realised ROI.

## Scope

Included: 18 synthetic Australian restaurants, 2024–2025 historical data,
January 2026 forecast continuation, nine Streamlit workflows with public-session and editable local modes, offline
reports, SQLite, notebooks, audit and quarantine, Tableau-ready datasets,
Excel-compatible exports a small committed demo bundle and append-only action/outcome evidence.

Excluded: confidential employer data, live POS/payroll integrations, native
Tableau authoring/publication, legally compliant roster construction, employee
scheduling, production authentication, causal proof and verified external hosting. Deployment configuration is prepared.

## Stakeholder needs (fictional)

| Role | Decision and information need | Proposed responsibility |
|---|---|---|
| Area Manager | Which stores need intervention and what to trial? | Review weekly attention queue and coordinate pilots |
| Restaurant Manager | Which hours or preparation practices require attention? | Validate constraints, record overrides and service outcomes |
| Workforce Planner | What demand coverage fits the budget? | Confirm productivity, skill mix and roster feasibility |
| Finance Analyst | Do costs reconcile and is the opportunity economically meaningful? | Own definitions, cost treatment and benefit measurement |
| Marketing / Loyalty Manager | Do offers or retention tests improve contribution? | Design holdouts and avoid sales-only success criteria |
| Data Analyst | Are inputs complete, models credible and results reproducible? | Own contracts, audit, backtests and traceability |
| Executive sponsor | Is the initiative delivering useful decisions? | Proposed scope/priority owner; no actual sign-off claimed |

See the existing [stakeholder map](stakeholder_map.md) for role context.

## Functional requirements and user stories

| ID / priority | User story | Testable acceptance criteria |
|---|---|---|
| FR11 / Must | As an Area Manager, I want a scoped weekly queue so I can choose stores to investigate. | State/store filters scope additive totals; two complete seven-day windows; target allocation sums across month boundaries; CSV contains store and window keys. |
| FR12 / Must | As a Finance Analyst, I want a reconciled bridge so I can explain recorded profit changes. | Order-volume plus basket-value effects equal revenue change; six cost changes reconcile to profit change within AUD 0.01; missing order/mix budgets are disclosed. |
| FR13 / Must | As a Manager, I want scenario controls so I can assess a proposed action. | Zero-change scenario reproduces ledger; six drivers update outputs; sold ingredients and waste are counted once; invalid assumptions reject; non-positive unit contribution shows unavailable break-even. |
| FR14 / Must | As a Workforce Planner, I want hourly demand and coverage estimates so I can review the trade-off. | Only pre-origin data shapes mix/ATV; 11 local hours per forecast day; scheduled template distinguished from actual hours; productivity/utilisation changes affect suggestions; costs and full CSV export available. |
| FR15 / Must | As an Analyst, I want comparable forecasting evidence so I can defend planning choices. | Seasonal naive baseline, ridge and boosting evaluated chronologically; validation selects model; final holdout retained; store MAE/RMSE/WAPE and interval coverage shown. |
| FR16 / Must | As a Marketing Manager, I want promotion economics so I can choose a controlled trial. | Eligible location peers, net sales, all incremental variable/labour costs and campaign spend included; unavailable controls explicit; uncertainty/confounding visible; truth isolated for evaluation. |
| FR17 / Must | As a Loyalty Manager, I want eligible cohort and segment results so I can target experiments. | Full follow-up denominator; anonymous visits excluded; snapshot period labelled; company-wide behaviour table does not pretend to respond to store filters. |
| FR18 / Must | As an Analyst, I want quality monitoring so I can investigate rejected or repaired records. | Schema/key/date/category/money checks; whole-order quarantine; rule and missing-value counts; source hashes and stable IDs; audit scope shown in demo mode. |
| FR19 / Must | As an Area Manager, I want an evidence-backed brief so I can assign measurable actions. | Current/prior windows, supporting metrics, conditional component opportunity, proposed owner and measure exported for each store; no claimed realised savings. |
| FR20 / Should | As a recruiter, I want a portable demonstration so I can verify the project quickly. | App works from committed demo without raw ledger; reproducible setup; real screenshots; five-minute script; honest limitations and actual validation record. |

## Non-functional requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR01 | Local operation, no paid services or confidential data | Loopback server configuration; fictional disclosure; no external integration |
| NFR02 | Reproducible analytical decisions | Fixed seed/configuration, package lock, deterministic calculations, chronological selection |
| NFR03 | Auditable financial semantics | Explicit fact grains, source hashes, independent SQL and reconciliation tests |
| NFR04 | Useful presentation | Dark RESTOPS theme, readable units, scoped filters, metric definitions, downloads |
| NFR05 | Fail visibly on unsupported inputs | Missing schema/keys and invalid money fail; missing comparisons show unavailable; no blanket zero fills |
| NFR06 | Portable demonstration | 92-day aggregate demo plus fixed-snapshot customer, promotion and forecast evidence; raw datasets ignored by Git |
| NFR07 | Maintainability | Pure scenario/planning/bridge modules; thin presentation layer; tests and CI workflow |

No latency or accessibility certification is claimed. Visual browser checks and
Streamlit workflow tests establish the recorded local behaviour only.

## Measurement approach

Use one primary commercial outcome plus service guardrails. For a roster pilot,
compare labour cost and peak coverage with a comparable or randomised control,
record demand differences and monitor satisfaction. For a preparation pilot,
track waste cost together with stock-outs. For a promotion, evaluate incremental
contribution after discount and campaign costs. Record baseline, owner, dates,
intervention and overrides before measuring outcomes. The tracker records explicitly simulated or unverified user-entered observations and review notes; it does not claim an executed real pilot.

Related delivery artefacts: [process maps](process_maps.md),
[traceability matrix](requirements_traceability.md), [backlog](backlog.md),
[UAT scenarios](uat_scenarios.md), [decision log](decision_log.md),
[scenario and labour methods](decision_support_methodology.md),
[interview walkthrough](demo_script.md).

## Decision workflow extension

| ID / priority | User story | Testable acceptance criteria |
|---|---|---|
| FR21 / Must | As an Area Manager, I want to save an investigation/scenario as an action. | Selected restaurant/month, reconciled baseline, source fingerprint and six assumptions are frozen; UUID stable after reopen; default state proposed; no outcomes created. |
| FR22 / Must | As a pilot owner, I want a measurable versioned plan. | Required problem/evidence/intervention/fictional owner, valid pilot/measurement dates, primary metric threshold, service guardrails, comparison and impact basis; revisions append; revised approved/in-progress actions return to proposed. |
| FR23 / Must | As a reviewer, I want classified outcomes and controlled status transitions. | proposed→approved→in progress→completed; cancellation terminal; completion requires latest full-window review; simulated and user-entered observed input distinct; thresholds/guardrails separately assessed; no causal/guaranteed savings claim. |
| FR24 / Must | As a public visitor, I want an isolated synthetic demo. | Public wrapper overrides local mode; ignores local data/database paths; sessions share no writable database; seeded example has no approval/outcomes; local mode persists separately. |
| FR25 / Should | As a Tableau analyst, I want an exact native build handoff. | ZIP has 13 sources, manifest/keys/checks and four-page sheet/calculation instructions; native workbook remains not verified until manual authoring and acceptance. |
| FR26 / Should | As a recruiter, I want a short evidence-backed introduction. | README opens with problem/three capabilities/actual screenshot, quick start, decision case, scripts and disclosure; internal links/assets checked. |

NFR08: append-only evidence and stale-write protection, verified with SQL trigger,
reopen, revision and transition tests. NFR09: public defaults fail closed; no
shared disk state or source overrides, verified across independent sessions.
See [action model](action_tracker.md), [deployment boundary](deployment.md),
[current validation](upgrade_validation.md) and [contribution/design choices](design_choices.md).
