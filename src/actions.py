"""Append-only action evidence, immutable financial snapshots and local SQLite.

Public sessions use their own in-memory database. No outcome is inferred from a
scenario and no status change establishes actual stakeholder approval.
"""

from dataclasses import asdict
from datetime import date, datetime, timezone
import hashlib
import json
import math
import re
from pathlib import Path
import sqlite3
import uuid

from .scenarios import Scenario, simulate

STATUSES = ("proposed", "approved", "in progress", "completed", "cancelled")
TRANSITIONS = {
    "proposed": ("approved", "cancelled"),
    "approved": ("in progress", "cancelled"),
    "in progress": ("completed", "cancelled"),
    "completed": (),
    "cancelled": (),
}
METRICS = {
    "labour_cost_pct": "lower",
    "waste_pct": "lower",
    "operating_margin_pct": "higher",
    "satisfaction_score": "higher",
    "operating_profit": "higher",
    "revenue": "higher",
}
PLAN_FIELDS = {
    "problem",
    "evidence",
    "intervention",
    "owner",
    "start_date",
    "end_date",
    "measurement_start",
    "measurement_end",
    "primary_metric",
    "target",
    "satisfaction_min",
    "late_delivery_max",
    "comparison_approach",
    "expected_impact_basis",
}
SCHEMA = """
CREATE TABLE actions (
    action_id TEXT PRIMARY KEY,
    restaurant_id INTEGER NOT NULL CHECK (restaurant_id > 0),
    restaurant_name TEXT NOT NULL,
    period TEXT NOT NULL,
    baseline_json TEXT NOT NULL CHECK (json_valid(baseline_json)),
    source_json TEXT NOT NULL CHECK (json_valid(source_json)),
    snapshot_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE revisions (
    action_id TEXT NOT NULL REFERENCES actions(action_id),
    revision INTEGER NOT NULL CHECK (revision > 0),
    plan_json TEXT NOT NULL CHECK (json_valid(plan_json)),
    assumptions_json TEXT NOT NULL CHECK (json_valid(assumptions_json)),
    estimate_json TEXT NOT NULL CHECK (json_valid(estimate_json)),
    revision_note TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (action_id, revision)
);
CREATE TABLE events (
    action_id TEXT NOT NULL REFERENCES actions(action_id),
    sequence INTEGER NOT NULL CHECK (sequence > 0),
    status TEXT NOT NULL CHECK (status IN ('proposed','approved','in progress','completed','cancelled')),
    note TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (action_id, sequence)
);
CREATE TABLE outcomes (
    outcome_id TEXT PRIMARY KEY,
    action_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('simulated', 'user_entered')),
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    metrics_json TEXT NOT NULL CHECK (json_valid(metrics_json)),
    observation TEXT NOT NULL,
    review TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (action_id, revision) REFERENCES revisions(action_id, revision)
);
"""
EXPECTED_COLUMNS = {
    "actions": [
        "action_id",
        "restaurant_id",
        "restaurant_name",
        "period",
        "baseline_json",
        "source_json",
        "snapshot_hash",
        "created_at",
    ],
    "revisions": [
        "action_id",
        "revision",
        "plan_json",
        "assumptions_json",
        "estimate_json",
        "revision_note",
        "created_at",
    ],
    "events": ["action_id", "sequence", "status", "note", "created_at"],
    "outcomes": [
        "outcome_id",
        "action_id",
        "revision",
        "kind",
        "window_start",
        "window_end",
        "metrics_json",
        "observation",
        "review",
        "created_at",
    ],
}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def encode(value):
    """Strict portable JSON; caller must explicitly replace undefined estimates."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def iso_date(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("Dates must use YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Dates must use valid YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise ValueError("Dates must use YYYY-MM-DD")
    return parsed


def text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 6000:
        raise ValueError(f"{field} is required (maximum 6000 characters)")
    return value.strip()


def number(value, field):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def validate_plan(plan, period):
    if set(plan) != PLAN_FIELDS:
        raise ValueError("Measurement plan fields do not match the schema")
    p = dict(plan)
    for key in (
        "problem",
        "evidence",
        "intervention",
        "owner",
        "comparison_approach",
        "expected_impact_basis",
    ):
        p[key] = text(p[key], key)
    dates = {
        key: iso_date(p[key])
        for key in ("start_date", "end_date", "measurement_start", "measurement_end")
    }
    if (
        dates["start_date"] > dates["end_date"]
        or dates["measurement_start"] > dates["measurement_end"]
    ):
        raise ValueError("Start dates must precede end dates")
    if (
        dates["measurement_start"] < dates["start_date"]
        or dates["measurement_end"] > dates["end_date"]
    ):
        raise ValueError("Measurement window must be inside the intervention window")
    if dates["start_date"].strftime("%Y-%m") <= period:
        raise ValueError("Pilot must start after the frozen baseline month")
    if p["primary_metric"] not in METRICS:
        raise ValueError("Unknown primary success metric")
    for key in ("target", "satisfaction_min", "late_delivery_max"):
        p[key] = number(p[key], key)
    if not 1 <= p["satisfaction_min"] <= 5 or not 0 <= p["late_delivery_max"] <= 1:
        raise ValueError(
            "Service guardrails require satisfaction 1–5 and late-delivery fraction 0–1"
        )
    metric = p["primary_metric"]
    if metric.endswith("_pct") and not -1 <= p["target"] <= 1:
        raise ValueError("Rate targets use fractions between -1 and 1")
    if metric in ("labour_cost_pct", "waste_pct") and p["target"] < 0:
        raise ValueError("Cost-share targets cannot be negative")
    if metric == "satisfaction_score" and not 1 <= p["target"] <= 5:
        raise ValueError("Satisfaction target must be 1–5")
    if metric == "revenue" and p["target"] < 0:
        raise ValueError("Revenue target cannot be negative")
    return p


def estimate(baseline, assumptions):
    result = simulate(baseline, Scenario(**assumptions))
    # A nonviable scenario has no finite break-even; preserve it as JSON null.
    return {
        key: float(value) if math.isfinite(value) else None
        for key, value in result.items()
    }


class ActionStore:
    """Single-user local persistence or per-session memory; all records append only."""

    def __init__(self, path=":memory:"):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(
            self.path, timeout=10, check_same_thread=False
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            existing = self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            if existing:
                self.close()
                raise ValueError(
                    "Unknown database schema; no migration or overwrite attempted"
                )
            self.connection.executescript(SCHEMA)
            for table in EXPECTED_COLUMNS:
                for operation in ("UPDATE", "DELETE"):
                    self.connection.execute(
                        f"CREATE TRIGGER {table}_{operation.lower()} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'Immutable evidence: append a revision'); END"
                    )
            self.connection.execute("PRAGMA user_version=1")
            self.connection.commit()
        try:
            self.validate_schema()
        except ValueError:
            self.close()
            raise

    def close(self):
        self.connection.close()

    def validate_schema(self):
        if self.connection.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise ValueError("Unsupported action schema version")
        for table, columns in EXPECTED_COLUMNS.items():
            actual = [
                row["name"]
                for row in self.connection.execute(f"PRAGMA table_info({table})")
            ]
            if actual != columns:
                raise ValueError(f"Invalid {table} schema")
            for operation in ("update", "delete"):
                if not self.connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?",
                    (f"{table}_{operation}",),
                ).fetchone():
                    raise ValueError("Immutable evidence trigger missing")
        if (
            self.connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
            or self.connection.execute("PRAGMA foreign_key_check").fetchone()
        ):
            raise ValueError("Action database integrity failed")

    def create(
        self,
        restaurant_id,
        restaurant_name,
        period,
        baseline,
        assumptions,
        plan,
        source,
        action_id=None,
    ):
        if (
            isinstance(restaurant_id, bool)
            or not isinstance(restaurant_id, int)
            or restaurant_id <= 0
        ):
            raise ValueError("Restaurant ID must be a positive integer")
        if not isinstance(period, str) or len(period) != 7:
            raise ValueError("Baseline period must use YYYY-MM")
        iso_date(period + "-01")
        name = text(restaurant_name, "restaurant_name")
        b = {key: number(value, key) for key, value in dict(baseline).items()}
        base = simulate(b)
        if "operating_profit" not in b or not math.isclose(
            base["operating_profit"], b["operating_profit"], abs_tol=0.01, rel_tol=0
        ):
            raise ValueError("Baseline profit must reconcile to the frozen ledger")
        if (
            not source
            or not re.fullmatch(r"[0-9a-f]{64}", str(source.get("fingerprint", "")))
            or source.get("period") != period
            or source.get("data_kind") != "synthetic_history"
        ):
            raise ValueError(
                "Source fingerprint and synthetic-history classification are required"
            )
        assumptions = (
            asdict(assumptions)
            if isinstance(assumptions, Scenario)
            else dict(assumptions)
        )
        p, result = validate_plan(plan, period), estimate(b, assumptions)
        aid = action_id or str(uuid.uuid4())
        uuid.UUID(aid)
        now = timestamp()
        with self.connection:
            self.connection.execute(
                "INSERT INTO actions VALUES (?,?,?,?,?,?,?,?)",
                (
                    aid,
                    restaurant_id,
                    name,
                    period,
                    encode(b),
                    encode(source),
                    digest({"baseline": b, "source": source}),
                    now,
                ),
            )
            self.connection.execute(
                "INSERT INTO revisions VALUES (?,?,?,?,?,?,?)",
                (
                    aid,
                    1,
                    encode(p),
                    encode(assumptions),
                    encode(result),
                    "Initial proposal; no approval or outcome",
                    now,
                ),
            )
            self.connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (
                    aid,
                    1,
                    "proposed",
                    "Fictional proposal created; no achieved impact",
                    now,
                ),
            )
        return aid

    def get(self, action_id):
        row = self.connection.execute(
            "SELECT * FROM actions WHERE action_id=?", (action_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Action not found")
        result = dict(row)
        result["baseline"] = json.loads(result.pop("baseline_json"))
        result["source"] = json.loads(result.pop("source_json"))
        if (
            digest({"baseline": result["baseline"], "source": result["source"]})
            != result["snapshot_hash"]
        ):
            raise ValueError("Frozen snapshot hash mismatch")
        result["revisions"] = []
        for item in self.connection.execute(
            "SELECT * FROM revisions WHERE action_id=? ORDER BY revision", (action_id,)
        ):
            revision = dict(item)
            for key in ("plan", "assumptions", "estimate"):
                revision[key] = json.loads(revision.pop(key + "_json"))
            result["revisions"].append(revision)
        result["events"] = [
            dict(item)
            for item in self.connection.execute(
                "SELECT * FROM events WHERE action_id=? ORDER BY sequence", (action_id,)
            )
        ]
        result["status"] = result["events"][-1]["status"]
        result["outcomes"] = []
        for item in self.connection.execute(
            "SELECT * FROM outcomes WHERE action_id=? ORDER BY created_at, outcome_id",
            (action_id,),
        ):
            outcome = dict(item)
            outcome["metrics"] = json.loads(outcome.pop("metrics_json"))
            result["outcomes"].append(outcome)
        result["interpretation"] = (
            "Scenario estimates are conditional, not achieved savings. User-entered observations are unverified. Before/after comparisons do not establish causality. Overlapping opportunities must not be summed as guaranteed savings."
        )
        return result

    def list(self, restaurant_ids=None):
        ids = [
            row[0]
            for row in self.connection.execute(
                "SELECT action_id FROM actions ORDER BY created_at, action_id"
            )
        ]
        rows = [self.get(aid) for aid in ids]
        return (
            rows
            if restaurant_ids is None
            else [r for r in rows if r["restaurant_id"] in restaurant_ids]
        )

    def revise(self, action_id, plan, assumptions, note, expected_revision):
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            action = self.get(action_id)
            if action["status"] in ("completed", "cancelled"):
                raise ValueError(
                    "Terminal actions cannot be revised; create a new action"
                )
            latest = action["revisions"][-1]["revision"]
            if expected_revision != latest:
                raise ValueError("Revision changed; reload before saving")
            p = validate_plan(plan, action["period"])
            a = (
                asdict(assumptions)
                if isinstance(assumptions, Scenario)
                else dict(assumptions)
            )
            result = estimate(action["baseline"], a)
            self.connection.execute(
                "INSERT INTO revisions VALUES (?,?,?,?,?,?,?)",
                (
                    action_id,
                    latest + 1,
                    encode(p),
                    encode(a),
                    encode(result),
                    text(note, "revision reason"),
                    timestamp(),
                ),
            )

            if action["status"] in ("approved", "in progress"):
                self.connection.execute(
                    "INSERT INTO events VALUES (?,?,?,?,?)",
                    (
                        action_id,
                        len(action["events"]) + 1,
                        "proposed",
                        f"Revision {latest + 1} requires fresh fictional workflow approval; earlier observations remain tied to their revision",
                        timestamp(),
                    ),
                )

    def transition(self, action_id, status, note, expected_status):
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            action = self.get(action_id)
            if action["status"] != expected_status:
                raise ValueError("Status changed; reload before updating")
            if status not in TRANSITIONS[action["status"]]:
                raise ValueError("Invalid status transition")
            latest = action["revisions"][-1]
            if status == "completed" and not any(
                o["revision"] == latest["revision"]
                and o["window_start"] == latest["plan"]["measurement_start"]
                and o["window_end"] == latest["plan"]["measurement_end"]
                for o in action["outcomes"]
            ):
                raise ValueError(
                    "Completion requires a full-window outcome review for the latest revision"
                )
            self.connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (
                    action_id,
                    len(action["events"]) + 1,
                    status,
                    text(note, "status explanation"),
                    timestamp(),
                ),
            )

    def observe(
        self,
        action_id,
        kind,
        window_start,
        window_end,
        metrics,
        observation,
        review,
        expected_revision,
    ):
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            action = self.get(action_id)
            if action["status"] != "in progress":
                raise ValueError("Outcomes require an in-progress action")
            revision = action["revisions"][-1]
            if expected_revision != revision["revision"]:
                raise ValueError("Revision changed; reload before recording an outcome")
            if kind not in ("simulated", "user_entered"):
                raise ValueError("Outcome kind must be simulated or user_entered")
            start, end = iso_date(window_start), iso_date(window_end)
            p = revision["plan"]
            if (
                start > end
                or start < iso_date(p["measurement_start"])
                or end > iso_date(p["measurement_end"])
            ):
                raise ValueError(
                    "Observation dates must fall within the measurement window"
                )
            required = {p["primary_metric"], "satisfaction_score", "late_delivery_pct"}
            if set(metrics) != required:
                raise ValueError(
                    "Outcome must contain primary metric and both service guardrails"
                )
            m = {key: number(value, key) for key, value in metrics.items()}
            if (
                not 1 <= m["satisfaction_score"] <= 5
                or not 0 <= m["late_delivery_pct"] <= 1
            ):
                raise ValueError("Invalid observed service metrics")
            if (
                p["primary_metric"].endswith("_pct")
                and not -1 <= m[p["primary_metric"]] <= 1
            ):
                raise ValueError("Outcome rate must be a fraction between -1 and 1")
            if (
                p["primary_metric"] in ("labour_cost_pct", "waste_pct", "revenue")
                and m[p["primary_metric"]] < 0
            ):
                raise ValueError("Observed cost shares/revenue cannot be negative")
            oid = str(uuid.uuid4())
            self.connection.execute(
                "INSERT INTO outcomes VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    oid,
                    action_id,
                    revision["revision"],
                    kind,
                    window_start,
                    window_end,
                    encode(m),
                    text(observation, "observations and provenance"),
                    text(review, "outcome review"),
                    timestamp(),
                ),
            )
        return oid


def review_outcome(action, outcome):
    """Evaluate recorded values, not causal impact; honour the observed revision."""
    revision = next(
        r for r in action["revisions"] if r["revision"] == outcome["revision"]
    )
    p, m = revision["plan"], outcome["metrics"]
    metric = p["primary_metric"]
    success = (
        m[metric] <= p["target"]
        if METRICS[metric] == "lower"
        else m[metric] >= p["target"]
    )
    return {
        "primary_metric": metric,
        "recorded_value": m[metric],
        "target": p["target"],
        "target_met": success,
        "guardrails_met": m["satisfaction_score"] >= p["satisfaction_min"]
        and m["late_delivery_pct"] <= p["late_delivery_max"],
        "window_complete": outcome["window_start"] == p["measurement_start"]
        and outcome["window_end"] == p["measurement_end"],
        "classification": (
            "Simulated outcome"
            if outcome["kind"] == "simulated"
            else "User-entered observed outcome (unverified)"
        ),
        "baseline_value": action["baseline"].get(metric),
        "caution": "Before/after is descriptive, not causal. Different-duration financial totals are not comparable without normalisation. Meeting recorded thresholds is not proof of business impact.",
    }


def default_plan(baseline):
    """Explicit fictional January pilot defaults, adjustable before saving."""
    return {
        "problem": "Wollongong has low operating margin and high labour share.",
        "evidence": f"December synthetic baseline: revenue AUD {baseline['revenue']:,.2f}; operating profit AUD {baseline['operating_profit']:,.2f}; labour share {baseline['labour_cost_pct']:.1%}.",
        "intervention": "Trial staggered starts with 1% fewer paid hours; reduce preparation waste to 4% without reducing meal-peak coverage.",
        "owner": "Fictional Area Manager — Alex Morgan",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "measurement_start": "2026-01-01",
        "measurement_end": "2026-01-31",
        "primary_metric": "labour_cost_pct",
        "target": float(baseline["labour_cost_pct"] * 0.99),
        "satisfaction_min": 3.5,
        "late_delivery_max": 0.25,
        "comparison_approach": "Same-weekday pre-period plus unpromoted NSW location peers; review demand, holidays and campaign changes. This is an observational pilot, not causal proof.",
        "expected_impact_basis": "Monthly contribution delta from saved scenario with unchanged demand/prices; not realised or annualised savings. Labour and waste opportunities may overlap.",
    }


EXAMPLE_ID = "c10691f4-018d-5a91-8c76-27d6f21265d2"


def seed_example(store, frames):
    """Idempotent proposal only; never seed approvals or achieved outcomes."""
    from .management import aggregate

    if any(row["action_id"] == EXAMPLE_ID for row in store.list()):
        return EXAMPLE_ID
    daily = frames["store_day"]
    rows = daily[daily.restaurant_name.eq("Wollongong") & daily.month.eq("2025-12")]
    if rows.empty:
        return None
    b = {
        key: float(value)
        for key, value in aggregate(rows).items()
        if math.isfinite(value)
    }
    source = {
        "data_kind": "synthetic_history",
        "grain": "restaurant/calendar month",
        "dataset": "store_day",
        "period": "2025-12",
        "fingerprint": hashlib.sha256(
            rows.sort_values("business_date").to_csv(index=False).encode()
        ).hexdigest(),
    }
    return store.create(
        int(rows.restaurant_id.iloc[0]),
        "Wollongong",
        "2025-12",
        b,
        Scenario(hours_change=-0.01, waste_rate=0.04),
        default_plan(b),
        source,
        EXAMPLE_ID,
    )
