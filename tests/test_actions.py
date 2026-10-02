"""Persistence, immutability, revisions, provenance and experiment boundaries."""

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from src.actions import (
    ActionStore,
    EXAMPLE_ID,
    default_plan,
    review_outcome,
    seed_example,
)
from src.app_data import load_bundle
from src.common import ROOT
from src.scenarios import Scenario


def baseline():
    return dict(
        revenue=10000.0,
        discounts=500.0,
        transactions=250.0,
        ingredient_cost=3000.0,
        waste_cost=200.0,
        labour_cost=3000.0,
        paid_hours=100.0,
        commission_cost=600.0,
        overhead_cost=1200.0,
        campaign_cost=100.0,
        operating_profit=1900.0,
        labour_cost_pct=0.3,
        waste_pct=0.0625,
        satisfaction_score=4.0,
        late_delivery_pct=0.1,
    )


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.store = ActionStore()
        self.addCleanup(self.store.close)
        self.plan = default_plan(baseline())
        self.source = dict(
            data_kind="synthetic_history",
            period="2025-12",
            fingerprint="a" * 64,
            dataset="store_day",
        )
        self.aid = self.create()

    def create(self, store=None, **changes):
        values = dict(
            restaurant_id=1,
            restaurant_name="Fictional fixture",
            period="2025-12",
            baseline=baseline(),
            assumptions=Scenario(hours_change=-0.01, waste_rate=0.04),
            plan=self.plan,
            source=self.source,
        )
        values.update(changes)
        return (store or self.store).create(**values)

    def start(self):
        self.store.transition(
            self.aid, "approved", "Fictional practice approval", "proposed"
        )
        self.store.transition(
            self.aid, "in progress", "Fictional pilot practice", "approved"
        )

    def observe(self, **changes):
        values = dict(
            action_id=self.aid,
            kind="simulated",
            window_start="2026-01-01",
            window_end="2026-01-31",
            metrics=dict(
                labour_cost_pct=0.29, satisfaction_score=4.0, late_delivery_pct=0.1
            ),
            observation="Explicitly simulated fixture, no real intervention",
            review="Compare peers and holidays; no causal conclusion",
            expected_revision=1,
        )
        values.update(changes)
        return self.store.observe(**values)

    def test_seed_is_a_stable_idempotent_proposal_without_outcomes(self):
        frames, _ = load_bundle(ROOT / "data/demo")
        seed_example(self.store, frames)
        seed_example(self.store, frames)
        example = self.store.get(EXAMPLE_ID)
        self.assertEqual(len(self.store.list()), 2)
        self.assertEqual(example["status"], "proposed")
        self.assertEqual(example["outcomes"], [])
        self.assertEqual(example["restaurant_name"], "Wollongong")
        self.assertEqual(example["revisions"][0]["assumptions"]["hours_change"], -0.01)
        self.assertAlmostEqual(
            example["baseline"]["operating_profit"], 2992.18, delta=1
        )

    def test_local_reopen_preserves_snapshot_and_uuid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "actions.sqlite"
            first = ActionStore(path)
            aid = self.create(first)
            before = first.get(aid)
            first.close()
            second = ActionStore(path)
            self.assertEqual(before, second.get(aid))
            second.close()

    def test_all_evidence_tables_reject_update_and_delete(self):
        for table in ("actions", "revisions", "events", "outcomes"):
            with self.subTest(table=table), self.assertRaises(sqlite3.IntegrityError):
                # Insert outcome so its trigger is actually executed.
                if table == "outcomes":
                    self.start()
                    self.observe()
                with self.store.connection:
                    self.store.connection.execute(f"DELETE FROM {table}")
        with self.assertRaises(sqlite3.IntegrityError), self.store.connection:
            self.store.connection.execute("UPDATE actions SET period='2025-11'")

    def test_revision_preserves_original_snapshot_and_assumptions(self):
        before = self.store.get(self.aid)
        plan = dict(self.plan, intervention="Revise preparation batch trial")
        self.store.revise(
            self.aid, plan, Scenario(hours_change=-0.02), "Feasibility revision", 1
        )
        after = self.store.get(self.aid)
        self.assertEqual(before["baseline"], after["baseline"])
        self.assertEqual(before["snapshot_hash"], after["snapshot_hash"])
        self.assertEqual(before["revisions"][0], after["revisions"][0])
        self.assertEqual(after["revisions"][1]["assumptions"]["hours_change"], -0.02)
        with self.assertRaisesRegex(ValueError, "reload"):
            self.store.revise(self.aid, plan, Scenario(), "Stale editor", 1)

    def test_plan_dates_targets_and_required_fields_are_validated(self):
        invalid = [
            dict(self.plan, end_date="2025-12-31"),
            dict(self.plan, measurement_end="2026-02-01"),
            dict(self.plan, start_date="2025-12-01"),
            dict(self.plan, measurement_start="bad"),
            dict(self.plan, owner=""),
            dict(self.plan, target=float("nan")),
            dict(self.plan, primary_metric="invented"),
            dict(self.plan, late_delivery_max=2),
        ]
        missing = deepcopy(self.plan)
        del missing["evidence"]
        invalid.append(missing)
        for plan in invalid:
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                self.create(plan=plan)
        self.assertEqual(len(self.store.list()), 1)

    def test_invalid_baseline_and_source_fail_atomically(self):
        for changes in [
            dict(baseline=dict(baseline(), operating_profit=999)),
            dict(source=dict(self.source, fingerprint="missing")),
            dict(source=dict(self.source, data_kind="real_company")),
            dict(period="2025-13"),
            dict(restaurant_id=0),
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.create(**changes)
        self.assertEqual(len(self.store.list()), 1)

    def test_status_transitions_and_completion_gate(self):
        with self.assertRaises(ValueError):
            self.store.transition(self.aid, "completed", "Skip states", "proposed")
        self.start()
        with self.assertRaisesRegex(ValueError, "full-window"):
            self.store.transition(
                self.aid, "completed", "Missing review", "in progress"
            )
        self.observe(window_end="2026-01-15")
        with self.assertRaisesRegex(ValueError, "full-window"):
            self.store.transition(
                self.aid, "completed", "Partial review", "in progress"
            )
        self.observe()
        self.store.transition(
            self.aid,
            "completed",
            "Fictional measured exercise; no real approval",
            "in progress",
        )
        with self.assertRaises(ValueError):
            self.store.revise(self.aid, self.plan, Scenario(), "Terminal edit", 1)

    def test_cancel_is_terminal_and_status_requires_note_and_fresh_state(self):
        with self.assertRaises(ValueError):
            self.store.transition(self.aid, "approved", "", "proposed")
        self.store.transition(
            self.aid, "cancelled", "Fictional feasibility failure", "proposed"
        )
        with self.assertRaises(ValueError):
            self.store.transition(self.aid, "approved", "Stale state", "proposed")

    def test_outcome_requires_classification_guardrails_dates_and_review(self):
        with self.assertRaises(ValueError):
            self.observe()
        self.start()
        for changes in [
            dict(kind="achieved_savings"),
            dict(metrics={"labour_cost_pct": 0.29}),
            dict(window_start="2025-12-31"),
            dict(review=""),
            dict(expected_revision=2),
            dict(
                metrics=dict(
                    labour_cost_pct=-0.2, satisfaction_score=4.0, late_delivery_pct=0.1
                )
            ),
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.observe(**changes)
        self.assertEqual(self.store.get(self.aid)["outcomes"], [])

    def test_review_distinguishes_simulated_and_user_entered_and_guardrail_failure(
        self,
    ):
        self.start()
        self.observe()
        self.observe(
            kind="user_entered",
            metrics=dict(
                labour_cost_pct=0.28, satisfaction_score=2.0, late_delivery_pct=0.4
            ),
        )
        action = self.store.get(self.aid)
        reviews = [review_outcome(action, item) for item in action["outcomes"]]
        self.assertEqual(reviews[0]["classification"], "Simulated outcome")
        self.assertIn("unverified", reviews[1]["classification"])
        self.assertTrue(reviews[1]["target_met"])
        self.assertFalse(reviews[1]["guardrails_met"])
        self.assertIn("not causal", reviews[1]["caution"])
        json.dumps(action, allow_nan=False)

    def test_review_uses_recorded_revision_after_plan_changes(self):
        self.start()
        self.observe()
        self.store.revise(
            self.aid, dict(self.plan, target=0.1), Scenario(), "Different target", 1
        )
        action = self.store.get(self.aid)
        self.assertEqual(action["status"], "proposed")
        self.assertTrue(review_outcome(action, action["outcomes"][0])["target_met"])
        with self.assertRaises(ValueError):
            self.store.transition(
                self.aid, "completed", "Only old review", "in progress"
            )

    def test_public_memory_stores_are_isolated(self):
        another = ActionStore()
        self.addCleanup(another.close)
        self.assertEqual(another.list(), [])
        self.create(another)
        self.assertNotEqual(another.list()[0]["action_id"], self.aid)
        self.assertEqual(len(self.store.list()), 1)

    def test_unknown_schema_and_missing_immutable_trigger_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.sqlite"
            db = sqlite3.connect(path)
            db.execute("CREATE TABLE unrelated(id)")
            db.commit()
            db.close()
            with self.assertRaisesRegex(ValueError, "Unknown database"):
                ActionStore(path)
            path = Path(folder) / "broken.sqlite"
            store = ActionStore(path)
            store.connection.execute("DROP TRIGGER actions_update")
            store.connection.commit()
            store.close()
            with self.assertRaisesRegex(ValueError, "trigger"):
                ActionStore(path)

    def test_nonviable_scenario_exports_null_break_even(self):
        aid = self.create(assumptions=Scenario(discount_rate=0.9))
        action = self.store.get(aid)
        self.assertIsNone(action["revisions"][0]["estimate"]["break_even_revenue"])
        json.dumps(action, allow_nan=False)
