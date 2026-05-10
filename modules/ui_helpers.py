"""Octa Financial Control — UI helpers."""
import streamlit as st
from config import DARK, APP_NAME, APP_VERSION

GLOBAL_CSS = f"""
<style>
html,body,[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section,
[data-testid="block-container"]{{background-color:{DARK['bg']}!important;color:{DARK['text']}!important}}
[data-testid="stVerticalBlock"],[data-testid="stHorizontalBlock"],
[data-testid="column"],.element-container,.stMarkdown{{background:transparent!important}}
h1,h2,h3,h4{{color:{DARK['text']}!important}}
label,.stTextInput label,.stSelectbox label,.stMultiselect label,
.stTextArea label,.stNumberInput label,.stDateInput label{{color:{DARK['muted']}!important;font-size:0.85rem!important}}
[data-testid="stSidebar"]{{background:{DARK['sidebar']}!important;border-right:3px solid {DARK['accent']}!important}}
[data-testid="stSidebar"] *{{color:{DARK['text']}!important}}
[data-testid="stSidebarNav"]{{display:none!important}}
[data-testid="stSidebar"] .stButton>button{{
    background:rgba(255,255,255,0.06)!important;border:1px solid rgba(255,255,255,0.1)!important;
    border-radius:8px!important;width:100%!important;color:{DARK['text']}!important;
    font-size:0.87rem!important;text-align:left!important;margin-bottom:2px!important}}
[data-testid="stSidebar"] .stButton>button:hover{{
    background:{DARK['accent']}22!important;border-color:{DARK['accent']}66!important;color:{DARK['accent']}!important}}
input,textarea{{background:{DARK['bg3']}!important;border:1px solid {DARK['border']}!important;
    border-radius:8px!important;color:{DARK['text']}!important}}
div[data-baseweb="select"]>div{{background:{DARK['bg3']}!important;border-color:{DARK['border']}!important;color:{DARK['text']}!important}}
div[data-baseweb="select"] *{{color:{DARK['text']}!important}}
div[data-baseweb="popover"]{{background:{DARK['bg2']}!important;border:1px solid {DARK['border']}!important}}
[data-testid="stTabs"] [role="tablist"]{{background:{DARK['bg2']};border-radius:10px;padding:4px;border:1px solid {DARK['border']}}}
[data-testid="stTabs"] [role="tab"]{{color:{DARK['muted']}!important;border-radius:8px}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{{background:{DARK['accent']}!important;color:white!important}}
[data-testid="stButton"]>button{{background:{DARK['bg3']}!important;border:1px solid {DARK['border']}!important;color:{DARK['text']}!important;border-radius:8px!important}}
[data-testid="stButton"]>button:hover{{border-color:{DARK['accent']}!important;color:{DARK['accent']}!important}}
[data-testid="stButton"]>button[kind="primary"]{{background:linear-gradient(135deg,{DARK['accent']},#0097A7)!important;border:none!important;color:white!important;font-weight:600!important}}
[data-testid="stExpander"]{{background:{DARK['bg2']}!important;border:1px solid {DARK['border']}!important;border-radius:10px!important}}
[data-testid="stExpander"] summary{{color:{DARK['text']}!important}}
hr{{border-color:{DARK['border']}!important}}
::-webkit-scrollbar{{width:6px}}
::-webkit-scrollbar-track{{background:{DARK['bg']}}}
::-webkit-scrollbar-thumb{{background:{DARK['bg3']};border-radius:3px}}
.page-header{{background:linear-gradient(135deg,{DARK['sidebar']} 0%,#2d4a7a 100%);
    padding:1.2rem 1.8rem;border-radius:12px;border-left:4px solid {DARK['accent']};margin-bottom:1.4rem}}
.page-header h1{{margin:0;font-size:1.6rem;font-weight:700;color:white!important}}
.page-header p{{margin:0.2rem 0 0;color:rgba(255,255,255,0.65)!important;font-size:0.88rem}}
.section-label{{font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;
    color:{DARK['accent']};margin:1.2rem 0 0.5rem;padding-bottom:0.3rem;border-bottom:1px solid {DARK['border']}}}
</style>
"""

def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def page_header(title, subtitle="", icon=""):
    st.markdown(
        f"<div class='page-header'>"
        f"<h1>{icon+' ' if icon else ''}{title}</h1>"
        f"{'<p>'+subtitle+'</p>' if subtitle else ''}"
        f"</div>", unsafe_allow_html=True)

def section_label(text):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)

def _hr():
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.12);margin:0.5rem 0'>",
                unsafe_allow_html=True)

def _nav(text):
    muted = DARK["muted"]
    st.markdown(
        f"<div style='font-size:0.68rem;font-weight:600;letter-spacing:0.1em;"
        f"text-transform:uppercase;color:{muted};margin-bottom:0.3rem'>{text}</div>",
        unsafe_allow_html=True)

