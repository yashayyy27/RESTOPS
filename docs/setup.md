# Setup, demonstration and reproduction

Run all commands from the repository root. Python **3.12** is the tested version.

## Portable public-session demonstration

```bash
git clone https://github.com/yashayyy27/RESTOPS.git
cd RESTOPS
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-demo.txt
python -m pip check
python -m streamlit run deployment/streamlit_app.py
```

Windows PowerShell: activate with `.venv\Scripts\Activate.ps1`. Open
`http://127.0.0.1:8501`. No raw generation or database service is required.
The public entry point forcibly selects public mode. The root app also defaults
public unless explicitly configured local. Public data-directory/database overrides
are ignored. Session-only SQLite lives in memory; restarting the session loses edits.

## Editable local actions

macOS/Linux:

```bash
RESTOPS_MODE=local python -m streamlit run streamlit_app.py
```

PowerShell:

```powershell
$env:RESTOPS_MODE = 'local'
python -m streamlit run streamlit_app.py
```

Local Auto uses full marts if they exist, otherwise committed Demo. To force
Demo choose the Dataset control. Local actions persist in ignored
`outputs/actions.sqlite`; optional `RESTOPS_ACTION_DB` specifies a local path.
Do not commit databases, exports containing personal notes or credentials.
Each new database seeds one fictional Wollongong proposal, with no outcomes.
Unknown versions/schemas fail closed; automatic destructive migration is absent.
Local mode is a single-user portfolio tool, not an authenticated shared service.

## Portable checks without generating raw data

```bash
python -m pip install -r requirements-demo-dev.txt
python -m unittest discover -s tests -p test_app.py -v
python -m unittest discover -s tests -p test_public.py -v
python -m unittest discover -s tests -p test_actions.py -v
python -m unittest discover -s tests -p test_management.py -v
python -m unittest discover -s tests -p test_planning.py -v
python -m unittest discover -s tests -p test_exports.py -v
python -m unittest discover -s tests -p test_tableau_bundle.py -v
python -m unittest discover -s tests -p test_links.py -v
```

## Full analytical reproduction

The full suite includes checks that need regenerated source CSVs and SQLite.
Install the analytical lock in a separate virtual environment when keeping the
public demo's compatible protobuf constraint isolated:

```bash
python3.12 -m venv .venv-analytics
source .venv-analytics/bin/activate
python -m pip install -r requirements-lock.txt
python -m src.run_pipeline --regenerate --skip-notebooks
python -m unittest discover -s tests -v
python -m black --check --workers 1 src tests streamlit_app.py deployment tools/clean_demo_checkout.py tools/verify_portable.py
python -m compileall -q src tests streamlit_app.py deployment
```

Omit `--skip-notebooks` to execute all six notebooks in the pipeline. Generating
full data takes several minutes and creates large ignored files. Configuration
in `config/project_config.json` fixes seed 42, dates and operating assumptions.
It never creates achieved tracker outcomes. The optional Excel authoring runtime
is separate; committed XLSX and CSV outputs work without it.

## Independent checkout check

`python tools/clean_demo_checkout.py /tmp/restops-demo-new` copies only Git-visible
files into a new directory. It excludes raw/full marts, local SQLite and virtual
environments. Run portable checks there with a fresh environment. This mirrors
recruiter access without relying on this workstation's generated data.

Use `python -m src.tableau_bundle` to rebuild the minimal Tableau ZIP from the
committed demo; it verifies data only, not a native workbook.
