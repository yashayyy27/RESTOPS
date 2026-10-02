# Current-state and future-state processes

These processes and roles are fictional design assumptions. They do not describe
observed employer processes or validated stakeholder interviews.

## Current state

```mermaid
flowchart TD
    POS[POS exports] --> Manual[Analyst reconciles spreadsheets manually]
    Roster[Roster and payroll exports] --> Manual
    Finance[Costs and targets] --> Manual
    Guest[Surveys and loyalty activity] --> Manual
    Manual --> Revenue[Area Manager compares revenue headlines]
    Revenue --> Guess[Discuss possible explanations without consistent definitions]
    Guess --> Change[Restaurant Manager adjusts operations]
    Change --> Review[Limited baseline and outcome measurement]
    Review --> Manual
```

Problems: mismatched grains, repeated costs, missing records, unclear definitions,
unmeasured actions and a focus on revenue rather than contribution.

## Future state implemented for analysis

```mermaid
flowchart TD
    Export[Synthetic source exports] --> Validate[Analyst validates contracts and relationships]
    Validate --> Gate{Valid or recoverable?}
    Gate -->|Recoverable| Repair[Apply documented business rules and record audit]
    Gate -->|Invalid basket| Reject[Quarantine whole order and linked events]
    Gate -->|Valid| Marts[Aggregate separate facts into explicit-grain marts]
    Repair --> Marts
    Reject --> Audit[Quality monitoring and source investigation]
    Marts --> Reconcile[Finance: reconcile ledger and independent SQL]
    Reconcile --> Queue[Area Manager: review weekly queue and targets]
    Queue --> Diagnose[Investigate volume, basket, mix, discounts and costs]
    Diagnose --> Estimate[Forecast demand and compare operating scenarios]
    Estimate --> Pilot[Proposed manager pilot with owner and success measure]
    Pilot -. Future operational work .-> Measure[Record intervention and measure against control]
    Measure -. Future operational work .-> Queue
```

The solid path is delivered analysis. Dashed steps are proposed operational work;
the repository does not invent approvals, executed interventions or benefits.