def kpi_card(col, label, value, color, subtitle=""):
    bg2 = DARK["bg2"]; muted = DARK["muted"]
    col.markdown(
        f"<div style='background:{bg2};border-top:3px solid {color};"
        f"border:1px solid {color}44;border-radius:10px;padding:0.8rem;text-align:center'>"
        f"<div style='font-size:1.5rem;font-weight:700;color:{color}'>{value}</div>"
        f"<div style='font-size:0.75rem;color:{muted}'>{label}</div>"
        + (f"<div style='font-size:0.7rem;color:{muted};margin-top:2px'>{subtitle}</div>" if subtitle else "")
        + "</div>", unsafe_allow_html=True)

def budget_bar(label, planned, actual, color):
    """Render a mini horizontal budget progress bar."""
    D = DARK
    pct       = round(actual/planned*100, 1) if planned else 0
    bar_color = D["success"] if pct<75 else (D["warning"] if pct<95 else D["danger"])
    bg2 = D["bg2"]; muted = D["muted"]; txt = D["text"]
    st.markdown(
        f"<div style='background:{bg2};border-left:4px solid {color};"
        f"border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.4rem'>"
        f"<div style='display:flex;justify-content:space-between;font-size:0.83rem'>"
        f"<span style='color:{txt};font-weight:600'>{label}</span>"
        f"<span style='color:{muted}'>€{actual:,.0f} / €{planned:,.0f}"
        f" <strong style='color:{bar_color}'>{pct}%</strong></span></div>"
        f"<div style='background:{D["bg3"]};border-radius:4px;height:6px;margin-top:6px'>"
        f"<div style='background:{bar_color};width:{min(pct,100)}%;height:6px;border-radius:4px'></div>"
        f"</div></div>", unsafe_allow_html=True)


def sidebar_nav():
    is_auth  = st.session_state.get("authenticated", False)
    is_admin = st.session_state.get("role") == "admin"
    uname    = st.session_state.get("first_name") or st.session_state.get("username","")
    pid      = st.session_state.get("selected_project_id","")

    with st.sidebar:
        txt = DARK["text"]; muted = DARK["muted"]
        st.markdown(f"""
<div style="text-align:center;padding:0.8rem 0 0.6rem">
<div style="font-size:1.9rem">💶</div>
<div style="font-weight:700;font-size:0.88rem;color:{txt};line-height:1.3">{APP_NAME}</div>
<div style="color:{muted};font-size:0.65rem">v{APP_VERSION}</div>
</div>""", unsafe_allow_html=True)

        if is_auth and uname:
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);"
                f"border-radius:8px;padding:0.35rem 0.7rem;font-size:0.8rem;margin-bottom:0.3rem'>"
                f"👤 <strong style='color:{txt}'>{uname}</strong></div>",
                unsafe_allow_html=True)

        if pid:
            acc = DARK["accent"]
            st.markdown(
                f"<div style='background:{acc}15;border:1px solid {acc}44;"
                f"border-radius:6px;padding:0.3rem 0.6rem;font-size:0.75rem;"
                f"color:{acc};margin-bottom:0.3rem'>📋 {pid}</div>",
                unsafe_allow_html=True)

        _hr()
        _nav("Financial Control")
        if st.button("📊  Dashboard",       key="nav_dash",   use_container_width=True):
            st.switch_page("app.py")
        if st.button("💰  Enter Spending",  key="nav_entry",  use_container_width=True):
            st.switch_page("pages/partner_budget.py")
        if st.button("📋  Budget Overview", key="nav_overview",use_container_width=True):
            st.switch_page("pages/overview.py")
        if st.button("📈  Forecast",        key="nav_forecast",use_container_width=True):
            st.switch_page("pages/forecast.py")
        if st.button("📥  Export Report",   key="nav_report", use_container_width=True):
            st.switch_page("pages/reports.py")

        _hr()
        if is_admin:
            _nav("Administration")
            if st.button("🛡️  Admin Panel", key="nav_admin", use_container_width=True):
                st.switch_page("pages/admin.py")
            _hr()

        _nav("Account")
        if is_auth:
            if st.button("🚪  Sign Out", use_container_width=True, key="nav_out"):
                try:
                    from modules.sso import logout
                    logout()
                except Exception: pass
                st.switch_page("pages/login.py")
        else:
            if st.button("🔑  Login", use_container_width=True, key="nav_in"):
                st.switch_page("pages/login.py")

        st.markdown(
            f"<div style='color:{muted};font-size:0.62rem;text-align:center;margin-top:1rem'>"
            f"Octa Platform · {__import__('datetime').date.today().year}</div>",
            unsafe_allow_html=True)
