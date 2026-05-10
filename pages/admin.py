"""
Octa Platform — Unified Admin Panel
Copy this file to pages/admin.py in every app — no changes needed.

All 5 functions work in every app:
  1. Approve/reject new user registrations (from ALL apps)
  2. Password reset — admin generates temp password shown ONLY to admin
  3. Working hours approval — approve or return with comment
  4. Manage approved users — edit access, role, status
  5. All users overview — stats, filters, export
"""
import streamlit as st
import json
import secrets
import string
import pandas as pd
from datetime import datetime, timezone

from modules.auth import require_auth, is_admin
from modules.database import db
from modules.ui_helpers import inject_css, sidebar_nav, page_header, DARK

st.set_page_config(page_title="Admin — Octa Platform",
                   page_icon="🛡️", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
sidebar_nav()
require_auth()

if not is_admin():
    st.error("🚫 Access denied. Admin role required.")
    st.stop()

page_header("Admin Panel", "Unified management across all Octa Platform applications", "🛡️")

admin_username = st.session_state.get("username", "admin")

ALL_APPS = [
    "octa_proposals", "octa_hours", "octa_writer",
    "octa_intelligence", "octa_kpi", "octa_partners",
    "octa_social", "octa_communication", "octa_projects", "octa_calendar",
]
APP_LABELS = {
    "octa_proposals":     "📋 Proposal Tracking",
    "octa_hours":         "⏱️ Working Hours",
    "octa_writer":        "📝 Writing App",
    "octa_intelligence":  "🤖 Proposal Intelligence",
    "octa_kpi":           "📊 KPI & Gantt",
    "octa_partners":      "🤝 Partner App",
    "octa_social":        "📱 Social Media",
    "octa_communication": "📧 Partner Communication",
    "octa_projects":      "🏗️ Project Tracking",
    "octa_calendar":      "📅 Calendar",
}

def _parse_apps(u):
    val = u.get("apps_access") or []
    if isinstance(val, str):
        try:    return json.loads(val)
        except: return []
    return list(val)

def _load_users(status_filter=None):
    try:
        q = db().table("octa_users").select("*").order("created_at", desc=True)
        if status_filter:
            q = q.eq("status", status_filter)
        return q.execute().data or []
    except Exception:
        return []

def _load_reset_requests():
    try:
        return db().table("password_reset_requests").select("*") \
                   .eq("status","pending") \
                   .order("requested_at", desc=True).execute().data or []
    except Exception:
        return []

def _load_pending_hours():
    try:
        return db().table("work_logs").select("*") \
                   .eq("status","pending") \
                   .order("log_date", desc=True).execute().data or []
    except Exception:
        return []

def _load_user_map():
    try:
        resp = db().table("octa_users").select("id,first_name,last_name,username").execute()
        return {
            u["id"]: (f"{u.get('first_name','')} {u.get('last_name','')}".strip()
                      or u.get("username",""))
            for u in (resp.data or [])
        }
    except Exception:
        return {}

def _load_proposal_map():
    try:
        resp = db().table("proposals").select("proposal_id,acronym").execute()
        return {
            p["proposal_id"]: (p.get("acronym","").strip() or p["proposal_id"])
            for p in (resp.data or [])
        }
    except Exception:
        return {}

def _gen_temp_password(length=12):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))

def _stripe(color):
    st.markdown(
        f"<div style='height:4px;background:{color};"
        f"border-radius:4px 4px 0 0;margin-bottom:2px'></div>",
        unsafe_allow_html=True
    )

# ── Load pending counts ───────────────────────────────────────────────────────
pending_users  = _load_users("pending")
pending_resets = _load_reset_requests()
pending_hours  = _load_pending_hours()
n_users  = len(pending_users)
n_resets = len(pending_resets)
n_hours  = len(pending_hours)
total_pending = n_users + n_resets + n_hours

