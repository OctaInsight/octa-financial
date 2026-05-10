"""
Octa Platform — Login Page
Sign In · Register · Reset Password
No email required — all flows work on-screen.
"""
import streamlit as st
from modules.ui_helpers import inject_css, sidebar_nav, DARK
from modules.auth import (
    login_user, register_user, set_session, is_authenticated,
    generate_reset_token, reset_password_with_token,
)

st.set_page_config(
    page_title="Login — Octa Platform",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_css()
sidebar_nav()

if is_authenticated():
    st.switch_page("app.py")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:2rem 0 1.5rem">
    <div style="font-size:3.2rem">📋</div>
    <h1 style="color:white;font-size:2rem;font-weight:800;
               margin:0.5rem 0 0.2rem;letter-spacing:-1px">
        Octa Platform
    </h1>
    <p style="color:{DARK['muted']};font-size:0.95rem;margin:0">
        Proposal tracking &amp; partner management
    </p>
</div>
""", unsafe_allow_html=True)

tab_login, tab_register, tab_reset = st.tabs(
    ["🔑  Sign In", "✨  Register", "🔓  Reset Password"]
)

# ─── SIGN IN ──────────────────────────────────────────────────────────────────
with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    li_email = st.text_input("Email address", key="li_email",
                              placeholder="you@example.com")
    li_pass  = st.text_input("Password", type="password", key="li_pass",
                              placeholder="Your password")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Sign In →", type="primary",
                 use_container_width=True, key="btn_login"):
        if not li_email or not li_pass:
            st.warning("Please fill in both fields.")
        else:
            ok, msg, user = login_user(li_email, li_pass)
            if ok:
                set_session(user)
                st.switch_page("app.py")
            else:
                st.error(f"❌ {msg}")

# ─── REGISTER ─────────────────────────────────────────────────────────────────
with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:rgba(0,188,212,0.1);border:1px solid rgba(0,188,212,0.3);
                border-left:4px solid {DARK['accent']};border-radius:10px;
                padding:0.9rem 1.1rem;margin-bottom:1rem;font-size:0.88rem">
        <strong style="color:{DARK['accent']}">How it works</strong><br>
        <span style="color:{DARK['text']}">
            1. Fill in the form below and submit<br>
            2. An admin will review and activate your account<br>
            3. Come back and sign in once approved
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Name fields
    rc1, rc2 = st.columns(2)
    with rc1:
        reg_first = st.text_input("First name *", key="reg_first",
                                   placeholder="Maria")
    with rc2:
        reg_last  = st.text_input("Last name *", key="reg_last",
                                   placeholder="Rossi")

    reg_username = st.text_input("Username *", key="reg_uname",
                                  placeholder="mariarossi  (min 3 characters)")
    reg_email    = st.text_input("Email address *", key="reg_email",
                                  placeholder="you@example.com")

    # ── Organisation dropdown (from partners table) ────────────────────────────
    OTHER_ORG = "➕  My organisation is not in the list"
    try:
        from modules.database import get_all_partners
        partner_names = [p["full_name"] for p in get_all_partners()
                         if p.get("full_name")]
    except Exception:
        partner_names = []

    org_options    = ["— Select your organisation —"] + sorted(partner_names) + [OTHER_ORG]
    reg_org_select = st.selectbox(
        "Organisation / Partner *",
        options=org_options,
        key="reg_org_select",
        help="Select your organisation. If not listed, choose the last option."
    )

    reg_org_custom = ""
    if reg_org_select == OTHER_ORG:
        reg_org_custom = st.text_input(
            "Enter your organisation name *",
            key="reg_org_custom",
            placeholder="Full name of your organisation",
        )
        st.markdown(
            f"<p style='color:{DARK['muted']};font-size:0.8rem;margin-top:-0.4rem'>"
            f"The admin will add your organisation to the partners list after approval.</p>",
            unsafe_allow_html=True
        )

    def _org_value():
        if reg_org_select == OTHER_ORG:
            return reg_org_custom.strip()
        if reg_org_select.startswith("—"):
            return ""
        return reg_org_select

    # Password
    rc3, rc4 = st.columns(2)
    with rc3:
        reg_pass  = st.text_input("Password *", type="password",
                                   key="reg_pass",
                                   placeholder="Min 8 characters")
    with rc4:
        reg_pass2 = st.text_input("Confirm password *", type="password",
                                   key="reg_pass2",
                                   placeholder="Repeat password")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Submit Registration →", type="primary",
                 use_container_width=True, key="btn_register"):
        org_val = _org_value()

        if reg_pass != reg_pass2:
            st.error("❌ Passwords do not match.")
        elif not all([reg_first, reg_last, reg_username, reg_email, reg_pass]):
            st.warning("Please fill in all required fields.")
        elif reg_org_select.startswith("—"):
            st.warning("Please select your organisation.")
        elif reg_org_select == OTHER_ORG and not reg_org_custom.strip():
            st.warning("Please enter your organisation name.")
        else:
            ok, msg, user = register_user(
                reg_email, reg_username, reg_first, reg_last, reg_pass,
                organisation=org_val
            )
            if ok:
                st.markdown(f"""
                <div style="background:rgba(40,167,69,0.12);
                            border:1px solid rgba(40,167,69,0.35);
                            border-left:4px solid {DARK['success']};
                            border-radius:10px;padding:1.1rem 1.3rem;
                            margin-top:1rem">
                    <div style="font-size:1.4rem;margin-bottom:0.4rem">✅</div>
                    <strong style="color:{DARK['success']};font-size:1rem">
                        Registration submitted!
                    </strong><br>
                    <span style="color:{DARK['text']};font-size:0.88rem">
                        Organisation: <strong>{org_val or '—'}</strong><br>
                        Your account is now <strong>pending admin approval</strong>.<br>
                        Come back to the <strong>Sign In</strong> tab once you've been notified.
                    </span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"❌ {msg}")

