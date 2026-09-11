"""
Clerk authentication — modular, secure, and styled for NutriGuard.

CLERK_SECRET_KEY is never sent to the browser; it is only used server-side
(in verify_session_token) to call Clerk's Backend REST API.

Communication between the Clerk JS widget (inside st.iframe) and Streamlit
uses window.parent.location.href redirect. Loop prevention is handled by
tracking the last failed token in session state and clearing query params
immediately on receipt.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from services.config import Settings

SESSION_KEY = "nutriguard_user"
_FAIL_FLAG = "_clerk_verify_failed_token"


@dataclass
class AuthUser:
    user_id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    is_guest: bool = False


def is_configured(settings: Settings) -> bool:
    return bool(settings.clerk_publishable_key and settings.clerk_secret_key)


def current_user() -> Optional[AuthUser]:
    return st.session_state.get(SESSION_KEY)


def sign_out() -> None:
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop("verification_result", None)
    st.session_state.pop(_FAIL_FLAG, None)
    try:
        st.query_params.clear()
    except Exception:
        pass


def verify_session_token(token: str, settings: Settings) -> Optional[AuthUser]:
    """Verify a Clerk session token server-side using the secret key."""
    import requests

    if not settings.clerk_secret_key:
        return None

    try:
        # 1. Verify active session by session ID
        session_url = f"https://api.clerk.com/v1/sessions/{token}"
        resp = requests.get(
            session_url,
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            timeout=7,
        )
        if resp.status_code != 200:
            return None

        sess_data = resp.json()
        if sess_data.get("status") != "active":
            return None

        user_id = sess_data.get("user_id")
        if not user_id:
            return None

        # 2. Enrich with user profile details
        display_name = user_id
        email = None
        avatar_url = None

        try:
            user_url = f"https://api.clerk.com/v1/users/{user_id}"
            u_resp = requests.get(
                user_url,
                headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
                timeout=5,
            )
            if u_resp.status_code == 200:
                u_data = u_resp.json()
                first = (u_data.get("first_name") or "").strip()
                last = (u_data.get("last_name") or "").strip()
                full = f"{first} {last}".strip()
                emails = u_data.get("email_addresses") or []
                if emails:
                    email = emails[0].get("email_address")
                display_name = full or (u_data.get("username") or email or user_id)
                avatar_url = u_data.get("image_url")
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


def _build_clerk_html(publishable_key: str, force_signout: bool = False) -> str:
    force_js = ""
    if force_signout:
        force_js = """
      // Force sign-out any cached Clerk session to break redirect loop
      try {
        if (window.Clerk && window.Clerk.signOut) {
          window.Clerk.signOut();
        }
      } catch(e) {}
"""
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {
      margin: 0;
      padding: 0;
      background: transparent;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    #clerk-sign-in {
      width: 100%;
      max-width: 440px;
      margin: 0 auto;
    }
    .clerk-loader {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 40px 20px;
      color: #94A3B8;
      font-size: 14px;
    }
    .spinner {
      width: 28px;
      height: 28px;
      border: 3px solid rgba(45, 212, 191, 0.15);
      border-top-color: #2DD4BF;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin-bottom: 12px;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  </style>
  <script>
    // Protect history API from about:srcdoc origin errors
    (function() {
      ['replaceState', 'pushState'].forEach(function(m) {
        try {
          var orig = window.history[m].bind(window.history);
          window.history[m] = function(s, t, u) {
            try { return orig(s, t, u); } catch(e) { try { return orig(s, t); } catch(e2) {} }
          };
        } catch(e) {}
      });
    })();
  </script>
  <script async crossorigin="anonymous"
    data-clerk-publishable-key="__CLERK_PK__"
    src="https://cdn.jsdelivr.net/npm/@clerk/clerk-js@5/dist/clerk.browser.js">
  </script>
</head>
<body>
  <div id="clerk-sign-in">
    <div id="loader" class="clerk-loader">
      <div class="spinner"></div>
      <span>Connecting to secure authentication...</span>
    </div>
  </div>
  <script>
    __FORCE_SIGNOUT_JS__

    function sendSession(token) {
      if (!token) return;
      try {
        var url = new URL(window.parent.location.href);
        url.searchParams.set('clerk_session', token);
        window.parent.location.replace(url.toString());
      } catch(e) {
        try {
          window.top.location.search = '?clerk_session=' + encodeURIComponent(token);
        } catch(e2) { console.warn('NutriGuard redirect failed', e2); }
      }
    }

    function initClerk() {
      if (!window.Clerk) { setTimeout(initClerk, 100); return; }
      window.Clerk.load({
        appearance: {
          variables: {
            colorPrimary: '#2DD4BF', colorBackground: '#171E27',
            colorText: '#F8FAFC', colorInputBackground: '#10161D',
            colorInputText: '#F8FAFC', colorTextSecondary: '#94A3B8',
            borderRadius: '8px'
          },
          elements: {
            card: { backgroundColor: '#171E27', border: '1px solid #222D3D',
                    boxShadow: '0 12px 36px rgba(0,0,0,0.5)' },
            headerTitle: { color: '#F8FAFC' },
            headerSubtitle: { color: '#94A3B8' },
            socialButtonsBlockButton: { backgroundColor: '#1F2937',
              borderColor: '#374151', color: '#F8FAFC' },
            socialButtonsBlockButtonText: { color: '#F8FAFC', fontWeight: '600' },
            dividerLine: { backgroundColor: '#2E3D52' },
            dividerText: { color: '#94A3B8' },
            formFieldLabel: { color: '#CBD5E1' },
            formFieldInput: { backgroundColor: '#10161D',
              borderColor: '#2E3D52', color: '#F8FAFC' },
            formButtonPrimary: { backgroundColor: '#2DD4BF',
              color: '#0B0F14', fontWeight: '600' },
            footerActionLink: { color: '#2DD4BF' }
          }
        }
      }).then(function() {
        var loader = document.getElementById('loader');
        if (loader) loader.style.display = 'none';
        if (window.Clerk.session && window.Clerk.session.id) {
          sendSession(window.Clerk.session.id);
          return;
        }
        var target = document.getElementById('clerk-sign-in');
        window.Clerk.mountSignIn(target, { routing: 'virtual' });
        window.Clerk.addListener(function(res) {
          if (res.session && res.session.id) sendSession(res.session.id);
        });
      }).catch(function(err) {
        var loader = document.getElementById('loader');
        if (loader) loader.innerHTML =
          '<span style="color:#F43F5E;font-size:13px;">Auth error: ' +
          (err.message || String(err)) + '</span>';
      });
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initClerk);
    } else {
      initClerk();
    }
  </script>
</body>
</html>"""


