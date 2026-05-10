"""Octa Financial Control — Budget Overview (all partners × all WPs)."""
import streamlit as st
from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (inject_css, sidebar_nav, page_header,
                                 section_label, budget_bar, DARK)
from modules.database import (get_project, get_work_packages,
                               get_project_partners, get_budget_matrix,
                               get_budget_summary_by_partner, get_project_totals)
from modules.charts import (chart_by_category, chart_wp_breakdown,
                             chart_partner_comparison, fig_to_html)
from config import COST_CATEGORIES, CAT_LABELS, CAT_KEYS, DARK as D

st.set_page_config(page_title="Budget Overview — Octa", page_icon="📋",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id","")
if not sel_pid: st.switch_page("app.py"); st.stop()

proj    = get_project(sel_pid)
acronym = proj.get("acronym","") or sel_pid
page_header("Budget Overview", f"{acronym} — Consolidated view by partner and WP", "📋")
if st.button("← Dashboard"): st.switch_page("app.py")

D2       = D
muted    = D2["muted"]; acc = D2["accent"]
wps      = get_work_packages(sel_pid)
partners = get_project_partners(sel_pid)
matrix   = get_budget_matrix(sel_pid)
summaries= get_budget_summary_by_partner(sel_pid)
totals   = get_project_totals(sel_pid)
WP_COLORS= ["#00BCD4","#FF6B35","#6fcf97","#f6cc52","#9b59b6","#3498db","#1abc9c","#e74c3c"]

# ── Project totals header ─────────────────────────────────────────────────────
section_label("📊 Project Totals")
bg2 = D2["bg2"]; border = D2["border"]; txt = D2["text"]
for c in (D2["success"],D2["warning"],D2["danger"],acc):
    pass  # suppress unused warning
pct = totals["pct_spent"]
c1,c2,c3,c4 = st.columns(4)
for col, label, val, color in [
    (c1,"Total Planned",  f"€{totals['planned']:,.0f}",   acc),
    (c2,"Total Spent",    f"€{totals['actual']:,.0f}",    D2["warning"]),
    (c3,"Remaining",      f"€{totals['remaining']:,.0f}", D2["success"]),
    (c4,"% Consumed",     f"{pct}%",
     D2["danger"] if pct>95 else (D2["warning"] if pct>75 else D2["success"])),
]:
    col.markdown(
        f"<div style='background:{bg2};border-top:3px solid {color};"
        f"border:1px solid {color}44;border-radius:10px;"
        f"padding:0.7rem;text-align:center'>"
        f"<div style='font-size:1.5rem;font-weight:700;color:{color}'>{val}</div>"
        f"<div style='font-size:0.75rem;color:{muted}'>{label}</div></div>",
        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Partner × Category matrix ─────────────────────────────────────────────────
section_label("🏛 Partner Budget Matrix")
if not summaries:
    st.info("No budget data entered yet. Go to **Enter Spending** to start.")
else:
    fig_comp = chart_partner_comparison(summaries)
    st.plotly_chart(fig_comp, use_container_width=True)
    if st.button("📥 Export", key="exp_comp"):
        st.download_button("⬇ Download HTML",
                           fig_to_html(fig_comp, "Partner Budget Comparison").encode(),
                           f"{acronym}_partner_budget.html","text/html", key="dl_comp")

    for i, p in enumerate(summaries):
        pid   = p["partner_id"]
        pname = p["partner_name"]
        with st.expander(
            f"🏛 {pname}  ·  Spent: €{p['actual']:,.0f} / €{p['planned']:,.0f}  ({p['pct_spent']}%)",
            expanded=False
        ):
            pc1, pc2 = st.columns([2,1])
            with pc1:
                fig_p = chart_by_category(p["by_category"],
                                          f"{pname} — by Category")
                st.plotly_chart(fig_p, use_container_width=True)
            with pc2:
                # Category breakdown table
                for cat_key, cat_label in COST_CATEGORIES:
                    cats = p["by_category"].get(cat_key,{})
                    pl   = cats.get("planned",0)
                    ac   = cats.get("actual",0)
                    pct2 = round(ac/pl*100,1) if pl else 0
                    col2 = D2["success"] if pct2<75 else (D2["warning"] if pct2<95 else D2["danger"])
                    st.markdown(
                        f"<div style='font-size:0.8rem;display:flex;justify-content:space-between;"
                        f"margin-bottom:2px'>"
                        f"<span style='color:{muted}'>{cat_label[:20]}</span>"
                        f"<span style='color:{col2}'>€{ac:,.0f} / €{pl:,.0f}</span></div>",
                        unsafe_allow_html=True)

# ── WP breakdown ──────────────────────────────────────────────────────────────
section_label("📦 Budget by Work Package")
fig_wp = chart_wp_breakdown(matrix, wps)
st.plotly_chart(fig_wp, use_container_width=True)
if st.button("📥 Export WP chart", key="exp_wp"):
    st.download_button("⬇ Download HTML",
                       fig_to_html(fig_wp, "Budget by WP").encode(),
                       f"{acronym}_budget_wp.html","text/html", key="dl_wp")

# ── Category overview ─────────────────────────────────────────────────────────
section_label("📊 Project-Level Category Breakdown")
fig_cat = chart_by_category(totals["by_category"], "All Categories — Project Total")
st.plotly_chart(fig_cat, use_container_width=True)
if st.button("📥 Export Category chart", key="exp_cat_ov"):
    st.download_button("⬇ Download HTML",
                       fig_to_html(fig_cat, "Budget by Category").encode(),
                       f"{acronym}_budget_category.html","text/html", key="dl_cat_ov")