# ─── RESET PASSWORD ───────────────────────────────────────────────────────────
with tab_reset:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(246,204,82,0.1);border:1px solid rgba(246,204,82,0.3);
                border-left:4px solid {DARK['warning']};border-radius:10px;
                padding:0.9rem 1.1rem;margin-bottom:1rem;font-size:0.88rem">
        <strong style="color:{DARK['warning']}">How password reset works</strong><br>
        <span style="color:{DARK['text']}">
            Enter your email → we generate a reset token shown on this screen →
            enter the token + your new password below.
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Step 1 — Get your reset token**")
    fp_email = st.text_input("Your registered email", key="fp_email",
                              placeholder="you@example.com")

    if st.button("Generate Reset Token", key="btn_gen_token"):
        if not fp_email:
            st.warning("Please enter your email address.")
        else:
            ok, result = generate_reset_token(fp_email)
            if ok:
                st.session_state["reset_token_display"] = result
                st.success("Token generated! Copy it below.")
            else:
                st.error(f"❌ {result}")

    if st.session_state.get("reset_token_display"):
        tok = st.session_state["reset_token_display"]
        st.markdown(f"""
        <div style="background:{DARK['bg3']};border:1px solid {DARK['accent']}66;
                    border-radius:8px;padding:0.8rem 1rem;margin:0.5rem 0">
            <div style="color:{DARK['muted']};font-size:0.72rem;margin-bottom:4px">
                YOUR RESET TOKEN — copy this
            </div>
            <code style="color:{DARK['accent']};font-size:0.85rem;
                         word-break:break-all">{tok}</code>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>**Step 2 — Set your new password**")

    fp_token  = st.text_input("Paste reset token", key="fp_token",
                               placeholder="Paste the token from above")
    fp_newpw  = st.text_input("New password", type="password", key="fp_newpw",
                               placeholder="At least 8 characters")
    fp_newpw2 = st.text_input("Confirm new password", type="password",
                               key="fp_newpw2", placeholder="Repeat new password")

    if st.button("✅ Set New Password", type="primary",
                 use_container_width=True, key="btn_reset"):
        if fp_newpw != fp_newpw2:
            st.error("❌ Passwords do not match.")
        elif not fp_token or not fp_newpw:
            st.warning("Please fill in all fields.")
        else:
            ok, msg = reset_password_with_token(fp_token, fp_newpw)
            if ok:
                st.success(f"✅ {msg}")
                st.session_state.pop("reset_token_display", None)
            else:
                st.error(f"❌ {msg}")

st.markdown(f"""
<div style="text-align:center;margin-top:2.5rem;
            color:{DARK['muted']};font-size:0.72rem">
    Octa Platform · Questions? octainsight@gmail.com
</div>
""", unsafe_allow_html=True)
