"""Copy Git-visible files only; do not carry local datasets or environment state."""

from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
target = Path(sys.argv[1]).resolve()
if target.exists():
    raise SystemExit("Use a new empty destination for an independent demo copy")
paths = (
    subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
    )
    .decode()
    .split("\0")
)
for relative in filter(None, paths):
    source = root / relative
    if source.is_file():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
print(f"Copied {sum(bool(p) for p in paths)} Git-visible paths into {target}")
print("Raw/full marts, SQLite databases and virtual environments are absent.")
