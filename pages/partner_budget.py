"""Octa Financial Control — Enter Actual Spending."""
import streamlit as st
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (inject_css, sidebar_nav, page_header,
                                 section_label, budget_bar, DARK)
from modules.database import (get_project, get_work_packages,
                               get_project_partners, get_budget_matrix,
                               upsert_budget_entry, update_actual_spent,
                               get_overhead_settings, save_overhead_setting,
                               save_financial_snapshot, get_budget_summary_by_partner)
from modules.charts import chart_by_category, chart_wp_breakdown, fig_to_html
from config import (COST_CATEGORIES, CAT_LABELS, CAT_KEYS,
                    OVERHEAD_BASE_CATS, DARK as D)

st.set_page_config(page_title="Enter Spending — Octa", page_icon="💰",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id","")
if not sel_pid:
    st.switch_page("app.py"); st.stop()

proj    = get_project(sel_pid)
acronym = proj.get("acronym","") or sel_pid
page_header("Enter Spending",
            f"{acronym} — Update actual spending per partner, per WP, per cost category",
            "💰")
if st.button("← Dashboard"): st.switch_page("app.py")

muted = D["muted"]; acc = D["accent"]
user_id = st.session_state.get("user_id")

wps      = get_work_packages(sel_pid)
partners = get_project_partners(sel_pid)
matrix   = get_budget_matrix(sel_pid)
oh_pcts  = get_overhead_settings(sel_pid)

if not wps:
    st.info("No Work Packages defined for this project."); st.stop()
if not partners:
    st.info("No partners found for this project."); st.stop()

# ── Overhead settings ─────────────────────────────────────────────────────────
section_label("⚙️ Overhead Rate Settings")
st.markdown(
    f"<p style='color:{muted};font-size:0.84rem'>"
    f"Overhead is calculated automatically as a percentage of the sum of "
    f"<strong>Personnel + Travel + Equipment + Other Goods & Services</strong>. "
    f"Set the rate per partner.</p>",
    unsafe_allow_html=True)

oh_cols = st.columns(min(len(partners), 4))
for i, p in enumerate(partners):
    pid  = p["id"]
    name = p.get("short_name","") or p.get("full_name","")[:20]
    cur  = oh_pcts.get(pid, 25.0)
    with oh_cols[i % 4]:
        new_oh = st.number_input(f"{name} overhead %",
                                  min_value=0.0, max_value=100.0,
                                  value=cur, step=0.5, format="%.1f",
                                  key=f"oh_{pid}")
        if new_oh != cur:
            save_overhead_setting(sel_pid, pid, new_oh)

st.markdown("<br>", unsafe_allow_html=True)

# ── Partner selector ──────────────────────────────────────────────────────────
section_label("💰 Enter Actual Spending")
partner_opts = {
    (p.get("short_name","") or p.get("full_name","")[:25]): p["id"]
    for p in partners
}
sel_partner_name = st.selectbox("Select Partner", list(partner_opts.keys()),
                                 key="sel_partner")
sel_pid_p = partner_opts[sel_partner_name]

# ── WP tabs ───────────────────────────────────────────────────────────────────
wp_tabs = st.tabs([f"📦 {w.get('wp_number','')}: {w.get('wp_title','')[:25]}"
                   for w in wps])

for wp_idx, (wp, tab) in enumerate(zip(wps, wp_tabs)):
    with tab:
        wid     = wp["wp_id"]
        wp_num  = wp.get("wp_number","")
        wp_data = matrix.get(sel_pid_p,{}).get(wid,{})
        oh_pct  = oh_pcts.get(sel_pid_p, 25.0) / 100

        tc1, tc2 = st.columns([3,2])

        with tc1:
            with st.form(f"spend_form_{sel_pid_p}_{wid}"):
                st.markdown(
                    f"<strong style='color:{acc}'>{wp_num}: {wp.get('wp_title','')}</strong>",
                    unsafe_allow_html=True)

                entries_to_save = {}
                base_actual_sum = 0.0
                base_planned_sum= 0.0

                for cat_key, cat_label in COST_CATEGORIES:
                    if cat_key == "overhead":
                        continue   # shown read-only below

                    cat_data = wp_data.get(cat_key, {})
                    planned  = cat_data.get("planned", 0.0)
                    actual   = cat_data.get("actual",  0.0)
                    entry_id = cat_data.get("entry_id")

                    # Colour the input based on spend level
                    pct = round(actual/planned*100,1) if planned else 0
                    s_col = D["success"] if pct<75 else (D["warning"] if pct<95 else D["danger"])

                    col_l, col_p, col_a = st.columns([3,2,2])
                    with col_l:
                        st.markdown(
                            f"<div style='padding-top:1.8rem;font-size:0.84rem;"
                            f"color:{D["text"]}'>{cat_label}</div>",
                            unsafe_allow_html=True)
                    with col_p:
                        st.number_input(f"Planned (€)",
                                         value=float(planned),
                                         key=f"pl_{sel_pid_p}_{wid}_{cat_key}",
                                         format="%.2f", disabled=True,
                                         label_visibility="visible")
                    with col_a:
                        new_actual = st.number_input(
                            f"Actual (€)",
                            value=float(actual),
                            min_value=0.0,
                            key=f"ac_{sel_pid_p}_{wid}_{cat_key}",
                            format="%.2f",
                            label_visibility="visible"
                        )

                    entries_to_save[cat_key] = {
                        "planned":  planned,
                        "actual":   new_actual,
                        "entry_id": entry_id,
                    }

                    if cat_key in OVERHEAD_BASE_CATS:
                        base_actual_sum  += new_actual
                        base_planned_sum += planned

                # Auto-calculated overhead (read-only display)
                oh_planned = round(base_planned_sum * oh_pct, 2)
                oh_actual  = round(base_actual_sum  * oh_pct, 2)
                success = D["success"]; muted2 = D["muted"]
                st.markdown(
                    f"<div style='background:{D["bg3"]};border-left:3px solid {D["muted"]};"
                    f"border-radius:6px;padding:0.5rem 0.8rem;margin-top:0.3rem;font-size:0.84rem'>"
                    f"<strong style='color:{D["muted"]}'>7. Overhead ({oh_pct*100:.1f}%)</strong>"
                    f"<span style='color:{D["muted"]};margin-left:1rem'>"
                    f"Planned: <strong>€{oh_planned:,.2f}</strong>"
                    f" · Actual: <strong style='color:{D["success"]}'>€{oh_actual:,.2f}</strong>"
                    f"</span></div>",
                    unsafe_allow_html=True)

                period = st.number_input("Reporting Period", min_value=1, max_value=20,
                                          value=1, key=f"per_{sel_pid_p}_{wid}")
                notes  = st.text_input("Notes (optional)", key=f"notes_{sel_pid_p}_{wid}",
                                        placeholder="e.g. Includes conference in Month 6")

                if st.form_submit_button("💾 Save Spending", type="primary",
                                          use_container_width=True):
                    saved = 0
                    for cat_key, vals in entries_to_save.items():
                        if vals["entry_id"]:
                            ok = update_actual_spent(
                                vals["entry_id"], vals["actual"],
                                notes, period, user_id
                            )
                        else:
                            # Create entry if it doesn't exist yet
                            ok, _ = upsert_budget_entry({
                                "proposal_id":        sel_pid,
                                "wp_id":              wid,
                                "partner_id":         sel_pid_p,
                                "cost_category":      cat_key,
                                "planned_amount":     vals["planned"],
                                "actual_spent_amount":vals["actual"],
                                "notes":              notes,
                                "reported_period":    period,
                            })
                        if ok: saved += 1

                    # Save snapshot
                    by_cat_snap = {
                        k: {"planned":v["planned"],"actual":v["actual"]}
                        for k,v in entries_to_save.items()
                    }
                    by_cat_snap["overhead"] = {
                        "planned": oh_planned, "actual": oh_actual
                    }
                    partner_summary = get_budget_summary_by_partner(sel_pid)
                    p_total_planned = next(
                        (p["planned"] for p in partner_summary if p["partner_id"]==sel_pid_p), 0
                    )
                    save_financial_snapshot(sel_pid, sel_pid_p, period,
                                            by_cat_snap, p_total_planned, notes)

                    if saved > 0:
                        st.success(f"✅ Saved {saved} entries + snapshot for Period {period}!")
                        st.rerun()
                    else:
                        st.error("❌ Save failed — check Supabase permissions.")

        with tc2:
            st.markdown(f"<br>", unsafe_allow_html=True)
            # Current state summary for this WP/partner
            if wp_data:
                total_p = sum(wp_data.get(c,{}).get("planned",0) for c in CAT_KEYS if c!="overhead")
                total_p += oh_planned
                total_a = sum(wp_data.get(c,{}).get("actual",0)  for c in CAT_KEYS if c!="overhead")
                total_a += oh_actual
                pct_wp  = round(total_a/total_p*100,1) if total_p else 0
                pct_col = D["success"] if pct_wp<75 else (D["warning"] if pct_wp<95 else D["danger"])

                bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
                st.markdown(
                    f"<div style='background:{bg2};border:1px solid {border};"
                    f"border-radius:10px;padding:1rem'>"
                    f"<div style='font-size:0.75rem;color:{muted};margin-bottom:0.5rem'>"
                    f"WP {wp_num} — {sel_partner_name}</div>"
                    f"<div style='font-size:1.6rem;font-weight:700;color:{pct_col}'>{pct_wp}%</div>"
                    f"<div style='font-size:0.78rem;color:{muted}'>"
                    f"€{total_a:,.0f} spent of €{total_p:,.0f}</div>"
                    f"<div style='background:{D["bg3"]};border-radius:4px;height:8px;margin-top:8px'>"
                    f"<div style='background:{pct_col};width:{min(pct_wp,100)}%;height:8px;border-radius:4px'></div>"
                    f"</div></div>",
                    unsafe_allow_html=True)

                # Mini category chart
                by_cat_display = {
                    k: {"planned": wp_data.get(k,{}).get("planned",0),
                        "actual":  wp_data.get(k,{}).get("actual",0)}
                    for k in CAT_KEYS if k != "overhead"
                }
                by_cat_display["overhead"] = {
                    "planned": oh_planned, "actual": oh_actual
                }
                fig_mini = chart_by_category(
                    by_cat_display,
                    f"{wp_num} — {sel_partner_name}"
                )
                st.plotly_chart(fig_mini, use_container_width=True)
