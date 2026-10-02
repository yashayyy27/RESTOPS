"""Action proposal, append-only revisions and labelled outcome review UI."""

from dataclasses import asdict
from datetime import date
import hashlib
import json
import math

import pandas as pd
import streamlit as st

from .actions import (
    ActionStore,
    METRICS,
    TRANSITIONS,
    default_plan,
    review_outcome,
    seed_example,
)
from .runtime import action_path, app_mode
from .scenarios import Scenario, simulate


def navigate(view):
    st.session_state["view"] = view


def prepare_action(sid, name, month, baseline, assumptions, rows, origin):
    """Called from investigation/scenario after the current ledger is calculated."""
    b = {key: float(value) for key, value in baseline.items() if math.isfinite(value)}
    st.session_state["action_draft"] = {
        "restaurant_id": sid,
        "restaurant_name": name,
        "period": month,
        "baseline": b,
        "assumptions": asdict(assumptions),
        "source": {
            "data_kind": "synthetic_history",
            "grain": "restaurant/calendar month",
            "dataset": "store_day",
            "period": month,
            "view": origin,
            "fingerprint": hashlib.sha256(
                rows.sort_values("business_date").to_csv(index=False).encode()
            ).hexdigest(),
        },
    }
    navigate("Action & experiment tracker")


def action_store(frames):
    mode = app_mode()
    path = action_path(mode)
    context = (mode, path)
    if st.session_state.get("action_store_context") != context:
        old = st.session_state.get("action_store")
        if old:
            old.close()
        st.session_state["action_store"] = ActionStore(path)
        st.session_state["action_store_context"] = context
        seed_example(st.session_state["action_store"], frames)
    return st.session_state["action_store"]


def plan_fields(plan, prefix):
    """Shared creation/revision form, with explicit rate units and date grain."""
    p = dict(plan)
    for key, label in [
        ("problem", "Problem"),
        ("evidence", "Supporting evidence"),
        ("intervention", "Proposed intervention"),
        ("owner", "Fictional owner"),
    ]:
        p[key] = st.text_area(label, value=plan[key], key=f"{prefix}_{key}")
    cols = st.columns(2)
    for index, (key, label) in enumerate(
        [
            ("start_date", "Pilot start"),
            ("end_date", "Pilot end"),
            ("measurement_start", "Measurement start"),
            ("measurement_end", "Measurement end"),
        ]
    ):
        p[key] = (
            cols[index % 2]
            .date_input(
                label, value=date.fromisoformat(plan[key]), key=f"{prefix}_{key}"
            )
            .isoformat()
        )
    p["primary_metric"] = st.selectbox(
        "Primary success metric",
        list(METRICS),
        index=list(METRICS).index(plan["primary_metric"]),
        key=f"{prefix}_metric",
    )
    st.caption(
        "Rate targets use fractions (0.40 = 40%); satisfaction uses 1–5. Currency targets refer to the measurement-window total; match duration before comparing baseline amounts."
    )
    p["target"] = st.number_input(
        "Success threshold (metric units)",
        value=float(plan["target"]),
        format="%.4f",
        key=f"{prefix}_target",
    )
    cols = st.columns(2)
    p["satisfaction_min"] = cols[0].number_input(
        "Minimum satisfaction (1–5)",
        1.0,
        5.0,
        float(plan["satisfaction_min"]),
        key=f"{prefix}_satisfaction",
    )
    p["late_delivery_max"] = cols[1].number_input(
        "Maximum late-delivery fraction",
        0.0,
        1.0,
        float(plan["late_delivery_max"]),
        format="%.3f",
        key=f"{prefix}_late",
    )
    for key, label in [
        ("comparison_approach", "Comparison approach and confounders"),
        ("expected_impact_basis", "Expected impact basis and overlap limitations"),
    ]:
        p[key] = st.text_area(label, value=plan[key], key=f"{prefix}_{key}")
    return p


