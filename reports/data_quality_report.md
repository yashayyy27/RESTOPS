# Data quality report

Generated from rule checks; the cleaning pipeline does not use hidden generation truth.

Retained **794,925 complete orders** and **2,105,626 lines**. Quarantined 2,049 complete orders to avoid partial baskets.

| Table | Rule | Rows | Action |
|---|---|---:|---|
| transactions | Exact duplicate records | 2,300 | Removed |
| labour | Exact duplicate records | 180 | Removed |
| customer_feedback | Exact duplicate records | 100 | Removed |
| products | Category aliases | 2 | Mapped to canonical categories |
| products | Category inconsistent with approved menu taxonomy | 2 | Corrected using checked-in business reference |
| transactions | Store name inconsistent with restaurant_id | 2,600 | Replaced from restaurant master |
| transactions | Invalid product foreign key | 800 | Quarantine complete affected order |
| transactions | Invalid timestamp | 650 | Quarantine complete affected order |
| transactions | Invalid quantity | 350 | Quarantine complete affected order |
| transactions | Invalid monetary values | 250 | Quarantine complete affected order |
| transactions | Revenue reconciliation | 250 | Quarantine complete affected order |
| transactions | GST reconciliation | 250 | Quarantine complete affected order |
| transactions | Complete-order quarantine (including companion lines) | 5,976 | Excluded from financial and order KPIs |
| customer_feedback | Invalid satisfaction score | 50 | Set null; retained survey |
| customer_feedback | Order quarantined | 181 | Order link set null |
| delivery | Order quarantined | 439 | Linked event excluded |
| loyalty | Order quarantined | 1,384 | Linked event excluded |
| labour | Paid hours inconsistent with shift duration and break | 60 | Recomputed from actual timestamps |
| labour | Missing hourly cost | 130 | Median of same role/weekend/holiday class; flagged |
| waste | Negative waste quantities | 70 | Quarantined; not silently converted to zero |

Counts can overlap across rules. The final quarantine row is the union, including companion lines. Raw exports remain unchanged. Null customer IDs represent anonymous orders, not errors. Missing survey answers remain null. Lost-order surveys remain in store satisfaction but are excluded from matched order analyses.

Labour-rate inference is appropriate only for this synthetic roster's known rate classes. A production system would require an authoritative payroll rate table.
