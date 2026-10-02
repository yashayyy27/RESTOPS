# Ten implementation-grounded interview questions

1. **What business problem does RESTOPS solve?** An Area Manager needs to move
   from a missed target to a feasible measured decision. Show the attention queue,
   exact investigation, scenario snapshot and action success/guardrail plan.
   Financial outcomes remain conditional, not demonstrated employer benefits.
2. **What was your contribution, and where did AI help?** Connect restaurant
   management questions to BA scope, definitions, hypotheses, acceptance evidence
   and interpretation. Be explicit that AI assisted code/docs/checks. Do not
   claim unaided authorship, interviews or manager approval. See design_choices.md.
3. **How did you prevent inflated revenue and costs?** Orders differ from lines.
   Independent store/date aggregates precede combination; product/campaign/customer
   facts keep their grains. Show SQL/Python reconciliation and complete-key checks.
4. **How do you explain profit change?** `management.profit_bridge` decomposes
   volume and net basket with interaction allocated to basket, plus six cost
   changes. Absolute tolerance is A$0.01 at all scales. Mix/discount context is
   not added again to the bridge. It does not prove why an operational change occurred.
5. **Why isn't the scenario a forecast?** `scenarios.simulate` applies six explicit
   drivers to one frozen calendar-month ledger. Wages/hours multiply; discounts
   enter net sales once; waste is additional food COGS. No automatic elasticity or
   staffing/service response exists. Sensitivity is assumption-based, not a probability.
6. **How did you avoid forecast leakage?** Cut off history inside predict_from_origin;
   train lags use prior values; future lags use recursive predictions. Three rolling
   validation windows select model; final holdout reports MAE/RMSE/WAPE/coverage.
   Future-actual mutation tests must leave predictions unchanged. Bands are approximate.
7. **Can you claim promotion ROI is causal?** No. Unpromoted location peers adjust
   a same-weekday baseline; contaminated controls are excluded; costs/spend enter
   contribution once. Missing controls mean no estimate. Bootstrap limitations and
   confounders remain; generator truth is accessed after estimation only.
8. **What makes the tracker auditable?** UUID action; immutable baseline/source
   hash; append-only plan/scenario revisions; status events; outcomes bound to the
   measured revision. Revision resets approval; full-window review gates completion.
   Simulated and unverified user-entered outcomes remain labelled. SQLite triggers
   do not make records tamper-proof against an administrator.
9. **What does acceptance testing prove?** AppTest, pure-calculation regressions,
   local reopen, two-session isolation, export read-back and link tests validate
   implemented behaviour. Fictional user stories map to these tests. They are
   developer evidence, not interviews or real-manager UAT. Point to actual check results.
10. **What would you do before real-world use?** Validate source completeness,
    awards/skills/availability and service productivity with managers; select a
    controlled intervention and comparison; collect operational outcomes; test
    affordability and service guardrails. Add access controls/production monitoring
    and verify the native Tableau workbook. Do not call proposed work completed.
