# UAT scenarios

Fictional users and scenarios. Actual execution in this repository is developer
automation and agent browser verification. No restaurant manager or stakeholder
has accepted the system. See [actual validation results](validation_results.md).

| ID | Proposed user / scenario | Steps | Expected result |
|---|---|---|---|
| UAT01 | Area Manager scopes a review | Select Demo, NSW and reporting month December 2025; open Executive overview | Only selected stores contribute; weekly window and target allocation are explicit; downloadable queue matches display |
| UAT02 | Finance investigates Wollongong | Select Restaurant investigation and Wollongong; inspect December vs November | Volume + basket change equals revenue change; all six cost movements reconcile to profit; product mix and discount detail do not double-count bridge effects |
| UAT03 | Manager compares a scenario | Keep all changes zero; then adjust hours, prices, demand, discount and waste | Baseline preserved at zero change; drivers update costs/results; break-even and demand ranges explicit; export retains assumptions |
| UAT04 | Workforce Planner reviews coverage | Open Labour planning; raise productivity and compare suggested hours; lower schedule template to 0% | Suggested coverage responds; zero template is preserved; under-coverage visible; forecast origin, capacity and costs labelled |
| UAT05 | Analyst challenges model | Select Forecasting and a restaurant; compare selected model with seasonal naive | Store-level MAE/RMSE/WAPE and coverage shown; validation selection separate from holdout; future bands visible |
| UAT06 | Marketing reviews campaign | Select Promotion evaluation and a campaign, then one without eligible controls | Valid campaign shows sales/contribution/ROI/range; unavailable campaign shows no fabricated estimate; truth validation is separate |
| UAT07 | Loyalty Manager interprets cohorts | Open Customer & loyalty and change restaurant selection | Scoped cohort denominator changes; incomplete follow-up excluded; company-wide behaviour table retains explicit global scope |
| UAT08 | Analyst audits trust | Open Data quality; inspect missing values and quarantine; verify mutation tests | Optional nulls retained; required/schema/key/date/money defects fail; complete basket quarantine and audit scope visible |
| UAT09 | Area Manager assigns action | Review a weekly brief entry and export it | Contains current/prior evidence, conditional impact basis, proposed owner, success measure and stable store/window keys |
| UAT10 | Recruiter runs demo | Clone, install demo dependencies, run public entry point without generating raw data | Committed demo supports all nine workflows; full generation remains available; real screenshots and five-minute script match working features |

Production UAT would also need manager validation of service rates, award and
shift constraints, business calendar targets, source completeness and workflow
fit. These are future tests, not claimed results.

## Proposed action/public acceptance scenarios

| ID | Fictional role | Scenario | Acceptance criterion |
|---|---|---|---|
| UAT11 | Area Manager | From December Wollongong investigation, evaluate −1% hours/4% waste and save action | Frozen selected ledger and exact assumptions; proposal only; UUID/export includes period/source |
| UAT12 | Finance Analyst | Revise scenario/plan, attempt invalid dates and stale edit | Original immutable; new revision appended; invalid inputs rejected; revised approval returns to proposed |
| UAT13 | Pilot reviewer | Enter labelled simulated result passing labour target but failing satisfaction; then review full window | Commercial/service results separate; no achieved/causal claim; latest full-window review required for completion |
| UAT14 | Public visitor | Try local overrides; practise action in session A and open independent B | Committed data forced; no shared disk DB; B sees only seeded proposal, no A edits; local mode separately persists |
| UAT15 | Tableau analyst | Build actual four-page workbook from ZIP and reconcile cards | Native sheets, filters, ratios and acceptance reference verified manually; remains NOT VERIFIED until run |
| UAT16 | Recruiter | Follow two-minute script and evidence links | Current screens match script; setup works; disclosures visible; no broken links/assets |

Actual developer evidence is recorded in [upgrade validation](upgrade_validation.md).
These are proposed human acceptance scenarios, not fabricated human testing.
