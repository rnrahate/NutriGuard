"""
NutriGuard Authentication.

The Clerk JS sign-in widget is served from Streamlit's static file server
(/app/static/clerk_widget.html) which shares the SAME ORIGIN as the Streamlit
app. This means window.parent.location works without cross-origin restrictions,
enabling the session-token redirect to work reliably.

Flow:
  1. st.iframe("/app/static/clerk_widget.html?pk=<PK>") -> full Clerk UI
  2. User signs in -> Clerk JS redirects parent to ?clerk_session=<id>
  3. Python verifies session via Clerk Backend API -> stores AuthUser
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import urllib.parse

import streamlit as st

from services.config import Settings

SESSION_KEY = "nutriguard_user"
_FAIL_FLAG  = "_clerk_failed_token"


# ─────────────────────────────────────────── data model ──────────────────────

@dataclass
class AuthUser:
    user_id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    is_guest: bool = False


# ─────────────────────────────────────── helpers ─────────────────────────────

def is_configured(settings: Settings) -> bool:
    return bool(settings.clerk_publishable_key and settings.clerk_secret_key)


def current_user() -> Optional[AuthUser]:
    return st.session_state.get(SESSION_KEY)


def sign_out() -> None:
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop("verification_result", None)
    try:
        st.query_params.clear()
    except Exception:
        pass


# ── Server-side Clerk session verification ────────────────────────────────────

def verify_session_token(token: str, settings: Settings) -> Optional[AuthUser]:
    """Verify a Clerk session ID via the Backend API (secret key never sent to browser)."""
    import requests

    if not settings.clerk_secret_key:
        return None

    try:
        resp = requests.get(
            f"https://api.clerk.com/v1/sessions/{token}",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        sess = resp.json()
        if sess.get("status") != "active":
            return None

        user_id = sess.get("user_id")
        if not user_id:
            return None

        display_name, email, avatar_url = user_id, None, None
        try:
            u_resp = requests.get(
                f"https://api.clerk.com/v1/users/{user_id}",
                headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
                timeout=7,
            )
            if u_resp.status_code == 200:
                u = u_resp.json()
                first = (u.get("first_name") or "").strip()
                last  = (u.get("last_name")  or "").strip()
                full  = f"{first} {last}".strip()
                emails = u.get("email_addresses") or []
                if emails:
                    email = emails[0].get("email_address")
                display_name = full or u.get("username") or email or user_id
                avatar_url   = u.get("image_url")
        except Exception:
            pass

        return AuthUser(
            user_id=user_id,
            display_name=display_name,
            email=email,
            avatar_url=avatar_url,
            is_guest=False,
        )
    except Exception:
        return None


# ── Clerk widget via static file (same-origin iframe) ────────────────────────

def _mount_clerk_widget(publishable_key: str) -> None:
    """
    Render the Clerk sign-in widget in a same-origin iframe.

    Streamlit serves static/ files from the app's own domain:
      https://nutriguard.streamlit.app/app/static/clerk_widget.html

    Because the iframe origin matches the parent page, window.parent.location
    is fully accessible — no cross-origin security errors.
    The widget redirects to ?clerk_session=<id> after a successful sign-in.
    """
    pk_encoded = urllib.parse.quote(publishable_key, safe="")
    st.iframe(f"/app/static/clerk_widget.html?pk={pk_encoded}", height=680)


# ── Login gate UI ─────────────────────────────────────────────────────────────

def _render_header() -> None:
    st.markdown(
        """
        <div class="ng-auth-container">
          <div class="ng-auth-motif">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <path d="M24 4L6 12V22C6 33.1 13.7 43.4 24 46C34.3 43.4 42 33.1 42 22V12L24 4Z"
                    fill="url(#sg)" stroke="#2DD4BF" stroke-width="2" stroke-linejoin="round"/>
              <path d="M16 24L22 30L32 18" stroke="#F8FAFC" stroke-width="3"
                    stroke-linecap="round" stroke-linejoin="round"/>
              <defs>
                <linearGradient id="sg" x1="6" y1="4" x2="42" y2="46" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#1D2630"/>
                  <stop offset="1" stop-color="#0F172A"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div class="ng-auth-title">NUTRIGUARD</div>
          <div class="ng-auth-tagline">VERIFY BEFORE YOU TRUST.</div>
          <div class="ng-auth-subtitle">
            AI-powered food image authenticity &amp; classification platform
          </div>
          <div class="ng-auth-divider"><span class="ng-auth-laser-beam"></span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_login_gate(settings: Settings) -> Optional[AuthUser]:
    """
    Render the NutriGuard login gate.

    The Clerk widget runs in /app/static/clerk_widget.html (same-origin),
    so window.parent.location.replace() works and sets ?clerk_session=<id>.

    Loop-safe token flow:
    - Token arrives in ?clerk_session -> cleared immediately to prevent rerun loop
    - Verified once via Backend API
    - On failure: token recorded in _FAIL_FLAG -> not re-verified on next rerun
    """
    if "signout" in st.query_params:
        sign_out()
        st.rerun()

    user = current_user()
    if user:
        return user

    # ── Handle clerk_session redirect from the Clerk widget ───────────────────
    token = st.query_params.get("clerk_session", "")
    if token:
        st.query_params.clear()  # clear immediately to break any potential loop

        last_failed = st.session_state.get(_FAIL_FLAG, "")
        if token == last_failed:
            # This exact token already failed — show error once and reset
            st.session_state.pop(_FAIL_FLAG, None)
            st.error(
                "Session verification failed. Please sign in again. "
                "If this persists, clear your browser cookies for this site."
            )
        else:
            with st.spinner("Verifying your Clerk session..."):
                verified = verify_session_token(token, settings)
            if verified:
                st.session_state[SESSION_KEY] = verified
                st.session_state.pop(_FAIL_FLAG, None)
                st.rerun()
            else:
                st.session_state[_FAIL_FLAG] = token
                st.rerun()

    configured = is_configured(settings)
    _render_header()

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        if configured:
            # ── Full Clerk UI via same-origin static file iframe ──────────
            _mount_clerk_widget(settings.clerk_publishable_key)
            st.markdown(
                """<div style="text-align:center;color:#475569;font-size:0.77rem;margin-top:0.5rem;">
                  \U0001f512 Secure sign-in powered by Clerk
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            # ── Dev-mode notice ───────────────────────────────────────────
            st.markdown(
                """<div class="ng-card" style="text-align:center;margin-bottom:1rem;">
                  <div class="ng-card-label" style="color:#F59E0B;">DEVELOPMENT MODE</div>
                  <div class="ng-card-title" style="font-size:1.1rem;">Clerk Not Configured</div>
                  <div style="font-size:0.88rem;color:#94A3B8;margin-top:0.4rem;">
                    Set <code>CLERK_PUBLISHABLE_KEY</code> and <code>CLERK_SECRET_KEY</code>
                    in Streamlit secrets to enable Clerk sign-in.
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
        btn_label = (
            "Continue as Guest"
            if not configured
            else "Or continue as Guest (Evaluation Mode)"
        )
        if st.button(btn_label, type="secondary", use_container_width=True, key="guest_auth_btn"):
            st.session_state[SESSION_KEY] = AuthUser(
                user_id="guest_evaluator",
                display_name="Guest Evaluator",
                email="guest@nutriguard.ai",
                is_guest=True,
            )
            st.session_state.pop(_FAIL_FLAG, None)
            st.rerun()

    return None

