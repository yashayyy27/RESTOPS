# Recruiter workflow upgrade — actual developer evidence

**2 October 2026.** This is developer automation and agent browser verification,
not real-manager UAT, stakeholder approval or measured operational benefit.
Completed local check counts are recorded below. Earlier
publication CI remains [separately recorded](validation_results.md).

## Audit findings and disposition

| Finding | Change / regression evidence | Status |
|---|---|---|
| Large-value bridges used relative tolerance despite a cent claim | Profit bridge uses rtol=0; large-value A$0.05 error rejected | PASS |
| SQL inner join could hide unmatched store/months; relative tolerance too loose | Outer key coverage + absolute A$0.01; missing-key/drift fixtures reject | PASS |
| Scenario/investigation had no saved intervention/outcome evidence | Frozen action/source; scenario/plan revisions; statuses; measured-review gate; local reopen and trigger tests | PASS |
| Public Auto could read local data and lacked persistence boundary | Forced committed demo and per-session memory; conflicting overrides and independent sessions tested | PASS |
| Unused forecasting import enlarged demo runtime dependencies | Removed unused UI import; small demo dependency set installed in fresh venv | PASS |
| Focus clearing and filter changes needed safe handling | Empty focus handled; state/focus/empty restaurant/register checks | PASS |
| Offline audit download broke in a clean clone | Point to committed gzip audit and fix report generator; clean-copy link check | PASS |
| Long recruiter introduction and absent end-to-end action script | Short README, current screenshot, decision case, 2/5-minute guides and Q&A | PASS for artifact checks; recruiter/human comprehension NOT VERIFIED |
| Tableau native deliverable absent | Verified ZIP with 13 sources and 36 data checks; exact build sheets/calculations and pending native checklist | Data bundle PASS; native workbook NOT VERIFIED |
| Public deployment absent | Public-only entry point, small adjacent requirements and deployment recipe; real local server/browser | Local runtime PASS; hosted URL / Docker NOT VERIFIED |

## Validation scope

Baseline inspection: existing 39 tests passed before changes. The full source
validation was rerun after strengthening reconciliation: **97 checks passed**.
Source manifests and raw/full datasets remain local and ignored by Git.
The committed demo and analytic findings are retained; synthetic generation/model
mechanisms were not changed, and no tracker outcomes were manufactured.

Portable installation was performed in a new Python 3.12 virtual environment
with demo requirements plus test formatter. `pip check` reported no broken
requirements. The entry-point server started on loopback port 8502 using that
environment. Real browser verification followed Start here → Wollongong →
scenario (−1% hours, 4% waste) → save proposed action. It displayed baseline
A$2,992, scenario A$4,152, delta A$1,160; these are rounded conditional numbers.
Current screenshots are in `docs/screenshots/`; the normal browser viewport is
775×804, without mocked output or Tableau screenshots.

Local SQLite reopen, append-only triggers, schema rejection, date/finite-value
validation, stale edits, revision reapproval, status transitions, classification,
full-window review and guardrail failure are tested. Public isolation is tested
at data path, SQLite-store and independent AppTest session levels. Observed input
is user-entered and unverified; no input provenance or causal effect is certified.

Financial checks cover zero-change equality across all 54 portable store/months,
cent-exact bridges, independent SQL, complete keys, forecast chronological isolation,
model selection and per-store export accuracy. Excel OOXML read-back compares
weekly revenues with the decision ledger. Tableau ZIP hashes/keys/grains and
financial identities are verified independently of native authoring.

## Final automated run record

| Completed check | Actual result |
|---|---|
| Full suite, Python 3.12.14 | **66 tests**, 20.615 seconds; zero failures/errors/skips |
| Fresh demo venv + Git-visible clean copy | **51 tests**, 5.996 seconds; zero failures/errors/skips; no raw sources or full marts |
| Source quality / financial validation | **97 checks passed** |
| Tableau build bundle | **13 sources / 36 data checks passed**; ZIP read-back/hash tests passed |
| Dependency consistency | Fresh demo environment: `pip check` passed, including protobuf 5.29.6 compatibility pin |
| Black and Python compilation | Passed; 41 files unchanged and compilation checked |
| Current hosted deployment / native Tableau / Docker | **NOT VERIFIED** |

Portable-test process peak RSS was **348.1 MiB** on macOS 26.3 / arm64. This
includes independent AppTest sessions; it is not server steady-state memory,
cloud capacity or multi-user load evidence. The [machine-readable record](../reports/upgrade_validation.json)
retains test counts and scope. The first clean-copy attempt exposed the audit
link defect; the corrected fresh copy passed. Nothing is inferred from CI
configuration alone. Current upgrade publication CI is pending publication.

## Not verified or remaining manual work

- Real-manager acceptance, stakeholder sign-off and actual intervention/benefit measurement.
- Public hosting: user approval and hosting-account access are required; no live URL exists.
- Docker build/runtime: Docker is unavailable here; direct Python server was checked.
- Native Tableau: author/save workbook, run the provided acceptance checklist and capture actual screenshots.
- Production authentication, shared-user access controls, award-compliant scheduling and live source integration.
- Multi-user cloud memory/capacity/load testing, accessibility certification and administrator-proof audit guarantees.
