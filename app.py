"""Octa Financial Control — Dashboard."""
import streamlit as st
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url, set_token_in_url, get_token_from_url
from modules.ui_helpers import (inject_css, sidebar_nav, page_header,
                                 section_label, kpi_card, budget_bar, DARK)
from modules.database import (get_funded_projects, get_project,
                               get_work_packages, get_project_partners,
                               get_project_totals, get_budget_summary_by_partner,
                               get_financial_snapshots, get_budget_matrix)
from modules.charts import (chart_budget_gauge, chart_by_category,
                             chart_spending_donut, chart_partner_comparison,
                             chart_burn_rate, chart_deviation, fig_to_html)
from config import DARK as D, CAT_LABELS

st.set_page_config(page_title="Financial Control — Octa",
                   page_icon="💶", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
auto_login_from_url()
require_auth()

token = st.session_state.get("sso_token","") or get_token_from_url()
if token: set_token_in_url(token)

sidebar_nav()
page_header("Financial Control",
            "Budget consumption, variance and financial reporting per funded project",
            "💶")

org      = st.session_state.get("organisation","")
is_admin = st.session_state.get("role") == "admin"
muted    = D["muted"]; acc = D["accent"]

# ── Project selector ──────────────────────────────────────────────────────────
projects, err = get_funded_projects(org, is_admin)
if err:
    st.error(f"❌ Database error: {err}"); st.stop()
if not projects:
    st.warning("No funded projects found. Set a proposal status to **Funded** in the Proposal Tracker.")
    st.stop()

proj_opts = {}
for p in projects:
    acr = p.get("acronym","").strip() or p["proposal_id"]
    st  = p.get("status","")
    proj_opts[f"{acr} — {p.get('proposal_title','')[:45]}"] = p["proposal_id"]

cur_pid   = st.session_state.get("selected_project_id","")
cur_label = next((l for l,v in proj_opts.items() if v==cur_pid), None)
def_idx   = list(proj_opts.keys()).index(cur_label) if cur_label else 0

sel_label = st.selectbox("Select Project", list(proj_opts.keys()),
                          index=def_idx, key="fin_proj")
sel_pid   = proj_opts[sel_label]
if sel_pid != cur_pid:
    st.session_state["selected_project_id"] = sel_pid
    st.rerun()

proj     = get_project(sel_pid)
acronym  = proj.get("acronym","") or sel_pid
totals   = get_project_totals(sel_pid)
partners = get_budget_summary_by_partner(sel_pid)
snapshots= get_financial_snapshots(sel_pid)

# ── KPI row ───────────────────────────────────────────────────────────────────
section_label("💶 Project Budget at a Glance")
k1,k2,k3,k4,k5 = st.columns(5)
pct = totals["pct_spent"]
kpi_card(k1,"Total Budget",     f"€{totals['planned']:,.0f}",  acc)
kpi_card(k2,"Total Spent",      f"€{totals['actual']:,.0f}",   D["warning"])
kpi_card(k3,"Remaining",        f"€{totals['remaining']:,.0f}",D["success"])
kpi_card(k4,"% Consumed",       f"{pct}%",
         D["danger"] if pct>95 else (D["warning"] if pct>75 else D["success"]))
kpi_card(k5,"Partners",         len(partners),                  D["accent2"])

st.markdown("<br>", unsafe_allow_html=True)

# ── Partner budget bars ───────────────────────────────────────────────────────
section_label("🏛 Budget by Partner")
wp_colors=["#00BCD4","#FF6B35","#6fcf97","#f6cc52",
           "#9b59b6","#3498db","#1abc9c","#e74c3c"]
for i, p in enumerate(partners):
    budget_bar(
        p["partner_name"],
        p["planned"], p["actual"],
        wp_colors[i % len(wp_colors)]
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts row 1 ──────────────────────────────────────────────────────────────
section_label("📈 Financial Charts")
cc1, cc2, cc3 = st.columns(3)

with cc1:
    fig1 = chart_budget_gauge(totals["planned"], totals["actual"],
                               "Overall Budget Consumed")
    st.plotly_chart(fig1, use_container_width=True)

with cc2:
    fig2 = chart_spending_donut(totals["by_category"],
                                "Actual Spending by Category")
    st.plotly_chart(fig2, use_container_width=True)
    if st.button("📥 Export", key="exp_donut"):
        st.download_button("⬇ Download", fig_to_html(fig2).encode(),
                           f"{acronym}_spending_donut.html","text/html", key="dl_donut")

with cc3:
    if snapshots:
        fig3 = chart_burn_rate(snapshots, totals["planned"])
        st.plotly_chart(fig3, use_container_width=True)
        if st.button("📥 Export", key="exp_burn"):
            st.download_button("⬇ Download", fig_to_html(fig3).encode(),
                               f"{acronym}_burn_rate.html","text/html", key="dl_burn")
    else:
        st.info("Burn rate chart will appear once financial snapshots are saved "
                "from the **Enter Spending** page.")

# ── Charts row 2 ──────────────────────────────────────────────────────────────
cc4, cc5 = st.columns(2)

with cc4:
    fig4 = chart_by_category(totals["by_category"],
                              "Planned vs Actual by Cost Category")
    st.plotly_chart(fig4, use_container_width=True)
    if st.button("📥 Export", key="exp_cat"):
        st.download_button("⬇ Download", fig_to_html(fig4).encode(),
                           f"{acronym}_by_category.html","text/html", key="dl_cat")

with cc5:
    fig5 = chart_partner_comparison(partners,
                                    "Budget by Partner — Planned vs Actual")
    st.plotly_chart(fig5, use_container_width=True)
    if st.button("📥 Export", key="exp_partner"):
        st.download_button("⬇ Download", fig_to_html(fig5).encode(),
                           f"{acronym}_partner_comparison.html","text/html", key="dl_part")

# ── Variance ──────────────────────────────────────────────────────────────────
if any(totals["by_category"].get(c,{}).get("actual",0)>0 for c in CAT_LABELS):
    section_label("📊 Variance — Actual vs Planned")
    fig6 = chart_deviation(totals["by_category"])
    st.plotly_chart(fig6, use_container_width=True)
    if st.button("📥 Export Variance Chart", key="exp_dev"):
        st.download_button("⬇ Download", fig_to_html(fig6).encode(),
                           f"{acronym}_variance.html","text/html", key="dl_dev")

# ── Quick nav ─────────────────────────────────────────────────────────────────
section_label("🔗 Quick Access")
qc1,qc2,qc3,qc4 = st.columns(4)
for col, icon, label, page in [
    (qc1,"💰","Enter Spending",  "pages/partner_budget.py"),
    (qc2,"📋","Budget Overview", "pages/overview.py"),
    (qc3,"📈","Forecast",        "pages/forecast.py"),
    (qc4,"📥","Export Report",   "pages/reports.py"),
]:
    col.markdown(
        f"<div style='background:{D["bg2"]};border:1px solid {D["border"]};"
        f"border-radius:10px;padding:0.7rem;text-align:center'>"
        f"<div style='font-size:1.5rem'>{icon}</div>"
        f"<div style='font-size:0.78rem;color:{D["text"]}'>{label}</div></div>",
        unsafe_allow_html=True)
    if col.button("Open", key=f"qfin_{label}", use_container_width=True):
        st.switch_page(page)
