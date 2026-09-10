"""
NutriGuard navigation and sidebar components with SVG icons, account badge, and model status.
"""
from __future__ import annotations

import html
from typing import Optional

import streamlit as st

from components.styles import COLORS
from services import auth

PAGES = [
    {"name": "Dashboard", "icon": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>"""},
    {"name": "Verify Food Image", "icon": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>"""},
    {"name": "History", "icon": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>"""},
    {"name": "System Status", "icon": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>"""},
    {"name": "About", "icon": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>"""},
]

ROUTE_KEY = "ng_route"


def current_route() -> str:
    return st.session_state.get(ROUTE_KEY, "Dashboard")


def go_to(page: str) -> None:
    st.session_state[ROUTE_KEY] = page


def render_sidebar(*, show_profile: bool = False, models_ready: bool = True) -> None:
    with st.sidebar:
        # Brand Header with Shield SVG Motif
        st.markdown(
            f"""
            <div class="ng-sidebar-logo">
              <svg width="28" height="28" viewBox="0 0 48 48" fill="none">
                <path d="M24 4L6 12V22C6 33.1 13.7 43.4 24 46C34.3 43.4 42 33.1 42 22V12L24 4Z" 
                      fill="#171E27" stroke="#2DD4BF" stroke-width="3" stroke-linejoin="round"/>
                <path d="M16 24L22 30L32 18" stroke="#F8FAFC" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <div class="ng-sidebar-wordmark">NUTRIGUARD</div>
            </div>
            <div class="ng-sidebar-tagline">AI AUTHENTICITY ENGINE</div>
            """,
            unsafe_allow_html=True,
        )

        active = current_route()
        for p in PAGES:
            page_name = p["name"]
            is_active = (page_name == active)
            wrapper_class = "ng-nav-active" if is_active else ""
            st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
            if st.button(page_name, key=f"nav_{page_name}", use_container_width=True):
                go_to(page_name)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:1.8rem;'></div>", unsafe_allow_html=True)

        # Engine Health Status Pill
        dot_color = COLORS["verified"] if models_ready else COLORS["warning"]
        status_text = "Models Online" if models_ready else "Models Initializing"
        st.markdown(
            f"""
            <div style="background:{COLORS['bg_surface']}; border:1px solid {COLORS['line']}; border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:1.2rem; display:flex; align-items:center; justify-content:space-between;">
              <div style="display:flex; align-items:center;">
                <span class="ng-status-dot" style="background:{dot_color}; color:{dot_color};"></span>
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:{COLORS['text_primary']}; font-weight:600;">{status_text}</span>
              </div>
              <span style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:{COLORS['accent']};">CUDA/CPU</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Authenticated User Profile & Logout
        user = auth.current_user()
        if user:
            avatar_html = ""
            if user.avatar_url:
                avatar_html = f'<img src="{user.avatar_url}" style="width:34px; height:34px; border-radius:50%; border:1.5px solid {COLORS["accent"]}; object-fit:cover;" />'
            else:
                initial = (user.display_name[:1] if user.display_name else "U").upper()
                avatar_html = f'<div style="width:34px; height:34px; border-radius:50%; background:{COLORS["bg_surface_raised"]}; border:1.5px solid {COLORS["accent"]}; display:flex; align-items:center; justify-content:center; font-weight:700; color:{COLORS["accent"]}; font-size:0.85rem;">{initial}</div>'

            display_title = user.display_name if not user.is_guest else "Guest Evaluator"
            role_label = "Verified User" if not user.is_guest else "Guest Mode"

            st.markdown(
                f"""
                <div style="background:{COLORS['bg_surface']}; border:1px solid {COLORS['line']}; border-radius:8px; padding:0.75rem; margin-top:0.5rem;">
                  <div style="display:flex; align-items:center; gap:10px; margin-bottom:0.6rem;">
                    {avatar_html}
                    <div style="overflow:hidden;">
                      <div style="font-family:'Outfit',sans-serif; font-size:0.88rem; font-weight:600; color:{COLORS['text_primary']}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {html.escape(display_title)}
                      </div>
                      <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:{COLORS['accent']};">
                        {role_label}
                      </div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Sign Out", key="sidebar_sign_out", use_container_width=True):
                auth.sign_out()
                st.session_state.pop("verification_result", None)
                st.rerun()
