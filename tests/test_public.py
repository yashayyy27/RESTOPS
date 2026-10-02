"""Public entry-point isolation, guided navigation and complete action workflow."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.app_data import data_folder
from src.common import ROOT
from src.runtime import action_path, app_mode


class PublicWorkflowTests(unittest.TestCase):
    def app(self, file="streamlit_app.py"):
        return AppTest.from_file(str(ROOT / file), default_timeout=30).run()

    def clean(self, app):
        self.assertFalse(app.exception, [e.message for e in app.exception])

    def test_default_is_public_and_ignores_local_data_and_database_overrides(self):
        with patch.dict(
            os.environ,
            {
                "RESTOPS_MODE": "public",
                "RESTOPS_DATA_DIR": "/missing/private",
                "RESTOPS_ACTION_DB": "/missing/shared.sqlite",
            },
        ):
            self.assertEqual(app_mode(), "public")
            self.assertEqual(data_folder("auto", public=True), ROOT / "data/demo")
            self.assertEqual(action_path("public"), ":memory:")
            app = self.app()
            self.clean(app)
            self.assertEqual(app.selectbox(key="data_mode").options, ["Demo"])
            app.selectbox(key="view").select("Action & experiment tracker").run()
            self.clean(app)
            self.assertEqual(app.session_state["action_store"].path, ":memory:")

    def test_public_entry_point_cannot_be_changed_to_local_by_environment(self):
        with patch.dict(
            os.environ,
            {"RESTOPS_MODE": "local", "RESTOPS_DATA_DIR": "/missing/private"},
        ):
            app = self.app("deployment/streamlit_app.py")
            self.clean(app)
            self.assertEqual(app.selectbox(key="data_mode").value, "Demo")
            self.assertEqual(os.environ["RESTOPS_MODE"], "public")

    def test_invalid_mode_fails_closed(self):
        with patch.dict(os.environ, {"RESTOPS_MODE": "publci"}):
            with self.assertRaises(ValueError):
                app_mode()

    def test_guided_investigation_scenario_save_and_outcome_workflow(self):
        with patch.dict(os.environ, {"RESTOPS_MODE": "public"}):
            app = self.app()
            app.button(key="start_investigation").click().run()
            self.clean(app)
            self.assertEqual(
                app.selectbox(key="view").value, "Restaurant investigation"
            )
            self.assertEqual(app.selectbox(key="focus_store").value, "Wollongong")
            app.button(key="investigate_scenario").click().run()
            app.slider(key="hours_change").set_value(-1).run()
            app.number_input(key="waste_rate").set_value(4.0).run()
            draft_profit = app.metric[1].value
            app.button(key="scenario_action").click().run()
            self.clean(app)
            self.assertEqual(
                app.selectbox(key="view").value, "Action & experiment tracker"
            )
            self.assertEqual(
                app.session_state["action_draft"]["restaurant_name"], "Wollongong"
            )
            app.button(key="save_action").click().run()
            self.clean(app)
            store = app.session_state["action_store"]
            actions = store.list()
            self.assertEqual(len(actions), 2)
            action = actions[-1]
            self.assertEqual(
                action["revisions"][0]["assumptions"]["hours_change"], -0.01
            )
            self.assertEqual(action["revisions"][0]["assumptions"]["waste_rate"], 0.04)
            self.assertEqual(action["status"], "proposed")
            self.assertEqual(action["outcomes"], [])
            self.assertIn("4,152", draft_profit)
            for status in ("approved", "in progress"):
                app.selectbox(key="next_status").select(status)
                app.text_area(key="status_note").set_value(
                    "Fictional workflow exercise; no actual approval"
                )
                app.button(key="transition_action").click().run()
                self.clean(app)
            app.text_area(key="outcome_observation").set_value(
                "Simulated practice values from synthetic case; no executed pilot"
            )
            app.text_area(key="outcome_review").set_value(
                "Before/after does not establish causality; review service before deciding"
            )
            app.button(key="record_outcome").click().run()
            self.clean(app)
            self.assertEqual(
                store.get(action["action_id"])["outcomes"][0]["kind"], "simulated"
            )
            app.selectbox(key="next_status").select("completed")
            app.text_area(key="status_note").set_value(
                "Completed simulated exercise only"
            )
            app.button(key="transition_action").click().run()
            self.clean(app)
            self.assertEqual(store.get(action["action_id"])["status"], "completed")
            other = self.app()
            other.selectbox(key="view").select("Action & experiment tracker").run()
            self.clean(other)
            self.assertEqual(len(other.session_state["action_store"].list()), 1)
            self.assertEqual(
                other.session_state["action_store"].list()[0]["outcomes"], []
            )

    def test_local_mode_reopens_persisted_action(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            os.environ,
            {
                "RESTOPS_MODE": "local",
                "RESTOPS_DATA_DIR": str(ROOT / "data/demo"),
                "RESTOPS_ACTION_DB": str(Path(folder) / "actions.sqlite"),
            },
        ):
            app = self.app()
            app.selectbox(key="view").select("Restaurant investigation").run()
            app.button(key="investigate_action").click().run()
            app.button(key="save_action").click().run()
            self.clean(app)
            frozen = app.session_state["action_store"].list()[-1]
            second = self.app()
            second.selectbox(key="view").select("Action & experiment tracker").run()
            self.clean(second)
            self.assertEqual(
                second.session_state["action_store"].get(frozen["action_id"]), frozen
            )

    def test_register_empty_filter_and_focus_changes_are_safe(self):
        with patch.dict(os.environ, {"RESTOPS_MODE": "public"}):
            app = self.app()
            app.selectbox(key="view").select("Restaurant investigation").run()
            app.selectbox(key="state").select("QLD").run()
            self.clean(app)
            self.assertNotEqual(app.selectbox(key="focus_store").value, "Wollongong")
            app.selectbox(key="view").select("Action & experiment tracker").run()
            self.clean(app)
            self.assertEqual(app.metric[0].value, "0")
            self.assertIn("No actions", app.info[-1].value)
