"""
Clerk authentication — modular, secure, and styled for NutriGuard.

CLERK_SECRET_KEY is never sent to the browser; it is only used server-side
(in verify_session_token) to call Clerk's Backend REST API.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from services.config import Settings

SESSION_KEY = "nutriguard_user"


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
    if "clerk_session" in st.query_params:
        del st.query_params["clerk_session"]
    st.query_params.clear()


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


def _mount_clerk_widget(publishable_key: str) -> None:
    template = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <base href="http://localhost:8501/">
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
    (function() {
      var parentUrl = 'http://localhost:8501/';
      try {
        if (window.parent && window.parent.location && window.parent.location.href) {
          parentUrl = window.parent.location.href;
        }
      } catch(e) {}

      var NativeURL = window.URL;
      function SafeURL(url, base) {
        if (typeof url === 'string' && (url === 'about:srcdoc' || url.indexOf('about:') === 0 || url === '')) {
          url = parentUrl;
        }
        if (base && typeof base === 'string' && (base === 'about:srcdoc' || base.indexOf('about:') === 0)) {
          base = parentUrl;
        }
        try {
          return new NativeURL(url, base);
        } catch (err) {
          return new NativeURL(parentUrl);
        }
      }
      SafeURL.prototype = NativeURL.prototype;
      for (var key in NativeURL) {
        try { SafeURL[key] = NativeURL[key]; } catch(e) {}
      }
      window.URL = SafeURL;

      // Protect history.replaceState and history.pushState from about:srcdoc URL mismatch errors
      try {
        var _origReplaceState = window.history.replaceState.bind(window.history);
        window.history.replaceState = function(state, title, url) {
          try {
            return _origReplaceState(state, title, url);
          } catch (e) {
            try { return _origReplaceState(state, title); } catch (e2) {}
          }
        };
        var _origPushState = window.history.pushState.bind(window.history);
        window.history.pushState = function(state, title, url) {
          try {
            return _origPushState(state, title, url);
          } catch (e) {
            try { return _origPushState(state, title); } catch (e2) {}
          }
        };
      } catch(e) {}
    })();
  </script>
  <script src="https://cdn.jsdelivr.net/npm/@clerk/clerk-js@5/dist/clerk.browser.js"
          data-clerk-publishable-key="__CLERK_PK__"></script>
</head>
<body>
  <div id="clerk-sign-in">
    <div id="loader" class="clerk-loader">
      <div class="spinner"></div>
      <span>Connecting to secure authentication...</span>
    </div>
  </div>
  <script>
    function handleSession(token) {
      if (!token) return;
      try {
        const targetUrl = new URL(window.parent.location.href);
        targetUrl.searchParams.set('clerk_session', token);
        window.parent.location.href = targetUrl.toString();
      } catch (e) {
        try {
          window.top.location.search = '?clerk_session=' + encodeURIComponent(token);
        } catch (e2) {
          console.error('Redirection error:', e2);
        }
      }
    }

    async function initClerk() {
      if (!window.Clerk) {
        setTimeout(initClerk, 50);
        return;
      }
      try {
        await window.Clerk.load({
          appearance: {
            variables: {
              colorPrimary: '#2DD4BF',
              colorBackground: '#171E27',
              colorText: '#F8FAFC',
              colorInputBackground: '#10161D',
              colorInputText: '#F8FAFC',
              colorTextSecondary: '#94A3B8',
              borderRadius: '8px'
            },
            elements: {
              card: {
                backgroundColor: '#171E27',
                border: '1px solid #222D3D',
                boxShadow: '0 12px 36px rgba(0,0,0,0.5)'
              },
              headerTitle: { color: '#F8FAFC', fontFamily: 'inherit' },
              headerSubtitle: { color: '#94A3B8' },
              socialButtonsBlockButton: {
                backgroundColor: '#1F2937',
                borderColor: '#374151',
                color: '#F8FAFC'
              },
              socialButtonsBlockButtonText: {
                color: '#F8FAFC',
                fontWeight: '600'
              },
              dividerLine: { backgroundColor: '#2E3D52' },
              dividerText: { color: '#94A3B8' },
              formFieldLabel: { color: '#CBD5E1' },
              formFieldInput: {
                backgroundColor: '#10161D',
                borderColor: '#2E3D52',
                color: '#F8FAFC'
              },
              formButtonPrimary: {
                backgroundColor: '#2DD4BF',
                color: '#0B0F14',
                fontWeight: '600',
                '&:hover': { backgroundColor: '#14B8A6' }
              },
              footerActionLink: { color: '#2DD4BF' }
            }
          }
        });

        const loader = document.getElementById('loader');
        if (loader) loader.style.display = 'none';

        if (window.Clerk.session && window.Clerk.session.id) {
          handleSession(window.Clerk.session.id);
          return;
        }

        const target = document.getElementById('clerk-sign-in');
        window.Clerk.mountSignIn(target, {
          routing: 'virtual'
        });

        window.Clerk.addListener(async ({ session }) => {
          if (session && session.id) {
            handleSession(session.id);
          }
        });
      } catch (err) {
        console.error('Failed to initialize Clerk:', err);
        const loader = document.getElementById('loader');
        if (loader) {
          loader.innerHTML = '<span style="color:#F43F5E;font-size:13px;">Error initializing authentication: ' + (err.message || err) + '</span>';
        }
      }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initClerk);
    } else {
      initClerk();
    }
  </script>
</body>
</html>"""
    widget_html = template.replace("__CLERK_PK__", publishable_key)
    components.html(widget_html, height=720, scrolling=True)


