"""
Octa Platform — Authentication Module
No email dependency — all notifications are on-screen.
"""
import bcrypt
import secrets
import streamlit as st
from datetime import datetime, timezone, timedelta
from modules.database import db

APP_NAME = "octa_financial"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def get_user_by_email(email: str) -> dict | None:
    resp = db().table("octa_users").select("*") \
               .eq("email", email.strip().lower()).execute()
    return resp.data[0] if resp.data else None


def get_user_by_username(username: str) -> dict | None:
    resp = db().table("octa_users").select("*") \
               .eq("username", username.strip()).execute()
    return resp.data[0] if resp.data else None


def get_user_by_id(uid: int) -> dict | None:
    resp = db().table("octa_users").select("*").eq("id", uid).execute()
    return resp.data[0] if resp.data else None


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(email: str, username: str, first_name: str,
                  last_name: str, password: str,
                  organisation: str = "") -> tuple:
    """Returns (ok, message, user|None)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters.", None
    if "@" not in email:
        return False, "Invalid email address.", None
    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters.", None
    if get_user_by_email(email):
        return False, "This email is already registered.", None
    if get_user_by_username(username):
        return False, "This username is already taken.", None

    try:
        resp = db().table("octa_users").insert({
            "email":         email.strip().lower(),
            "username":      username.strip(),
            "first_name":    first_name.strip(),
            "last_name":     last_name.strip(),
            "password_hash": hash_password(password),
            "status":        "pending",
            "apps_access":   [],
            "role":          "user",
            "organisation":  organisation.strip(),
        }).execute()
        user = resp.data[0] if resp.data else None
        return True, "Registration submitted successfully.", user
    except Exception as e:
        return False, f"Registration failed: {e}", None


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(email: str, password: str) -> tuple:
    """Returns (ok, message, user|None)."""
    user = get_user_by_email(email)
    if not user:
        return False, "No account found with this email.", None

    status = user.get("status")
    if status == "pending":
        return False, (
            "⏳ Your account is pending admin approval.\n"
            "Please check back later or contact octainsight@gmail.com."
        ), None
    if status == "disabled":
        return False, "🚫 Your account has been disabled. Contact octainsight@gmail.com.", None

    if not verify_password(password, user.get("password_hash", "")):
        return False, "Incorrect password.", None

    # Check app access (admins bypass)
    if user.get("role") != "admin":
        apps = user.get("apps_access") or []
        if isinstance(apps, str):
            import json
            try:    apps = json.loads(apps)
            except: apps = []
        if APP_NAME not in apps:
            return False, "Your account does not have access to this application.", None

    db().table("octa_users") \
        .update({"last_login": datetime.now(timezone.utc).isoformat()}) \
        .eq("id", user["id"]).execute()

    name = user.get("first_name") or user.get("username", "")
    return True, f"Welcome back, {name}!", user


# ── Password Reset (token-based, on-screen only) ──────────────────────────────

def generate_reset_token(email: str) -> tuple:
    """
    Generate a token, store it in DB, return (ok, token|error).
    The token is shown on-screen — no email needed.
    """
    user = get_user_by_email(email)
    if not user:
        return False, "No account found with this email."

    token   = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    db().table("octa_users").update({
        "reset_token":   token,
        "reset_expires": expires,
    }).eq("id", user["id"]).execute()

    return True, token


def reset_password_with_token(token: str, new_password: str) -> tuple:
    """Returns (ok, message)."""
    if len(new_password) < 8:
        return False, "Password must be at least 8 characters."

    resp = db().table("octa_users").select("*") \
               .eq("reset_token", token.strip()).execute()
    if not resp.data:
        return False, "Invalid reset token."

    user    = resp.data[0]
    expires = user.get("reset_expires", "")
    if expires:
        try:
            exp = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                return False, "Reset token has expired. Please generate a new one."
        except Exception:
            pass

    db().table("octa_users").update({
        "password_hash": hash_password(new_password),
        "reset_token":   None,
        "reset_expires": None,
    }).eq("id", user["id"]).execute()

    return True, "Password updated successfully. You can now log in."


# ── Session ───────────────────────────────────────────────────────────────────

def set_session(user: dict):
    apps = user.get("apps_access") or []
    if isinstance(apps, str):
        import json
        try:    apps = json.loads(apps)
        except: apps = []
    st.session_state.authenticated = True
    st.session_state.user_id       = user["id"]
    st.session_state.username      = user.get("username", "")
    st.session_state.first_name    = user.get("first_name", "")
    st.session_state.last_name     = user.get("last_name", "")
    st.session_state.email         = user.get("email", "")
    st.session_state.role          = user.get("role", "user")
    st.session_state.apps_access   = apps
    st.session_state.organisation  = user.get("organisation", "")


def clear_session():
    for k in ["authenticated", "user_id", "username", "first_name",
              "last_name", "email", "role", "apps_access"]:
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated"))


def require_auth():
    """Check auth. Tries URL SSO token first, then session state."""
    if is_authenticated():
        return
    try:
        from modules.sso import auto_login_from_url
        if auto_login_from_url():
            return
    except ImportError:
        pass
    st.switch_page("pages/login.py")


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"
