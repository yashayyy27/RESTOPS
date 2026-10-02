# Contribution, design choices and AI-assisted development

**Portfolio owner:** Yash Hurdale. The case connects Master of Business Analytics,
Bachelor of Data Science and Assistant Restaurant Manager experience. Practical
restaurant experience informs the questions; no employer process, data or outcomes
are represented. The code and documentation were developed with AI assistance.

The defensible contribution is a decision-oriented project scope: explain the
business problem, choose meaningful measures, challenge assumptions, connect
requirements to testable outputs, and present a proposed intervention with a
measurement plan. The repository records implemented choices and developer
verification; it cannot establish who independently authored every line or prove
understanding through commit labels. Do not claim sole unaided implementation.

| Choice | Reason and implementation | Trade-off |
|---|---|---|
| Streamlit + Pandas for the demonstration | Fast filtered analytics, actual controls/exports and AppTest coverage; nine computed views | Single-user/local semantics; no production access controls |
| Separate fact grains | Aggregate complete orders, labour, waste, finance independently; product and campaign facts separate | More explicit preparation instead of one easy but inflated join |
| Accounting identity before models | Absolute-cent profit bridge; discounts and waste counted once | Bridge explains accounting movement, not operational causation |
| Six explicit scenario assumptions | Hours/wages multiply; demand independent; fixed overhead/campaign spend; transparent break-even | No hidden price elasticity, capacity optimisation or service effects |
| Simple models must improve a decision | Weekly naive baseline challenged by Ridge/boosting; chronological validation selects four-week planning model | Synthetic training mechanisms limit external applicability |
| Append-only SQLite action evidence | Frozen baseline/source hash, immutable revisions/events/outcomes, stale-write protection and measured-review gate | Local portfolio database; no automatic migration or administrator-proof audit |
| Per-session public memory | Public wrapper forces synthetic demo; database/data overrides ignored; no shared writes | Edits intentionally disappear after session reset |
| Conservative outcomes | Only explicitly classified input; simulated versus user-entered observed; thresholds/guardrails separately evaluated | Does not verify provenance or estimate causal treatment impact |
| Small public dependencies | Runtime uses Pandas/NumPy/Plotly/Streamlit; forecasting results already exported; compatibility protobuf pin | Full analytical reproduction has a separate, larger lock |
| Honest Tableau handoff | Verified 13-source build ZIP, exact sheets/calculations and pending native checklist | Native workbook/manual validation still required |

AI assisted code generation, refactoring, documentation and test execution. Use
[actual validation](upgrade_validation.md) to describe what was checked. Proposed
stakeholders, fictional approvals in practice, and simulated observations are not
interviews, human UAT or demonstrated operational benefits.
