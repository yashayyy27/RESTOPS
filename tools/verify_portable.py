"""Run all demo-only checks and save actual counts/environment/resource evidence."""

import json
from pathlib import Path
import platform
import resource
import sys
import time
import unittest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
patterns = (
    "test_app.py",
    "test_actions.py",
    "test_public.py",
    "test_management.py",
    "test_planning.py",
    "test_exports.py",
    "test_tableau_bundle.py",
    "test_links.py",
)
suite = unittest.TestSuite()
loader = unittest.TestLoader()
for pattern in patterns:
    suite.addTests(loader.discover(str(root / "tests"), pattern=pattern))
start = time.perf_counter()
result = unittest.TextTestRunner(verbosity=2).run(suite)
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
record = {
    "scope": "Portable demo-only developer automation; no raw/full datasets required",
    "python": platform.python_version(),
    "platform": platform.platform(),
    "tests": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skips": len(result.skipped),
    "seconds": round(time.perf_counter() - start, 3),
    "peak_test_process_rss_mib": round(
        peak / (1024**2 if sys.platform == "darwin" else 1024), 1
    ),
    "memory_boundary": "Peak whole test-process RSS, including independent AppTest sessions; not cloud multi-user capacity or server steady-state memory",
    "raw_sources_present": (root / "data/raw/transactions.csv").exists(),
    "full_marts_present": (root / "data/tableau/store_day.csv").exists(),
    "patterns": list(patterns),
}
output = root / "outputs/portable_validation.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
raise SystemExit(0 if result.wasSuccessful() else 1)