if total_pending > 0:
    items = []
    if n_users:  items.append(f"{n_users} new registration{'s' if n_users>1 else ''}")
    if n_resets: items.append(f"{n_resets} password reset{'s' if n_resets>1 else ''}")
    if n_hours:  items.append(f"{n_hours} working hour entr{'ies' if n_hours>1 else 'y'}")
    warn = DARK['warning']
    st.markdown(
        f"<div style='background:rgba(246,204,82,0.15);border:1px solid rgba(246,204,82,0.4);"
        f"border-left:5px solid {warn};border-radius:10px;padding:0.9rem 1.2rem;margin-bottom:1rem'>"
        f"<span style='font-size:1.2rem'>⏳</span> "
        f"<strong style='color:{warn}'>{' and '.join(items)} waiting for your action</strong></div>",
        unsafe_allow_html=True
    )

tab_reg, tab_reset, tab_hours, tab_approved, tab_all = st.tabs([
    f"⏳ Registrations ({n_users})",
    f"🔑 Password Resets ({n_resets})",
    f"⏱️ Working Hours ({n_hours})",
    "✅ Approved Users",
    "👥 All Users",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — New User Registrations
# ══════════════════════════════════════════════════════════════════════════════
with tab_reg:
    if not pending_users:
        st.success("✅ No pending registrations — all clear.")
    else:
        st.caption("Select which apps to grant access to, then Approve or Reject.")
        for u in pending_users:
            uid       = u["id"]
            full_name = (f"{u.get('first_name','')} {u.get('last_name','')}".strip()
                         or u.get("username",""))
            org   = u.get("organisation","—") or "—"
            email = u.get("email","")
            uname = u.get("username","")
            reg_at = str(u.get("created_at",""))[:16]

            _stripe(DARK["warning"])
            with st.expander(
                f"⏳  {full_name}  ·  {uname}  ·  {org}  ·  {email}",
                expanded=True
            ):
                c1,c2,c3,c4 = st.columns(4)
                c1.markdown(f"**Full Name:** {full_name}")
                c2.markdown(f"**Username:** {uname}")
                c3.markdown(f"**Email:** {email}")
                c4.markdown(f"**Organisation:** {org}")
                c1.markdown(f"**Registered:** {reg_at}")

                st.markdown("<br>", unsafe_allow_html=True)
                selected_apps = st.multiselect(
                    "Grant access to:",
                    options=ALL_APPS,
                    default=[a for a in ["octa_proposals"] if a in ALL_APPS],
                    format_func=lambda k: APP_LABELS.get(k,k),
                    key=f"reg_apps_{uid}"
                )

                bc1,bc2,_ = st.columns([1,1,4])
                with bc1:
                    if st.button("✅ Approve", key=f"approve_{uid}",
                                 type="primary", use_container_width=True):
                        try:
                            db().table("octa_users").update({
                                "status":      "approved",
                                "apps_access": selected_apps,
                                "approved_at": datetime.now(timezone.utc).isoformat(),
                                "approved_by": admin_username,
                            }).eq("id", uid).execute()
                            st.success(f"✅ {full_name} approved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with bc2:
                    if st.button("🚫 Reject", key=f"reject_{uid}",
                                 use_container_width=True):
                        try:
                            db().table("octa_users").update({"status":"disabled"}) \
                                .eq("id",uid).execute()
                            st.warning(f"Rejected {full_name}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Password Reset Requests
# ══════════════════════════════════════════════════════════════════════════════
with tab_reset:
    accent = DARK['accent']
    text_c = DARK['text']
    st.markdown(
        f"<div style='background:rgba(0,188,212,0.1);border:1px solid rgba(0,188,212,0.3);"
        f"border-left:4px solid {accent};border-radius:10px;"
        f"padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.88rem'>"
        f"<strong style='color:{accent}'>Secure reset process</strong><br>"
        f"<span style='color:{text_c}'>Generate a temporary password here — "
        f"it appears <b>only on your screen</b>. Share it with the user via phone "
        f"or personal email. The user will be forced to set a new password on login."
        f"</span></div>",
        unsafe_allow_html=True
    )

    if not pending_resets:
        st.success("✅ No pending password reset requests.")
    else:
        for req in pending_resets:
            req_id  = req["id"]
            user_id = req.get("user_id")
            req_at  = str(req.get("requested_at",""))[:16]

            try:
                u_resp = db().table("octa_users").select(
                    "first_name,last_name,username,email,organisation"
                ).eq("id",user_id).execute()
                u = u_resp.data[0] if u_resp.data else {}
            except Exception:
                u = {}

            full_name = (f"{u.get('first_name','')} {u.get('last_name','')}".strip()
                         or u.get("username",""))
            email = u.get("email","")
            org   = u.get("organisation","—") or "—"
            gen_key = f"temp_pw_{req_id}"

            _stripe(DARK["accent"])
            with st.expander(
                f"🔑  {full_name}  ·  {email}  ·  {org}  ·  Requested: {req_at}",
                expanded=True
            ):
                rc1,rc2,rc3 = st.columns(3)
                rc1.markdown(f"**Name:** {full_name}")
                rc2.markdown(f"**Email:** {email}")
                rc3.markdown(f"**Organisation:** {org}")

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("🔐 Generate Temporary Password",
                             key=f"gen_{req_id}", type="primary"):
                    st.session_state[gen_key] = _gen_temp_password()

                if st.session_state.get(gen_key):
                    temp_pw = st.session_state[gen_key]
                    warn_c  = DARK["warning"]
                    bg3_c   = DARK["bg3"]
                    muted_c = DARK["muted"]
                    st.markdown(
                        f"<div style='background:{bg3_c};border:2px solid {warn_c};"
                        f"border-radius:10px;padding:1rem 1.2rem;margin:0.6rem 0'>"
                        f"<div style='color:{warn_c};font-size:0.78rem;font-weight:600;"
                        f"margin-bottom:8px'>⚠️ TEMPORARY PASSWORD — visible only to you. "
                        f"Do NOT share via this system.</div>"
                        f"<div style='font-size:1.8rem;font-family:monospace;font-weight:700;"
                        f"color:white;letter-spacing:0.18em;background:rgba(0,0,0,0.3);"
                        f"padding:0.4rem 0.8rem;border-radius:6px;display:inline-block'>"
                        f"{temp_pw}</div>"
                        f"<div style='color:{muted_c};font-size:0.75rem;margin-top:8px'>"
                        f"Share via phone, personal email, or in person.</div></div>",
                        unsafe_allow_html=True
                    )

                    if st.button("✅ Done — I've shared the password with the user",
                                 key=f"resolve_{req_id}", type="primary",
                                 use_container_width=True):
                        try:
                            db().table("octa_users").update({
                                "temp_password":         temp_pw,
                                "force_password_change": True,
                            }).eq("id",user_id).execute()
                            db().table("password_reset_requests").update({
                                "status":      "completed",
                                "resolved_at": datetime.now(timezone.utc).isoformat(),
                                "resolved_by": admin_username,
                            }).eq("id",req_id).execute()
                            st.session_state.pop(gen_key,None)
                            st.success("✅ Reset completed. User can now log in with the temporary password.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                _,rej_col = st.columns([4,1])
                with rej_col:
                    if st.button("🚫 Reject Request", key=f"rej_reset_{req_id}",
                                 use_container_width=True):
                        try:
                            db().table("password_reset_requests").update({
                                "status":      "rejected",
                                "resolved_at": datetime.now(timezone.utc).isoformat(),
                                "resolved_by": admin_username,
                            }).eq("id",req_id).execute()
                            st.warning("Reset request rejected.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Working Hours Approval
# ══════════════════════════════════════════════════════════════════════════════
with tab_hours:
    if not pending_hours:
        st.success("✅ No pending working hour entries — all clear.")
    else:
        umap     = _load_user_map()
        prop_map = _load_proposal_map()
        st.caption("Review each entry. Approve or return it with a comment to the employee.")

        for log in pending_hours:
            log_id   = log["id"]
            uid      = log.get("user_id")
            emp      = umap.get(uid, f"User {uid}")
            etype    = log.get("entry_type","proposal")
            hours    = float(log.get("hours_worked",0) or 0)
            log_date = str(log.get("log_date",""))[:10]
            start    = str(log.get("start_time",""))[:5]
            end_t    = str(log.get("end_time",""))[:5]
            comment  = log.get("comment","") or ""

            if etype == "project":
                ref       = log.get("project_id","") or "—"
                ref_label = ref
            else:
                ref       = log.get("proposal_id","") or "—"
                ref_label = prop_map.get(ref, ref)

            _stripe(DARK["warning"])
            with st.expander(
                f"⏳  {emp}  ·  {log_date}  ·  {ref_label}  ·  "
                f"{start}–{end_t}  ·  {hours:.2f}h",
                expanded=False
            ):
                r1,r2,r3,r4 = st.columns(4)
                r1.markdown(f"**Employee:** {emp}")
                r2.markdown(f"**Date:** {log_date}")
                r3.markdown(f"**Type:** {etype.capitalize()}")
                r4.markdown(f"**Reference:** {ref_label}")
                r1.markdown(f"**Start:** {start}")
                r2.markdown(f"**End:** {end_t}")
                r3.markdown(f"**Hours:** {hours:.2f}h")

                if comment:
                    muted_c = DARK["muted"]
                    st.markdown(
                        f"<div style='background:rgba(255,255,255,0.05);"
                        f"border-left:3px solid {muted_c};border-radius:6px;"
                        f"padding:0.5rem 0.8rem;margin:0.4rem 0;font-size:0.85rem'>"
                        f"<em>💬 {comment}</em></div>",
                        unsafe_allow_html=True
                    )

                adm_cmt = st.text_input(
                    "Admin comment (required when returning)",
                    key=f"h_cmt_{log_id}",
                    placeholder="Optional for approval · Required for return"
                )
                hc1,hc2,_ = st.columns([1,1,4])
                with hc1:
                    if st.button("✅ Approve", key=f"h_app_{log_id}",
                                 type="primary", use_container_width=True):
                        try:
                            db().table("work_logs").update({
                                "status":        "approved",
                                "approved_by":   admin_username,
                                "admin_comment": adm_cmt,
                                "approved_at":   datetime.now(timezone.utc).isoformat(),
                                "updated_at":    datetime.now(timezone.utc).isoformat(),
                            }).eq("id",log_id).execute()
                            st.success(f"✅ Approved {hours:.2f}h for {emp}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with hc2:
                    if st.button("↩️ Return", key=f"h_ret_{log_id}",
                                 use_container_width=True):
                        if not adm_cmt.strip():
                            st.warning("Please add a comment explaining the return.")
                        else:
                            try:
                                db().table("work_logs").update({
                                    "status":        "returned",
                                    "approved_by":   admin_username,
                                    "admin_comment": adm_cmt,
                                    "approved_at":   datetime.now(timezone.utc).isoformat(),
                                    "updated_at":    datetime.now(timezone.utc).isoformat(),
                                }).eq("id",log_id).execute()
                                st.warning(f"↩️ Returned to {emp}.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Approved Users (manage access)
# ══════════════════════════════════════════════════════════════════════════════
with tab_approved:
    approved = _load_users("approved")
    if not approved:
        st.info("No approved users yet.")
    else:
        for u in approved:
            uid       = u["id"]
            apps_val  = _parse_apps(u)
            full_name = (f"{u.get('first_name','')} {u.get('last_name','')}".strip()
                         or u.get("username",""))
            apps_str  = ", ".join(APP_LABELS.get(a,a) for a in apps_val) or "no apps"

            _stripe(DARK["success"])
            with st.expander(f"✅  {full_name}  ·  {u.get('username','')}  ·  {apps_str}"):
                ec1,ec2,ec3 = st.columns(3)
                ec1.markdown(f"**Email:** {u.get('email','')}")
                ec2.markdown(f"**Organisation:** {u.get('organisation','—') or '—'}")
                ec3.markdown(f"**Role:** {u.get('role','user')}")
                ec1.markdown(f"**Last login:** {str(u.get('last_login','—'))[:16]}")
                ec2.markdown(f"**Approved:** {str(u.get('approved_at','—'))[:10]}")

                new_apps = st.multiselect(
                    "App access:", ALL_APPS,
                    default=[a for a in apps_val if a in ALL_APPS],
                    format_func=lambda k: APP_LABELS.get(k,k),
                    key=f"edit_apps_{uid}"
                )
                new_role = st.selectbox(
                    "Role:", ["user","admin"],
                    index=1 if u.get("role")=="admin" else 0,
                    key=f"role_{uid}"
                )
                sc1,sc2,_ = st.columns([1,1,4])
                with sc1:
                    if st.button("💾 Save", key=f"save_{uid}", use_container_width=True):
                        try:
                            db().table("octa_users").update({
                                "apps_access": new_apps,
                                "role":        new_role,
                            }).eq("id",uid).execute()
                            st.success("Saved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with sc2:
                    if st.button("🚫 Disable", key=f"disable_{uid}",
                                 use_container_width=True):
                        try:
                            db().table("octa_users").update({"status":"disabled"}) \
                                .eq("id",uid).execute()
                            st.warning("Account disabled.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — All Users overview
# ══════════════════════════════════════════════════════════════════════════════
with tab_all:
    all_users = _load_users()
    if not all_users:
        st.info("No users found.")
    else:
        total      = len(all_users)
        n_approved = sum(1 for u in all_users if u.get("status")=="approved")
        n_pend     = sum(1 for u in all_users if u.get("status")=="pending")
        n_dis      = sum(1 for u in all_users if u.get("status")=="disabled")
        n_adm      = sum(1 for u in all_users if u.get("role")=="admin")

        k1,k2,k3,k4,k5 = st.columns(5)
        for col,label,val,color in [
            (k1,"Total Users", total,      DARK["accent"]),
            (k2,"Approved",    n_approved, DARK["success"]),
            (k3,"Pending",     n_pend,     DARK["warning"]),
            (k4,"Disabled",    n_dis,      DARK["danger"]),
            (k5,"Admins",      n_adm,      DARK["accent2"]),
        ]:
            bg2 = DARK["bg2"]; muted = DARK["muted"]
            col.markdown(
                f"<div style='background:{bg2};border-top:3px solid {color};"
                f"border:1px solid {color}44;border-radius:10px;"
                f"padding:0.9rem;text-align:center'>"
                f"<div style='font-size:1.8rem;font-weight:700;color:{color}'>{val}</div>"
                f"<div style='font-size:0.78rem;color:{muted}'>{label}</div></div>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        fc1,fc2,fc3 = st.columns(3)
        with fc1:
            f_status = st.selectbox("Status",["All","approved","pending","disabled"],
                                     key="all_status")
        with fc2:
            f_role = st.selectbox("Role",["All","user","admin"],key="all_role")
        with fc3:
            f_search = st.text_input("Search name / email / org",
                                      placeholder="Type to search…",key="all_search")

        filtered = all_users
        if f_status!="All": filtered=[u for u in filtered if u.get("status")==f_status]
        if f_role!="All":   filtered=[u for u in filtered if u.get("role")==f_role]
        if f_search:
            q=f_search.lower()
            filtered=[u for u in filtered if
                q in f"{u.get('first_name','')} {u.get('last_name','')}".lower() or
                q in (u.get("email","") or "").lower() or
                q in (u.get("organisation","") or "").lower() or
                q in (u.get("username","") or "").lower()]

        muted_c = DARK["muted"]; text_c = DARK["text"]
        st.markdown(
            f"<p style='color:{muted_c};font-size:0.84rem'>"
            f"Showing <strong style='color:{text_c}'>{len(filtered)}</strong>"
            f" of {total} users</p>",
            unsafe_allow_html=True
        )

        STATUS_COLORS={"approved":DARK["success"],"pending":DARK["warning"],"disabled":DARK["danger"]}
        STATUS_ICONS={"approved":"✅","pending":"⏳","disabled":"🚫"}

        for u in filtered:
            uid       = u["id"]
            full_name = (f"{u.get('first_name','')} {u.get('last_name','')}".strip()
                         or u.get("username",""))
            status    = u.get("status","")
            role      = u.get("role","user")
            org       = u.get("organisation","—") or "—"
            email     = u.get("email","")
            username  = u.get("username","")
            registered= str(u.get("created_at",""))[:10]
            last_login= str(u.get("last_login",""))[:16] if u.get("last_login") else "Never"
            apps_val  = _parse_apps(u)
            s_color   = STATUS_COLORS.get(status,DARK["muted"])
            s_icon    = STATUS_ICONS.get(status,"❓")
            role_badge= "🛡️ Admin" if role=="admin" else "👤 User"

            _stripe(s_color)
            with st.expander(
                f"{s_icon}  {full_name}  ·  {org}  ·  {role_badge}  ·  {status.upper()}",
                expanded=False
            ):
                d1,d2,d3,d4 = st.columns(4)
                d1.markdown(f"**Username:** {username}")
                d2.markdown(f"**Email:** {email}")
                d3.markdown(f"**Organisation:** {org}")
                d4.markdown(f"**Role:** {role_badge}")
                d1.markdown(f"**Status:** {s_icon} {status}")
                d2.markdown(f"**Registered:** {registered}")
                d3.markdown(f"**Last Login:** {last_login}")
                d4.markdown(f"**Approved by:** {u.get('approved_by','—') or '—'}")

                # App chips
                muted_c2 = DARK["muted"]; acc = DARK["accent"]
                st.markdown(
                    f"<div style='margin:0.5rem 0 0.3rem;font-size:0.78rem;"
                    f"color:{muted_c2};font-weight:600;text-transform:uppercase;"
                    f"letter-spacing:0.06em'>App Access</div>",
                    unsafe_allow_html=True
                )
                if apps_val:
                    chips=" ".join(
                        f"<span style='background:{acc}22;color:{acc};"
                        f"border:1px solid {acc}44;padding:2px 9px;"
                        f"border-radius:12px;font-size:0.78rem;margin-right:3px'>"
                        f"{APP_LABELS.get(a,a)}</span>"
                        for a in apps_val
                    )
                    st.markdown(chips,unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<span style='color:{muted_c2};font-size:0.84rem'>"
                        f"No apps assigned</span>",
                        unsafe_allow_html=True
                    )

                st.markdown("---")
                ea1,ea2,ea3 = st.columns([3,1,1])
                with ea1:
                    new_apps=st.multiselect(
                        "Edit app access:", ALL_APPS,
                        default=[a for a in apps_val if a in ALL_APPS],
                        format_func=lambda k: APP_LABELS.get(k,k),
                        key=f"all_apps_{uid}"
                    )
                with ea2:
                    new_role=st.selectbox(
                        "Role:",["user","admin"],
                        index=1 if role=="admin" else 0,
                        key=f"all_role_{uid}"
                    )
                with ea3:
                    opts=["approved","pending","disabled"]
                    new_status=st.selectbox(
                        "Status:",opts,
                        index=opts.index(status) if status in opts else 0,
                        key=f"all_stat_{uid}"
                    )

                if st.button("💾 Save Changes",key=f"all_save_{uid}",type="primary"):
                    try:
                        db().table("octa_users").update({
                            "apps_access": new_apps,
                            "role":        new_role,
                            "status":      new_status,
                        }).eq("id",uid).execute()
                        st.success("Saved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("---")
        df_export=pd.DataFrame([{
            "Name":         f"{u.get('first_name','')} {u.get('last_name','')}".strip(),
            "Username":     u.get("username",""),
            "Email":        u.get("email",""),
            "Organisation": u.get("organisation","—") or "—",
            "Status":       u.get("status",""),
            "Role":         u.get("role",""),
            "Apps":         ", ".join(APP_LABELS.get(a,a) for a in _parse_apps(u)) or "—",
            "Registered":   str(u.get("created_at",""))[:10],
            "Last Login":   str(u.get("last_login",""))[:16] if u.get("last_login") else "Never",
        } for u in all_users])
        st.download_button(
            "📥 Export All Users CSV",
            data=df_export.to_csv(index=False),
            file_name="octa_users.csv",
            mime="text/csv",
        )
