# Public demonstration readiness

**Status: prepared and locally tested; not deployed. No live demo URL exists.**
Hosting requires the user's publishing approval and access to their hosting
account. No paid service is necessary or introduced by this project.

## Public boundary

Use `deployment/streamlit_app.py`, which forces `RESTOPS_MODE=public` before
running the app. Public mode always loads `data/demo`; it ignores
`RESTOPS_DATA_DIR` and `RESTOPS_ACTION_DB`. The app exposes no local-mode toggle.
Each browser session gets a separate `ActionStore(':memory:')` in session state,
never a cached/shared writable SQLite connection. Scenario/actions can be practised
and downloaded but edits disappear when the session is reset. No approved status
or outcome is seeded. All input sources are committed synthetic aggregates.

This boundary is tested with conflicting environment values, separate sessions,
local reopen tests and a complete save/review workflow. It is not an authentication
or security certification. Avoid entering personal/confidential details even in
public demo forms; session data is still handled by the hosting process.

## Streamlit Community Cloud preparation

The [official deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
explain GitHub repository selection and Python configuration. The app's
`deployment/requirements.txt` is adjacent to the entry point so the
[documented dependency-file search](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
finds the small demo dependency set before the root analytical environment.
The demo pins protobuf below 6 for the
[documented Community Cloud compatibility constraint](https://docs.streamlit.io/deploy/streamlit-community-cloud/status),
while the earlier full analytic lock retains its validated workstation versions.

After approval and account sign-in:

1. Select repository `yashayyy27/RESTOPS`, branch `main`, entry point
   `deployment/streamlit_app.py`, Python 3.12.
2. Add no secrets or private-source credentials. No external databases are used.
3. Deploy, then verify the actual assigned URL, synthetic notice, January 2026
   continuation and nine views. Repeat the public-isolation/action workflow.
4. Check hosting logs/resources. Add the verified URL to README only after these
   checks pass. Record actual date/commit and status in the validation record.

## Container option

```bash
docker build -t restops-demo -f deployment/Dockerfile .
docker run --rm -p 8501:8501 restops-demo
```

The container is public-only and binds 0.0.0.0 inside the container. The normal
local app remains loopback-only. Docker build/runtime is **not verified** here;
Docker is unavailable in this environment. The actual Python entry point/server
and dependencies are tested directly. This is a compatible recipe, not a claimed
deployment. Never launch the editable local entry point as a shared public app.
