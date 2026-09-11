"""
NutriGuard Authentication — fully server-side, no iframe required.

Sign-in flow:
  1. Show a branded email + password form.
  2. Call Clerk's Frontend API from Python to authenticate.
  3. Verify the resulting session via Clerk's Backend API.
  4. Store the AuthUser in st.session_state.

No browser JS, no iframe, no cross-origin issues.
"""
from __future__ import annotations

import base64
import html
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from services.config import Settings

SESSION_KEY = "nutriguard_user"


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


def _frontend_api_base(publishable_key: str) -> str:
    """
    Decode the Clerk publishable key to get the Frontend API base URL.

    pk_test_<base64-encoded-instance-domain>
    e.g. pk_test_cmlnaHQtZmxhbWluZ28tMzEuY2xlcmsuYWNjb3VudHMuZGV2JA
      → right-flamingo-31.clerk.accounts.dev
      → https://right-flamingo-31.clerk.accounts.dev
    """
    try:
        # Strip pk_test_ / pk_live_ prefix
        encoded = publishable_key.split("_", 2)[-1]
        # Re-pad to valid base64 length
        padded = encoded + "=" * (-len(encoded) % 4)
        domain = base64.b64decode(padded).decode().rstrip("$").strip()
        return f"https://{domain}"
    except Exception:
        return ""


# ─────────────────────────────── server-side Clerk auth ──────────────────────

def _clerk_sign_in(email: str, password: str, settings: Settings) -> Optional[str]:
    """
    Create a sign-in attempt via Clerk's Frontend API.
    Returns a session_id on success, or None on failure.
    """
    import requests

    base = _frontend_api_base(settings.clerk_publishable_key or "")
    if not base:
        return None

    try:
        resp = requests.post(
            f"{base}/v1/client/sign_ins",
            headers={
                "Authorization": f"Bearer {settings.clerk_publishable_key}",
                "Content-Type": "application/json",
                "User-Agent": "NutriGuard/1.0 (+https://nutriguard.streamlit.app)",
            },
            json={"identifier": email, "password": password},
            timeout=12,
        )
        if resp.status_code not in (200, 201):
            return None

        body = resp.json()
        data = body.get("response", body)
        if data.get("status") != "complete":
            return None

        return data.get("created_session_id")
    except Exception:
        return None


def verify_session_token(token: str, settings: Settings) -> Optional[AuthUser]:
    """Verify a Clerk session ID server-side via the Backend API."""
    import requests

    if not settings.clerk_secret_key:
        return None

    try:
        session_url = f"https://api.clerk.com/v1/sessions/{token}"
        resp = requests.get(
            session_url,
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
                last = (u.get("last_name") or "").strip()
                full = f"{first} {last}".strip()
                emails = u.get("email_addresses") or []
                if emails:
                    email = emails[0].get("email_address")
                display_name = full or u.get("username") or email or user_id
                avatar_url = u.get("image_url")
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


def authenticate_with_clerk(
    email: str, password: str, settings: Settings
) -> tuple[Optional[AuthUser], str]:
    """
    Full Clerk auth flow: sign in → verify session → return user.
    Returns (AuthUser, "") on success or (None, error_message) on failure.
    """
    session_id = _clerk_sign_in(email, password, settings)
    if not session_id:
        return None, "Invalid email or password. Please try again."

    user = verify_session_token(session_id, settings)
    if not user:
        return None, "Authentication succeeded but session could not be verified. Please try again."

    return user, ""


# ─────────────────────────────────────── login gate UI ───────────────────────

def _render_login_header() -> None:
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
          <div class="ng-auth-divider">
            <span class="ng-auth-laser-beam"></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_login_gate(settings: Settings) -> Optional[AuthUser]:
    """
    Render the NutriGuard login page and return AuthUser when signed in.

    Uses a server-side email + password form backed by Clerk's REST API.
    No iframe, no browser JS, no cross-origin issues.
    """
    if "signout" in st.query_params:
        sign_out()
        st.rerun()

    user = current_user()
    if user:
        return user

    configured = is_configured(settings)
    _render_login_header()

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        if configured:
            # ── Clerk email + password form ───────────────────────────────
            st.markdown(
                """
                <div style="
                  background:#131920;
                  border:1px solid #222D3D;
                  border-radius:12px;
                  padding:1.6rem 1.8rem 1.2rem;
                  margin-bottom:0.6rem;
                  box-shadow:0 12px 36px rgba(0,0,0,0.5);
                ">
                  <div style="
                    font-family:'Outfit',sans-serif;
                    font-size:1.15rem;
                    font-weight:700;
                    color:#F8FAFC;
                    margin-bottom:0.25rem;
                  ">Sign in to NutriGuard</div>
                  <div style="
                    font-family:'JetBrains Mono',monospace;
                    font-size:0.72rem;
                    color:#94A3B8;
                    margin-bottom:1.2rem;
                    letter-spacing:0.04em;
                  ">Powered by Clerk · End-to-end encrypted</div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("ng_clerk_login", clear_on_submit=False):
                email_in = st.text_input(
                    "Email address",
                    placeholder="you@example.com",
                    label_visibility="visible",
                )
                pass_in = st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••",
                    label_visibility="visible",
                )
                submitted = st.form_submit_button(
                    "Sign In",
                    use_container_width=True,
                    type="primary",
                )

            st.markdown("</div>", unsafe_allow_html=True)

            if submitted:
                if not email_in or not pass_in:
                    st.error("Please enter both email and password.")
                else:
                    with st.spinner("Authenticating with Clerk..."):
                        auth_user, err = authenticate_with_clerk(
                            email_in.strip(), pass_in, settings
                        )
                    if auth_user:
                        st.session_state[SESSION_KEY] = auth_user
                        st.rerun()
                    else:
                        st.error(err)

            st.markdown(
                """
                <div style="text-align:center;color:#475569;font-size:0.78rem;margin-top:0.4rem;">
                  🔒 Credentials verified server-side via Clerk's secure API
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            # ── Dev-mode notice ───────────────────────────────────────────
            st.markdown(
                """
                <div class="ng-card" style="text-align:center;margin-bottom:1rem;">
                  <div class="ng-card-label" style="color:#F59E0B;">DEVELOPMENT MODE</div>
                  <div class="ng-card-title" style="font-size:1.1rem;">Clerk Not Configured</div>
                  <div style="font-size:0.88rem;color:#94A3B8;margin-top:0.4rem;">
                    Set <code>CLERK_PUBLISHABLE_KEY</code> and <code>CLERK_SECRET_KEY</code>
                    in Streamlit secrets to enable sign-in.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Guest bypass ──────────────────────────────────────────────────
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
            st.rerun()

    return None