def proposal_defaults(draft):
    p = default_plan(draft["baseline"])
    p["problem"] = (
        f"Investigate {draft['restaurant_name']} performance in {draft['period']}."
    )
    b = draft["baseline"]
    p["evidence"] = (
        f"Synthetic {draft['period']} ledger: revenue AUD {b['revenue']:,.2f}; operating profit AUD {b['operating_profit']:,.2f}; labour share {b['labour_cost_pct']:.1%}. Source: {draft['source']['dataset']} / {draft['source']['view']}."
    )
    p["intervention"] = (
        "Trial the saved operating assumptions; confirm capacity and preserve peak service before approval."
    )
    future = pd.Period(draft["period"]) + 1
    for key in ("start_date", "measurement_start"):
        p[key] = future.start_time.date().isoformat()
    for key in ("end_date", "measurement_end"):
        p[key] = future.end_time.date().isoformat()
    result = simulate(b, Scenario(**draft["assumptions"]))
    p["target"] = result["labour_cost"] / result["revenue"]
    return p


def action_markdown(action):
    revision = action["revisions"][-1]
    plan = revision["plan"]
    delta = (
        revision["estimate"]["operating_profit"]
        - action["baseline"]["operating_profit"]
    )
    return f"""# RESTOPS action {action['action_id']}

Fictional case study · {action['restaurant_name']} · frozen baseline {action['period']}
User-recorded status: {action['status']} · latest revision {revision['revision']}

**Problem:** {plan['problem']}

**Evidence:** {plan['evidence']}

**Intervention:** {plan['intervention']}

**Fictional owner:** {plan['owner']}

**Dates:** {plan['start_date']}–{plan['end_date']}; measurement {plan['measurement_start']}–{plan['measurement_end']}

**Success:** {plan['primary_metric']} ({METRICS[plan['primary_metric']]} is better), threshold {plan['target']}; satisfaction ≥ {plan['satisfaction_min']}; late deliveries ≤ {plan['late_delivery_max']}

**Comparison:** {plan['comparison_approach']}

**Scenario estimate:** AUD {delta:,.2f} operating-profit change for the baseline duration.
{plan['expected_impact_basis']}

**Saved assumptions:** `{json.dumps(revision['assumptions'], sort_keys=True)}`

**Outcome records:** {len(action['outcomes'])}. Full observations, revisions and events are retained in the JSON export.

**Evidence fingerprint:** {action['source']['fingerprint']}

{action['interpretation']}
"""


