# Native Tableau acceptance record — pending manual authoring

All native checks below are **NOT VERIFIED**. The ZIP manifest separately
records verified source-file checks. Replace status only after running the check
in a real workbook; record workbook version, date, tester and actual values.

| Check | Expected result | Native status |
|---|---|---|
| Four pages open with data | Executive, Operations, Customers, Forecasting | NOT VERIFIED |
| Wollongong / Dec 2025 finance | Exact revenue, profit, orders and ratios in manifest.acceptance_reference | NOT VERIFIED |
| Historical chain totals | Monthly sums = grouped daily ledger; ZIP checks pass | NOT VERIFIED |
| Grain/relationships | Unique complete keys; each fact separate; dimension many-to-one | NOT VERIFIED |
| Store action changes all scoped sheets | pRestaurant transferred; customer/campaign periods unchanged | NOT VERIFIED |
| Month selection | Only history/product fields change; no silent customer/campaign/forecast truncation | NOT VERIFIED |
| Campaign without controls | ROI and contribution unavailable; spend excluded from eligible ROI denominator | NOT VERIFIED |
| Forecast metrics | Holdout per-model errors equal CSV actual/predicted computations | NOT VERIFIED |
| Forecast uncertainty | Bands displayed only at one store; no chain interval sum | NOT VERIFIED |
| Monetary/percentage/null formats | AUD excluding GST; ratios 0–1; undefined remains null | NOT VERIFIED |
| Screenshots and workbook export | Four real screenshots + actual saved .twb/.twbx | NOT VERIFIED |
| Publication | Only after approval; verify public URL | NOT VERIFIED |
