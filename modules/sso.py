"""
Octa Platform — SSO Session Module
Copy to modules/sso.py in every app including the launcher.

How it works:
1. User logs in on the launcher (or any app)
2. A secure token is created in Supabase session_tokens table
3. Token is added to the URL: ?session=TOKEN
4. Each app checks the URL token on load and auto-signs in
5. Token expires after SESSION_HOURS of inactivity
6. Browser refresh keeps the session because the token stays in the URL
"""
import secrets
import streamlit as st
from datetime import datetime, timezone, timedelta

SESSION_HOURS = 4    # auto-logout after 8 hours of inactivity


def _db():
    """Import db from the app's own database module."""
    from modules.database import db
    return db()


def create_session_token(user_id: int) -> str:
    """
    Generate a secure token, store in DB, return the token string.
    Call this after successful login.
    """
    token     = secrets.token_urlsafe(48)
    now       = datetime.now(timezone.utc)
    expires   = now + timedelta(hours=SESSION_HOURS)

    try:
        # Remove any existing tokens for this user (single active session)
        _db().table("session_tokens").delete() \
             .eq("user_id", user_id).execute()

        _db().table("session_tokens").insert({
            "token":       token,
            "user_id":     user_id,
            "expires_at":  expires.isoformat(),
            "last_active": now.isoformat(),
        }).execute()
    except Exception as e:
        st.error(f"Session error: {e}")
        return ""

    return token


def validate_session_token(token: str) -> dict | None:
    """
    Validate a token string.
    Returns the full user dict if valid, None if invalid/expired.
    Updates last_active on every successful validation.
    """
    if not token:
        return None

    try:
        resp = _db().table("session_tokens").select("*") \
                    .eq("token", token).execute()
        if not resp.data:
            return None

        session  = resp.data[0]
        now      = datetime.now(timezone.utc)
        expires  = datetime.fromisoformat(
            session["expires_at"].replace("Z", "+00:00")
        )

        if now > expires:
            # Expired — delete it
            _db().table("session_tokens").delete() \
                 .eq("token", token).execute()
            return None

        # Update last_active + extend expiry on each use
        new_expiry = now + timedelta(hours=SESSION_HOURS)
        _db().table("session_tokens").update({
            "last_active": now.isoformat(),
            "expires_at":  new_expiry.isoformat(),
        }).eq("token", token).execute()

        # Load the user
        user_resp = _db().table("octa_users").select("*") \
                         .eq("id", session["user_id"]).execute()
        return user_resp.data[0] if user_resp.data else None

    except Exception:
        return None


def invalidate_session_token(token: str):
    """Delete the token (logout)."""
    if not token:
        return
    try:
        _db().table("session_tokens").delete() \
             .eq("token", token).execute()
    except Exception:
        pass


def get_token_from_url() -> str:
    """Read session token from URL query params."""
    try:
        return st.query_params.get("session", "")
    except Exception:
        return ""


def set_token_in_url(token: str):
    """Write session token to URL query params."""
    try:
        st.query_params["session"] = token
    except Exception:
        pass


def clear_token_from_url():
    """Remove session token from URL."""
    try:
        if "session" in st.query_params:
            del st.query_params["session"]
    except Exception:
        pass


def auto_login_from_url() -> bool:
    """
    Check URL for a valid session token and auto-sign in if found.
    Call this at the top of every page BEFORE require_auth().
    Returns True if auto-login succeeded.
    """
    if st.session_state.get("authenticated"):
        return True   # already logged in

    token = get_token_from_url()
    if not token:
        return False

    user = validate_session_token(token)
    if not user:
        clear_token_from_url()
        return False

    # Auto sign-in
    from modules.auth import set_session
    set_session(user)
    st.session_state["sso_token"] = token
    return True


def logout():
    """Full logout: clear session, invalidate token, clean URL."""
    token = st.session_state.get("sso_token","") or get_token_from_url()
    invalidate_session_token(token)
    clear_token_from_url()

    from modules.auth import clear_session
    clear_session()
    st.session_state.pop("sso_token", None)