def tracker(frames, meta, ids, month):
    st.write("Turn a restaurant investigation into a measurable proposed intervention.")
    if message := st.session_state.pop("action_message", None):
        st.success(message)
    public = app_mode() == "public"
    st.info(
        "Public demo: experimental edits stay in this browser session and disappear on session reset. No shared writable database."
        if public
        else "Local mode: append-only action evidence is saved in local SQLite. Keep exports fictional and free of employer or personal data."
    )
    st.caption(
        "Restaurant selection filters the register. Reporting-month selection does not rewrite saved baseline periods. Statuses are user-recorded fictional workflow states, not independently verified stakeholder approvals."
    )
    try:
        store = action_store(frames)
    except (ValueError, OSError) as exc:
        st.error(f"Action storage could not be validated: {exc}")
        return
    draft = st.session_state.get("action_draft")
    if draft:
        with st.expander(
            f"New proposal · {draft['restaurant_name']} · frozen {draft['period']}",
            expanded=True,
        ):
            st.caption(
                "This draft retains the exact selected baseline and six scenario inputs even if sidebar filters change. Saving records a proposal only."
            )
            prefix = (
                "create_"
                + hashlib.sha256(
                    json.dumps(draft, sort_keys=True).encode()
                ).hexdigest()[:16]
            )
            with st.form("create_action_form"):
                plan = plan_fields(proposal_defaults(draft), prefix)
                save = st.form_submit_button("Save proposed action", key="save_action")
            if save:
                try:
                    aid = store.create(
                        draft["restaurant_id"],
                        draft["restaurant_name"],
                        draft["period"],
                        draft["baseline"],
                        draft["assumptions"],
                        plan,
                        draft["source"],
                    )
                    st.session_state["selected_action_id"] = aid
                    st.session_state.pop("saved_action", None)
                    del st.session_state["action_draft"]
                    st.session_state["action_message"] = (
                        "Proposal saved; no approval or achieved savings recorded."
                    )
                    st.rerun()
                except (ValueError, TypeError) as exc:
                    st.error(str(exc))
    actions = store.list(ids)
    cols = st.columns(3)
    cols[0].metric("Saved proposals", len(actions))
    cols[1].metric(
        "In-progress actions", sum(a["status"] == "in progress" for a in actions)
    )
    cols[2].metric("Outcome records", sum(len(a["outcomes"]) for a in actions))
    summary = pd.DataFrame(
        [
            {
                "action_id": a["action_id"],
                "restaurant": a["restaurant_name"],
                "baseline_month": a["period"],
                "status": a["status"],
                "revision": a["revisions"][-1]["revision"],
                "owner": a["revisions"][-1]["plan"]["owner"],
                "scenario_profit_delta_aud": a["revisions"][-1]["estimate"][
                    "operating_profit"
                ]
                - a["baseline"]["operating_profit"],
                "impact_kind": "Conditional scenario estimate; not additive savings",
            }
            for a in actions
        ],
        columns=[
            "action_id",
            "restaurant",
            "baseline_month",
            "status",
            "revision",
            "owner",
            "scenario_profit_delta_aud",
            "impact_kind",
        ],
    )
    st.dataframe(summary, hide_index=True, width="stretch")
    if not actions:
        st.info(
            "No actions for selected restaurants. Prepare one from Restaurant investigation or Profit scenario simulator; the fictional Wollongong example is visible when Wollongong is selected."
        )
        return
    st.warning(
        "Overlapping staffing, waste and demand opportunities cannot be added as guaranteed savings. Review each complete scenario and its service trade-offs."
    )
    labels = {
        a["action_id"]: f"{a['restaurant_name']} · {a['period']} · {a['action_id'][:8]}"
        for a in actions
    }
    preferred = st.session_state.get("selected_action_id")
    options = list(labels)
    aid = st.selectbox(
        "Saved action",
        options,
        index=options.index(preferred) if preferred in options else 0,
        format_func=labels.get,
        key="saved_action",
    )
    action = store.get(aid)
    revision = action["revisions"][-1]
    plan = revision["plan"]
    st.subheader("Frozen decision evidence")
    st.markdown(
        f"**Problem:** {plan['problem']}\n\n**Evidence:** {plan['evidence']}\n\n**Intervention:** {plan['intervention']}\n\n**Fictional owner:** {plan['owner']}\n\n**Success:** {plan['primary_metric']} → {plan['target']:.4f} ({METRICS[plan['primary_metric']]} is better). **Service guardrails:** satisfaction ≥ {plan['satisfaction_min']}; late-delivery share ≤ {plan['late_delivery_max']:.1%}.\n\n**Measurement:** {plan['measurement_start']}–{plan['measurement_end']}\n\n**Comparison approach:** {plan['comparison_approach']}"
    )
    st.caption(
        f"Source {action['source']['dataset']} · baseline {action['period']} · immutable hash {action['snapshot_hash'][:16]} · revision {revision['revision']}. Expected impact: {plan['expected_impact_basis']}"
    )
    financial = pd.DataFrame(
        [
            {
                "metric": key,
                "synthetic_baseline": simulate(action["baseline"])[key],
                "scenario_estimate": revision["estimate"][key],
            }
            for key in (
                "revenue",
                "cogs",
                "labour_cost",
                "operating_contribution",
                "operating_profit",
                "operating_margin_pct",
            )
        ]
    )
    display = financial.copy()
    for key in ("synthetic_baseline", "scenario_estimate"):
        display[key] = display.apply(
            lambda row: (
                f"{row[key]:.1%}"
                if row.metric.endswith("_pct")
                else f"A${row[key]:,.0f}"
            ),
            axis=1,
        )
    st.dataframe(display, hide_index=True, width="stretch")
    st.json(revision["assumptions"], expanded=False)
    c1, c2 = st.columns(2)
    c1.download_button(
        "Download action summary Markdown",
        action_markdown(action),
        f"restops_action_{aid}.md",
        "text/markdown",
        key="action_md",
    )
    c2.download_button(
        "Download complete action evidence JSON",
        json.dumps(action, indent=2, allow_nan=False),
        f"restops_action_{aid}.json",
        "application/json",
        key="action_json",
    )
    allowed = TRANSITIONS[action["status"]]
    with st.expander(f"Workflow status · {action['status']}"):
        st.dataframe(pd.DataFrame(action["events"]), hide_index=True)
        if allowed:
            with st.form(f"status_{aid}"):
                status = st.selectbox(
                    "Next recorded status", allowed, key="next_status"
                )
                note = st.text_area(
                    "Status explanation / fictional approval basis", key="status_note"
                )
                update = st.form_submit_button(
                    "Record status transition", key="transition_action"
                )
            if update:
                try:
                    store.transition(aid, status, note, action["status"])
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.caption(
                "Terminal record; retain evidence and create a new proposal for a follow-up."
            )
    if action["status"] not in ("completed", "cancelled"):
        with st.expander("Append a plan / scenario revision"):
            prefix = f"rev_{aid}_{revision['revision']}"
            with st.form(f"revision_{aid}"):
                revised = plan_fields(plan, prefix)
                inputs = {}
                reference = simulate(action["baseline"])
                for key, value in revision["assumptions"].items():
                    inputs[key] = st.number_input(
                        f"Revised {key} (fraction)",
                        value=float(reference[key] if value is None else value),
                        format="%.4f",
                        key=f"{prefix}_{key}",
                    )
                reason = st.text_area("Reason for revision", key="revision_reason")
                update = st.form_submit_button("Append revision", key="revise_action")
            if update:
                try:
                    store.revise(aid, revised, inputs, reason, revision["revision"])
                    st.rerun()
                except (ValueError, TypeError) as exc:
                    st.error(str(exc))
    if action["status"] == "in progress":
        with st.expander("Record an outcome and review", expanded=True):
            with st.form(f"outcome_{aid}_{revision['revision']}"):
                kind = st.selectbox(
                    "Outcome classification",
                    ["simulated", "user_entered"],
                    format_func=lambda k: (
                        "Simulated outcome"
                        if k == "simulated"
                        else "Observed outcome entered by user (unverified)"
                    ),
                    key="outcome_kind",
                )
                left, right = st.columns(2)
                start = left.date_input(
                    "Observation start",
                    date.fromisoformat(plan["measurement_start"]),
                    key="outcome_start",
                )
                end = right.date_input(
                    "Observation end",
                    date.fromisoformat(plan["measurement_end"]),
                    key="outcome_end",
                )
                values = {}
                for key in sorted(
                    {plan["primary_metric"], "satisfaction_score", "late_delivery_pct"}
                ):
                    values[key] = st.number_input(
                        f"Recorded {key} (metric units)",
                        value=float(action["baseline"].get(key, 0)),
                        format="%.4f",
                        key=f"outcome_value_{key}",
                    )
                observation = st.text_area(
                    "Observations and input provenance", key="outcome_observation"
                )
                review = st.text_area(
                    "Review outcome, confounders and next decision",
                    key="outcome_review",
                )
                submit = st.form_submit_button(
                    "Record labelled outcome", key="record_outcome"
                )
            if submit:
                try:
                    store.observe(
                        aid,
                        kind,
                        start.isoformat(),
                        end.isoformat(),
                        values,
                        observation,
                        review,
                        revision["revision"],
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    st.subheader("Outcome measurement")
    if not action["outcomes"]:
        st.info(
            "No outcome has been recorded. The saved scenario is an estimate, not a simulated or observed pilot result."
        )
    else:
        for outcome in action["outcomes"]:
            reviewed = review_outcome(action, outcome)
            st.markdown(
                f"**{reviewed['classification']} · revision {outcome['revision']} · {outcome['window_start']}–{outcome['window_end']}**"
            )
            st.dataframe(pd.DataFrame([reviewed]), hide_index=True)
            st.write(
                f"Observations: {outcome['observation']}\n\nReview: {outcome['review']}"
            )
    with st.expander("Append-only revision history"):
        st.json(action["revisions"])
    st.caption(action["interpretation"])
