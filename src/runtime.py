"""Fail-closed deployment mode: public sessions cannot select local sources."""

import os

from .common import ROOT


def app_mode():
    mode = os.environ.get("RESTOPS_MODE", "public").lower()
    if mode not in ("public", "local"):
        raise ValueError("RESTOPS_MODE must be public or local")
    return mode


def action_path(mode):
    if mode == "public":
        return ":memory:"
    if mode != "local":
        raise ValueError("Unknown runtime mode")
    return os.environ.get("RESTOPS_ACTION_DB", str(ROOT / "outputs/actions.sqlite"))
