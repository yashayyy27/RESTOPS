# Design decision log

| ID | Decision | Reason and trade-off |
|---|---|---|
| D01 | Extend existing Pandas / SQLite marts | Preserve working notebooks, SQL checks and financial semantics; avoid duplicate metric implementations |
| D02 | Pure scenario, planning and management modules | Make critical business logic independently testable; Streamlit is a thin presentation layer |
| D03 | Local Streamlit with committed aggregate demo | Fast recruiter demonstration with no paid services or confidential data; demo cannot independently re-audit absent raw facts |
| D04 | Reporting month for finance; explicit other view scopes | Campaign windows, fixed customer snapshots and forecast origins must not be silently truncated by a finance filter |
| D05 | Exact volume/basket decomposition followed by six cost changes | Reconciles to observed profit; product mix and discount relationships are supporting detail, not extra additive bridge components |
| D06 | Treat chosen labour as fixed within break-even period | A clear conditional break-even calculation; step costs, elasticity and service/demand feedback are not modelled |
| D07 | Disaggregate daily revenue using pre-origin weekday ATV and hourly mix | Connect evaluated forecasts to an understandable operational plan; historical basket/mix stability is a material assumption |
| D08 | Distinguish scheduled template, actual support hours and suggested coverage | Future roster has not been supplied; repeating historical schedule is a comparison template, not an approved future roster |
| D09 | Retain validation-selected chain model, show store results | Avoid holdout selection and leakage; some restaurants can perform worse than the naive baseline |
| D10 | Calibrate empirical bands using 84 validation errors per store | More relevant store-level scale than pooled dollar bands; horizon shape and probability guarantees remain limited |
| D11 | Isolate generator treatment truth after estimation | Validate promotion order-uplift error without leaking hidden mechanisms; expected mean effect is not realised causal contribution |
| D12 | Keep current/prior weekly opportunity formula explicit | Supports a measurable pilot; estimated component opportunities are not committed or additive savings |
| D13 | Preserve curated README during rebuild | Rebuild dynamic evidence in a separate generated summary; protect interview documentation and actual screenshots |
| D14 | Retain motorsport-inspired RESTOPS palette without employer branding | Consistent visual identity requested by the user; no Nando's data, branding or confidential operational formula |
| D15 | Excel-compatible current-selection CSVs and prepared workbook snapshot | Portable app exports retain filter/assumption fidelity; the prepared XLSX is explicitly a snapshot and does not claim to recalculate with app sliders |

| D16 | Exclude unavailable promotion estimates and their spend together from reported ROI | Align contribution and cost populations; preserve unavailable campaign metadata for investigation |
| D17 | Reset scenario assumptions when restaurant, month or data mode changes | Prevent assumptions attached to one observed baseline from silently applying to another |

This log records implementation decisions, not stakeholder approvals.
