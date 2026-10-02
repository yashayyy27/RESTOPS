"""RESTOPS local management app. Run: streamlit run streamlit_app.py."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from src.app_data import data_folder, load_bundle
from src.app_views import VIEWS, render_view

st.set_page_config(
    page_title="RESTOPS · Performance control", page_icon="🏁", layout="wide"
)
st.markdown(
    """<style>
.block-container{padding-top:4.5rem;max-width:1500px}
h1{font-style:italic;letter-spacing:-1.5px;text-transform:uppercase}
h2{letter-spacing:-.6px}
[data-testid="stMetric"]{background:#19191f;border:1px solid #363640;border-top:3px solid #ff3b30;padding:16px;border-radius:3px 16px 3px 3px}
[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums}
@media(max-width:1100px){
 [data-testid="stHorizontalBlock"]{flex-wrap:wrap}
 [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{min-width:190px;flex:1 1 calc(50% - 1rem)}
 [data-testid="stMetricValue"]{font-size:1.65rem}
}
@media(max-width:600px){
 [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{flex-basis:100%}
}
[data-testid="stSidebar"]{border-right:1px solid #363640}
.restops-label{color:#ff3b30;font:11px monospace;letter-spacing:2px;margin-bottom:12px}
.restops-brand{font-size:30px;font-weight:900;font-style:italic;letter-spacing:-1px}
</style>""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def bundle(path, manifest_mtime):
    return load_bundle(path)


with st.sidebar:
    st.markdown(
        '<div class="restops-brand">RESTOPS</div><div class="restops-label">PERFORMANCE CONTROL</div>',
        unsafe_allow_html=True,
    )
    view = st.selectbox("Management view", VIEWS, key="view")
    mode = st.selectbox(
        "Dataset",
        ["Auto", "Demo"],
        key="data_mode",
        help="Auto uses full local marts when ready; otherwise the committed 92-day demo.",
    )

folder = data_folder(mode.lower())
manifest_path = folder / "app_manifest.json"
if not manifest_path.exists():
    st.error(
        "Management data is not ready. Run `python -m src.run_pipeline --skip-notebooks` from the repository root."
    )
    st.stop()
frames, meta = bundle(str(folder), manifest_path.stat().st_mtime_ns)
stores = (
    frames["store_day"][["restaurant_id", "restaurant_name", "state", "area"]]
    .drop_duplicates()
    .sort_values("restaurant_name")
)
with st.sidebar:
    state = st.selectbox("State", ["All"] + sorted(stores.state.unique()), key="state")
    available = stores if state == "All" else stores[stores.state.eq(state)]
    chosen = st.multiselect(
        "Restaurants",
        available.restaurant_name.tolist(),
        default=available.restaurant_name.tolist(),
        key=f"restaurants_{state}",
    )
    months = sorted(frames["store_month_kpis"].month.unique(), reverse=True)
    month = st.selectbox(
        "Reporting month",
        months,
        key="month",
        help="Applies to historical finance and scenarios. Other views label their own periods.",
    )
    st.divider()
    st.caption(
        f"{meta['mode'].upper()} DATA · {meta['history_start']} to {meta['history_end']}"
    )
    st.caption("Fictional Australian operation. All money is AUD excluding GST.")
    st.caption("Forecast continuation: January 2026. No live restaurant data.")

ids = available.loc[available.restaurant_name.isin(chosen), "restaurant_id"].tolist()
if not ids:
    st.info("Select at least one restaurant to investigate.")
    st.stop()
st.markdown(
    f'<div class="restops-label">{VIEWS.index(view)+1:02d} / RESTAURANT OPERATIONS INTELLIGENCE</div>',
    unsafe_allow_html=True,
)
st.title(view)
st.caption(
    f"Southern Table Hospitality · {len(ids)} selected restaurants · Historical reporting month {month} · Synthetic case study"
)
render_view(view, frames, meta, ids, month)
st.divider()
st.caption(
    "RESTOPS connects restaurant operations with commercial analysis and testable decisions. Estimates, observed relationships and statistical forecasts are labelled separately."
)
