"""One-command orchestration: python -m src.run_pipeline [--regenerate]."""

import argparse
import gc
import importlib.metadata
import json
import os
import platform
import time

from .common import RAW, REPORTS, ROOT, config


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild RESTOPS from synthetic source data."
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Replace raw exports using the configured seed.",
    )
    parser.add_argument(
        "--skip-notebooks",
        action="store_true",
        help="Create notebook sources without executing them.",
    )
    args = parser.parse_args()
    os.environ.setdefault("LOKY_MAX_CPU_COUNT", "2")
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
    for directory in (
        RAW,
        REPORTS / "exports",
        REPORTS / "figures",
        ROOT / "data/processed",
        ROOT / "data/tableau",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    from . import generate_data, clean_data, feature_engineering, kpi_engine
    from . import analysis, forecasting, database, reporting, project_assets
    from . import validation, build_management, excel_inputs

    started = time.perf_counter()
    manifest = RAW / "generation_manifest.json"
    should_generate = args.regenerate or not manifest.exists()
    if not should_generate:
        prior = json.loads(manifest.read_text())
        if prior.get("configuration") != config():
            raise ValueError(
                "Raw generation configuration differs; run with --regenerate."
            )
        if any(not (RAW / f"{name}.csv").exists() for name in clean_data.PRIMARY_KEYS):
            raise ValueError("Raw source set is incomplete; run with --regenerate.")
    steps = ([generate_data.run] if should_generate else []) + [
        clean_data.run,
        feature_engineering.run,
        kpi_engine.run,
        analysis.run,
        forecasting.run,
        database.run,
        validation.run,
        reporting.run,
        build_management.run,
        excel_inputs.run,
        project_assets.run,
    ]
    for step in steps:
        step_started = time.perf_counter()
        step()
        gc.collect()
        print(
            f"{step.__module__.split('.')[-1]} completed in {time.perf_counter()-step_started:.1f}s",
            flush=True,
        )
    if not args.skip_notebooks:
        project_assets.execute_notebooks()
    packages = (
        "pandas",
        "numpy",
        "matplotlib",
        "scikit-learn",
        "holidays",
        "nbformat",
        "nbclient",
        "streamlit",
        "plotly",
    )
    metadata = {
        "configuration": config(),
        "python": platform.python_version(),
        "package_versions": {
            name: importlib.metadata.version(name) for name in packages
        },
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "notebooks_executed": not args.skip_notebooks,
        "quality": json.loads((REPORTS / "quality_summary.json").read_text()),
        "forecast": json.loads((REPORTS / "forecast_summary.json").read_text()),
    }
    (REPORTS / "run_metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"RESTOPS ready. Open {REPORTS / 'portfolio.html'}", flush=True)


if __name__ == "__main__":
    main()
