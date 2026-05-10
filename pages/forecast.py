"""Octa Financial Control — Forecast & Burn Rate."""
import streamlit as st
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (inject_css, sidebar_nav, page_header,
                                 section_label, kpi_card, DARK)
from modules.database import (get_project, get_project_partners,
                               get_project_totals, get_financial_snapshots,
                               get_budget_summary_by_partner)
from modules.charts import chart_burn_rate, chart_partner_comparison, fig_to_html
from config import DARK as D

st.set_page_config(page_title="Forecast — Octa", page_icon="📈",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id","")
if not sel_pid: st.switch_page("app.py"); st.stop()

proj    = get_project(sel_pid)
acronym = proj.get("acronym","") or sel_pid
page_header("Budget Forecast",
            f"{acronym} — Burn rate, spend trajectory and completion forecast", "📈")
if st.button("← Dashboard"): st.switch_page("app.py")

muted    = D["muted"]; acc = D["accent"]
totals   = get_project_totals(sel_pid)
partners = get_project_partners(sel_pid)
summaries= get_budget_summary_by_partner(sel_pid)
snaps    = get_financial_snapshots(sel_pid)

proj_start = proj.get("project_start_date")
proj_dur   = int(proj.get("project_duration_months") or 36)

# ── Elapsed periods ───────────────────────────────────────────────────────────
current_period = len(snaps) if snaps else 1
remaining_periods = max(0, proj_dur - current_period) if proj_dur else None

# ── Burn rate calculation ─────────────────────────────────────────────────────
total_planned = totals["planned"]
total_actual  = totals["actual"]
avg_per_period= total_actual / current_period if current_period else 0
forecast_total= total_actual + avg_per_period * remaining_periods if remaining_periods is not None else None
forecast_variance = forecast_total - total_planned if forecast_total else None

section_label("📊 Forecast Summary")
k1,k2,k3,k4 = st.columns(4)
kpi_card(k1,"Avg Spend / Period",  f"€{avg_per_period:,.0f}", acc)
kpi_card(k2,"Remaining Periods",   remaining_periods if remaining_periods is not None else "—", D["warning"])
kpi_card(k3,"Forecast Total Spend",
         f"€{forecast_total:,.0f}" if forecast_total else "—",
         D["danger"] if forecast_total and forecast_total>total_planned else D["success"])
kpi_card(k4,"Projected Variance",
         f"€{forecast_variance:+,.0f}" if forecast_variance is not None else "—",
         D["danger"] if forecast_variance and forecast_variance>0 else D["success"],
         "over budget" if forecast_variance and forecast_variance>0 else "under budget")

st.markdown("<br>", unsafe_allow_html=True)

# ── Burn rate chart ───────────────────────────────────────────────────────────
section_label("📈 Budget Burn Rate")
if snaps:
    fig1 = chart_burn_rate(snaps, total_planned,
                            f"{acronym} — Cumulative Budget Consumption")
    st.plotly_chart(fig1, use_container_width=True)
    ec1, ec2 = st.columns(2)
    with ec1:
        if st.button("📥 Export Burn Rate", key="exp_burn"):
            st.download_button("⬇ Download HTML",
                               fig_to_html(fig1).encode(),
                               f"{acronym}_burn_rate.html","text/html", key="dl_burn")
    with ec2:
        st.caption(
            "Dashed line = budget ceiling | Solid = actual cumulative | "
            "Dotted = linear forecast based on current burn rate"
        )
else:
    bg2 = D["bg2"]; border = D["border"]
    st.markdown(
        f"<div style='background:{bg2};border:1px solid {border};border-radius:10px;"
        f"padding:2rem;text-align:center;color:{muted}'>"
        f"Burn rate chart appears after entering spending on the "
        f"<strong>Enter Spending</strong> page for at least 2 reporting periods.</div>",
        unsafe_allow_html=True)

# ── Partner-level forecasts ───────────────────────────────────────────────────
section_label("🏛 Partner-Level Forecast")
for p in summaries:
    pid   = p["partner_id"]
    pname = p["partner_name"]
    p_snaps = get_financial_snapshots(sel_pid, pid)
    p_avg   = p["actual"] / len(p_snaps) if p_snaps else 0
    p_fc    = p["actual"] + p_avg * remaining_periods if remaining_periods is not None else None
    p_var   = p_fc - p["planned"] if p_fc else None
    pct     = p["pct_spent"]
    color   = D["danger"] if pct>95 else (D["warning"] if pct>75 else D["success"])

    bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
    st.markdown(
        f"<div style='background:{bg2};border:1px solid {border};"
        f"border-left:4px solid {color};border-radius:10px;"
        f"padding:0.8rem 1rem;margin-bottom:0.5rem'>"
        f"<div style='display:flex;flex-wrap:wrap;gap:2rem;align-items:center'>"
        f"<strong style='color:{txt}'>{pname}</strong>"
        f"<span style='color:{muted};font-size:0.82rem'>"
        f"Spent: <strong style='color:{color}'>€{p['actual']:,.0f}</strong> / €{p['planned']:,.0f} ({pct}%)</span>"
        + (f"<span style='color:{muted};font-size:0.82rem'>Avg/period: €{p_avg:,.0f}</span>" if p_avg else "")
        + (f"<span style='color:{D['danger'] if p_var and p_var>0 else D['success']};font-size:0.82rem'>"
           f"Forecast total: €{p_fc:,.0f} (<strong>€{p_var:+,.0f}</strong>)</span>"
           if p_fc else "")
        + f"</div></div>", unsafe_allow_html=True)