def _mount_clerk_widget(publishable_key: str, force_signout: bool = False) -> None:
    force_js = ""
    if force_signout:
        force_js = (
            "try { if (window.Clerk && window.Clerk.signOut) {"
            " window.Clerk.signOut(); } } catch(e) {}"
        )
    # Inject PK and optional force-signout JS into the template
    raw = _build_clerk_html(publishable_key, force_signout=force_signout)
    widget_html = raw.replace("__CLERK_PK__", publishable_key)
    widget_html = widget_html.replace("__FORCE_SIGNOUT_JS__", force_js)
    st.iframe(widget_html, height=680)



def render_login_gate(settings: Settings) -> Optional[AuthUser]:
    """
    Renders the NutriGuard login gate.

    Loop-safe flow:
    1. Signout param → clear session and rerun.
    2. User already in session state → return immediately.
    3. ?clerk_session=<token> present → clear it immediately, then verify once.
       - Success: store user, rerun.
       - Failure: record failed token in session state, rerun (shows login page).
    4. If last verification failed with the same token, show error + Clerk widget
       with force_signout so Clerk JS clears its session before re-mounting.
    """
    if "signout" in st.query_params:
        sign_out()
        st.rerun()

    user = current_user()
    if user:
        return user

    # ── Token handling ───────────────────────────────────────────────────────
    token = st.query_params.get("clerk_session", "")
    if token:
        # IMMEDIATELY clear the query param to prevent rerun loops
        st.query_params.clear()

        last_failed = st.session_state.get(_FAIL_FLAG, "")
        if token == last_failed:
            # Same token failed before — show error but don't retry
            st.session_state.pop(_FAIL_FLAG, None)
            st.error(
                "⚠️ Session verification failed. Please sign in again. "
                "If this keeps happening, clear your browser cookies for this site."
            )
        else:
            with st.spinner("Verifying secure credentials..."):
                verified = verify_session_token(token, settings)
            if verified:
                st.session_state[SESSION_KEY] = verified
                st.session_state.pop(_FAIL_FLAG, None)
                st.rerun()
            else:
                # Record failure and rerun cleanly (no clerk_session in URL now)
                st.session_state[_FAIL_FLAG] = token
                st.rerun()

    configured = is_configured(settings)
    # Show the Clerk widget with force_signout if the last attempt failed
    # — this breaks the auto-redirect loop by clearing Clerk's cached session
    failed_before = bool(st.session_state.get(_FAIL_FLAG, ""))

    # ── Branded login header ─────────────────────────────────────────────────
    st.markdown(
        """
        <div class="ng-auth-container">
          <div class="ng-auth-motif">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M24 4L6 12V22C6 33.1 13.7 43.4 24 46C34.3 43.4 42 33.1 42 22V12L24 4Z"
                    fill="url(#shield_grad)" stroke="#2DD4BF" stroke-width="2" stroke-linejoin="round"/>
              <path d="M16 24L22 30L32 18" stroke="#F8FAFC" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
              <defs>
                <linearGradient id="shield_grad" x1="6" y1="4" x2="42" y2="46" gradientUnits="userSpaceOnUse">
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

    if not configured:
        st.markdown(
            """
            <div class="ng-card" style="max-width:540px; margin: 0 auto 1.5rem auto; text-align:center;">
              <div class="ng-card-label" style="color:#F59E0B;">DEVELOPMENT MODE</div>
              <div class="ng-card-title" style="font-size:1.15rem; color:#F8FAFC;">Clerk Keys Not Configured</div>
              <div class="ng-card-body" style="font-size:0.9rem; margin-bottom:1rem;">
                Add <code>CLERK_PUBLISHABLE_KEY</code> and <code>CLERK_SECRET_KEY</code> to your Streamlit
                secrets (or <code>.env</code>) to enable full identity verification.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        if configured:
            _mount_clerk_widget(
                settings.clerk_publishable_key,
                force_signout=failed_before,
            )
            st.markdown(
                """
                <div style="text-align:center; color:#64748B; font-size:0.8rem;
                            margin-top:0.6rem; letter-spacing:0.02em;">
                  🔒 Secure authentication powered by Clerk
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
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