def render_login_gate(settings: Settings) -> Optional[AuthUser]:
    """Renders the custom NutriGuard-branded authentication experience and returns user if signed in."""
    if "signout" in st.query_params:
        sign_out()
        st.query_params.clear()
        st.rerun()

    user = current_user()
    if user:
        return user

    # Check query params for returned session
    token = st.query_params.get("clerk_session")
    if token:
        with st.spinner("Verifying secure credentials..."):
            verified = verify_session_token(token, settings)
        if verified:
            st.session_state[SESSION_KEY] = verified
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Could not verify your session. Please sign in again.")

    configured = is_configured(settings)

    # Branded NutriGuard Login Header Container
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
            AI-powered food image authenticity & classification platform
          </div>
          <div class="ng-auth-divider">
            <span class="ng-auth-laser-beam"></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render Auth Widget or Configuration State
    if not configured:
        st.markdown(
            """
            <div class="ng-card" style="max-width:540px; margin: 0 auto 1.5rem auto; text-align:center;">
              <div class="ng-card-label" style="color:#F59E0B;">DEVELOPMENT MODE</div>
              <div class="ng-card-title" style="font-size:1.15rem; color:#F8FAFC;">Clerk Keys Not Configured</div>
              <div class="ng-card-body" style="font-size:0.9rem; margin-bottom:1rem;">
                Add <code>CLERK_PUBLISHABLE_KEY</code> and <code>CLERK_SECRET_KEY</code> to your <code>.env</code>
                file to enable full identity verification. You can continue as a guest for local testing.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        if configured:
            _mount_clerk_widget(settings.clerk_publishable_key)
            st.markdown(
                """
                <div style="text-align:center; color:#64748B; font-size:0.8rem; margin-top:0.6rem; letter-spacing:0.02em;">
                  🔒 Secure authentication powered by Clerk • End-to-end encrypted session
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Guest mode / fast bypass
        st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
        btn_label = "Continue as Guest" if not configured else "Or continue as Guest (Evaluation Mode)"
        if st.button(btn_label, type="secondary", use_container_width=True, key="guest_auth_btn"):
            st.session_state[SESSION_KEY] = AuthUser(
                user_id="guest_evaluator",
                display_name="Guest Evaluator",
                email="guest@nutriguard.ai",
                is_guest=True,
            )
            st.rerun()

    return None
