# Requirements traceability matrix

Requirements are fictional case-study needs. Automated and agent validation is
recorded in [validation results](validation_results.md); it is not stakeholder UAT.

| Business need | Requirement | Implementation / data | Verification | UAT scenario |
|---|---|---|---|---|
| BR01, BR09 · restaurant attention | FR11 | `management.weekly_scorecard`, Executive overview | complete-window and target-allocation tests; app filters | UAT01 |
| BR01 · explain profit | FR12 | `management.profit_bridge`, Restaurant investigation; store-day / product-month / waste-detail | exact revenue and profit bridge tests; ledger SQL | UAT02 |
| Commercial impact | FR13 | `scenarios.simulate`, `compare`, `sensitivity`; Profit scenario simulator | identity, discount, labour, waste, break-even and sensitivity tests | UAT03 |
| BR02, BR08 · forward labour | FR14 | `planning.hourly_plan`, scheduled-hour allocations; Labour & demand planning | scheduled-hour reconciliation, pre-origin isolation, hourly demand totals; app productivity control | UAT04 |
| BR08 · credible forecast | FR15 | `forecasting.predict_from_origin`; Forecasting and store metrics | chronological selection, lag and future-actual isolation; per-store baseline comparison | UAT05 |
| BR06 · promotion economics | FR16 | `analysis.promotion_analysis`; Promotion evaluation; isolated validation truth | contribution identity, control contamination test; unavailable controls | UAT06 |
| BR05, BR07 · customer decisions | FR17 | customer RFM / cohorts; Customer & loyalty | full 90-day eligibility and denominators; snapshot labels | UAT07 |
| BR10 · trustworthy inputs | FR18, NFR03, NFR05 | `validation.contract_checks`, cleaning, SQLite, hashes; Data quality | deliberate schema/null/key/money/date mutations; complete-order quarantine; financial and FK checks | UAT08 |
| BR09 · weekly decisions | FR19 | `management.weekly_brief`; weekly CSV / Markdown | opportunity formula and trace fields checked | UAT09 |
| BR10 · reproduce and present | FR20, NFR02, NFR06, NFR07 | demo bundle, app tests, package lock, CI, demo script | full pipeline run plus demo-only app workflows and screenshots | UAT10 |

Existing FR01–FR10 remain documented in [business requirements](business_requirements.md).
The [data dictionary](data_dictionary.md), [KPI definitions](kpi_definitions.md)
and [Tableau catalogue](tableau_catalog.json) establish the data/metric contracts.

## Decision workflow and public demonstration

| Business need | Requirement | Implementation / data | Verification | UAT |
|---|---|---|---|---|
| Carry investigation into action | FR21 | action_views.prepare_action; actions.create; actions/revisions | test_public guided workflow; test_actions snapshot, UUID/reopen | UAT11 |
| Define success and preserve revisions | FR22, NFR08 | validate_plan; revise; immutable SQLite triggers | required fields/dates/finite values; frozen original; stale revision; reapproval | UAT12 |
| Measure without inventing benefits | FR23 | observe/review_outcome; append-only events/outcomes | classifications, guardrail failure, full-window completion gate and outcome revision | UAT13 |
| Safe public demonstration | FR24, NFR09 | runtime/app_data/public wrapper; session memory | conflicting overrides; two-session isolation; local reopen | UAT14 |
| Honest Tableau completion | FR25 | tableau_bundle + build instructions | 36 data checks; hash/key/financial tests; native workbook pending | UAT15 |
| Recruiter comprehension | FR26 | README, 2/5-minute scripts, design choices/Q&A | current browser screenshots and automated internal link/asset checks | UAT16 |

These extension requirements are detailed in the [BA pack](ba_delivery_pack.md).
Automated checks are developer evidence; fictional UAT remains proposed for humans.
