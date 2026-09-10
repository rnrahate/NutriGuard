"""
Design tokens + global CSS for NutriGuard.
Sleek, dark, high-contrast digital trust & computer vision security aesthetic.
"""
import streamlit as st

COLORS = {
    # Deep background layers
    "bg_darkest": "#0B0F14",
    "bg_dark": "#10161D",
    "bg_surface": "#171E27",
    "bg_surface_raised": "#1D2630",
    "bg_surface_hover": "#222D3A",

    # Borders & dividers
    "line": "#222D3D",
    "line_light": "#2E3D52",

    # High-contrast typography
    "text_primary": "#F8FAFC",
    "text_secondary": "#CBD5E1",
    "text_muted": "#94A3B8",
    "text_dim": "#64748B",

    # Accents & Brand
    "accent": "#2DD4BF",
    "accent_mint": "#45D483",
    "accent_glow": "rgba(45, 212, 191, 0.25)",
    "accent_bg": "rgba(45, 212, 191, 0.08)",

    # Verification status tokens
    "verified": "#10B981",
    "verified_bg": "rgba(16, 185, 129, 0.12)",
    "verified_border": "rgba(16, 185, 129, 0.35)",

    "warning": "#F59E0B",
    "warning_bg": "rgba(245, 158, 11, 0.12)",
    "warning_border": "rgba(245, 158, 11, 0.35)",

    "alert": "#EF4444",
    "alert_bg": "rgba(239, 68, 68, 0.12)",
    "alert_border": "rgba(239, 68, 68, 0.35)",

    # Legacy mapping for backwards compatibility with any helper references
    "paper": "#0B0F14",
    "paper_raised": "#171E27",
    "ink": "#F8FAFC",
    "ink_muted": "#94A3B8",
}

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {{
  --ng-bg-darkest: {COLORS['bg_darkest']};
  --ng-bg-dark: {COLORS['bg_dark']};
  --ng-bg-surface: {COLORS['bg_surface']};
  --ng-bg-surface-raised: {COLORS['bg_surface_raised']};
  --ng-bg-surface-hover: {COLORS['bg_surface_hover']};
  --ng-line: {COLORS['line']};
  --ng-line-light: {COLORS['line_light']};
  --ng-text-primary: {COLORS['text_primary']};
  --ng-text-secondary: {COLORS['text_secondary']};
  --ng-text-muted: {COLORS['text_muted']};
  --ng-accent: {COLORS['accent']};
  --ng-accent-mint: {COLORS['accent_mint']};
  --ng-accent-glow: {COLORS['accent_glow']};
  --ng-verified: {COLORS['verified']};
  --ng-verified-bg: {COLORS['verified_bg']};
  --ng-warning: {COLORS['warning']};
  --ng-warning-bg: {COLORS['warning_bg']};
  --ng-alert: {COLORS['alert']};
  --ng-alert-bg: {COLORS['alert_bg']};
}}

/* ================= Global App Background & Base Typography ================= */
html, body, [data-testid="stAppViewContainer"] {{
  background-color: {COLORS['bg_darkest']} !important;
  color: {COLORS['text_primary']} !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: -0.01em;
}}

/* Subtle ambient dark gradient */
[data-testid="stAppViewContainer"] {{
  background: radial-gradient(circle at 50% 0%, #151F2B 0%, #0B0F14 70%) fixed !important;
}}

[data-testid="stHeader"] {{
  background: transparent !important;
}}
#MainMenu, footer {{
  visibility: hidden;
}}

/* Clean Typography Hierarchy */
h1, .ng-h1 {{
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
  font-size: 2.2rem !important;
  letter-spacing: -0.03em !important;
  color: {COLORS['text_primary']} !important;
  margin-bottom: 0.5rem !important;
}}

h2, .ng-h2 {{
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  font-size: 1.5rem !important;
  letter-spacing: -0.02em !important;
  color: {COLORS['text_primary']} !important;
  margin-top: 0.8rem !important;
  margin-bottom: 0.4rem !important;
}}

h3, .ng-h3 {{
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  font-size: 1.15rem !important;
  color: {COLORS['text_primary']} !important;
  margin-bottom: 0.3rem !important;
}}

p, [data-testid="stMarkdownContainer"] p {{
  color: {COLORS['text_secondary']} !important;
  font-size: 0.96rem;
  line-height: 1.6;
}}

[data-testid="stCaptionContainer"] p, .stCaption {{
  color: {COLORS['text_muted']} !important;
  font-size: 0.84rem !important;
}}

/* ================= Sidebar Overrides ================= */
[data-testid="stSidebar"] {{
  background-color: {COLORS['bg_dark']} !important;
  border-right: 1px solid {COLORS['line']} !important;
}}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
  color: {COLORS['text_secondary']} !important;
}}

.ng-sidebar-logo {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0.25rem;
}}

.ng-sidebar-wordmark {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: {COLORS['text_primary']};
}}

.ng-sidebar-tagline {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  color: {COLORS['accent']};
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 1.4rem;
}}

/* Sidebar navigation buttons */
[data-testid="stSidebar"] [data-testid="stButton"] button {{
  width: 100%;
  text-align: left;
  justify-content: flex-start;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: {COLORS['text_secondary']} !important;
  font-weight: 500;
  font-size: 0.92rem;
  padding: 0.65rem 0.85rem;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}}

[data-testid="stSidebar"] [data-testid="stButton"] button:hover {{
  background: {COLORS['bg_surface_raised']} !important;
  color: {COLORS['accent']} !important;
  border-color: {COLORS['line_light']} !important;
  transform: translateX(3px);
}}

[data-testid="stSidebar"] [data-testid="stButton"] button:active,
[data-testid="stSidebar"] [data-testid="stButton"] button:focus,
[data-testid="stSidebar"] [data-testid="stButton"] button:focus-visible {{
  background: {COLORS['bg_surface_raised']} !important;
  color: {COLORS['accent']} !important;
  border: 1.5px solid {COLORS['accent']} !important;
  box-shadow: 0 0 16px rgba(45, 212, 191, 0.3) !important;
  outline: none !important;
}}

.ng-nav-active button {{
  background: {COLORS['bg_surface_raised']} !important;
  color: {COLORS['accent']} !important;
  border: 1.5px solid {COLORS['accent']} !important;
  box-shadow: 0 0 18px rgba(45, 212, 191, 0.25) !important;
  font-weight: 700 !important;
}}

/* Ensure all elements inside buttons inherit the high-contrast text color */
[data-testid="stButton"] button * {{
  color: inherit !important;
}}

/* Status dot pulse */
.ng-status-dot {{
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  box-shadow: 0 0 8px currentColor;
  animation: pulseDot 2s infinite ease-in-out;
}}

@keyframes pulseDot {{
  0%, 100% {{ opacity: 1; transform: scale(1); }}
  50% {{ opacity: 0.6; transform: scale(1.15); }}
}}

/* ================= Action Buttons ================= */
[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="primary"] {{
  background: linear-gradient(135deg, #2DD4BF 0%, #10B981 100%) !important;
  border: 1px solid #2DD4BF !important;
  color: #0B0F14 !important;
  border-radius: 8px !important;
  padding: 0.65rem 1.4rem !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  letter-spacing: -0.01em !important;
  box-shadow: 0 4px 14px rgba(45, 212, 191, 0.3) !important;
  transition: all 0.2s ease !important;
}}

[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="primary"]:hover {{
  box-shadow: 0 6px 22px rgba(45, 212, 191, 0.5) !important;
  transform: translateY(-1px) !important;
  filter: brightness(1.08) !important;
  color: #0B0F14 !important;
}}

[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="primary"]:active,
[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="primary"]:focus,
[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="primary"]:focus-visible {{
  background: #2DD4BF !important;
  border: 2px solid #FFFFFF !important;
  color: #0B0F14 !important;
  box-shadow: 0 0 24px rgba(45, 212, 191, 0.7) !important;
  transform: scale(0.98) !important;
  outline: none !important;
}}

[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="secondary"] {{
  background: {COLORS['bg_surface']} !important;
  border: 1.5px solid {COLORS['line']} !important;
  color: {COLORS['text_primary']} !important;
  border-radius: 8px !important;
  padding: 0.65rem 1.4rem !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
  transition: all 0.2s ease !important;
}}

[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="secondary"]:hover {{
  border-color: {COLORS['accent']} !important;
  color: {COLORS['accent']} !important;
  background: {COLORS['bg_surface_raised']} !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 14px rgba(45, 212, 191, 0.2) !important;
}}

[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="secondary"]:active,
[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="secondary"]:focus,
[data-testid="stAppViewContainer"] [data-testid="stButton"] button[kind="secondary"]:focus-visible {{
  border-color: {COLORS['accent']} !important;
  color: #FFFFFF !important;
  background: {COLORS['bg_surface_raised']} !important;
  box-shadow: 0 0 20px rgba(45, 212, 191, 0.4) !important;
  transform: scale(0.98) !important;
  outline: none !important;
}}

/* ================= Cards & Containers ================= */
.ng-card {{
  background: {COLORS['bg_surface']};
  border: 1px solid {COLORS['line']};
  border-radius: 10px;
  padding: 1.4rem 1.5rem;
  margin-bottom: 1.1rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  transition: border-color 0.2s ease, transform 0.2s ease;
}}

.ng-card:hover {{
  border-color: {COLORS['line_light']};
}}

.ng-card-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  color: {COLORS['accent']};
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}}

.ng-card-title {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.18rem;
  font-weight: 600;
  color: {COLORS['text_primary']};
  margin-bottom: 0.4rem;
}}

.ng-card-body {{
  color: {COLORS['text_secondary']};
  font-size: 0.92rem;
  line-height: 1.55;
}}

/* ================= Branded Auth Gate ================= */
.ng-auth-container {{
  text-align: center;
  max-width: 620px;
  margin: 1.5rem auto 1.2rem auto;
  padding: 0 1rem;
}}

.ng-auth-motif {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  background: radial-gradient(circle, rgba(45, 212, 191, 0.15) 0%, rgba(15, 23, 42, 0) 70%);
  border-radius: 50%;
  margin-bottom: 0.8rem;
  box-shadow: 0 0 30px rgba(45, 212, 191, 0.2);
  animation: floatShield 4s ease-in-out infinite;
}}

@keyframes floatShield {{
  0%, 100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-4px); }}
}}

.ng-auth-title {{
  font-family: 'Outfit', sans-serif;
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  color: {COLORS['text_primary']};
  margin-bottom: 0.2rem;
}}

.ng-auth-tagline {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.92rem;
  font-weight: 600;
  color: {COLORS['accent']};
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 0.6rem;
}}

.ng-auth-subtitle {{
  font-size: 0.96rem;
  color: {COLORS['text_muted']};
  line-height: 1.5;
  max-width: 480px;
  margin: 0 auto 1.2rem auto;
}}

.ng-auth-divider {{
  position: relative;
  width: 100%;
  max-width: 380px;
  height: 2px;
  background: linear-gradient(90deg, transparent, {COLORS['line']}, transparent);
  margin: 1rem auto 1.4rem auto;
  overflow: hidden;
}}

.ng-auth-laser-beam {{
  position: absolute;
  top: 0;
  left: -40%;
  width: 40%;
  height: 100%;
  background: linear-gradient(90deg, transparent, {COLORS['accent']}, transparent);
  animation: laserScan 2.5s infinite ease-in-out;
}}

@keyframes laserScan {{
  0% {{ left: -40%; }}
  100% {{ left: 100%; }}
}}

/* ================= 5-Stage Verification Pipeline ================= */
.ng-pipeline-container {{
  background: {COLORS['bg_surface']};
  border: 1px solid {COLORS['line']};
  border-radius: 12px;
  padding: 1.25rem 1.4rem;
  margin: 1.2rem 0 1.6rem 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}}

.ng-pipeline-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid {COLORS['line']};
}}

.ng-pipeline-title {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.98rem;
  font-weight: 600;
  color: {COLORS['text_primary']};
  display: flex;
  align-items: center;
  gap: 8px;
}}

.ng-pipeline-status-badge {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  letter-spacing: 0.04em;
}}

.ng-pipeline-grid {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  position: relative;
}}

.ng-stage-node {{
  background: {COLORS['bg_surface_raised']};
  border: 1px solid {COLORS['line']};
  border-radius: 8px;
  padding: 0.85rem 0.75rem;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: all 0.25s ease;
}}

.ng-stage-node.done {{
  border-color: {COLORS['verified_border']};
  background: rgba(16, 185, 129, 0.06);
}}

.ng-stage-node.active {{
  border-color: {COLORS['accent']};
  background: rgba(45, 212, 191, 0.08);
  box-shadow: 0 0 16px rgba(45, 212, 191, 0.2);
}}

.ng-stage-node.failed {{
  border-color: {COLORS['alert_border']};
  background: rgba(239, 68, 68, 0.08);
}}

.ng-stage-node.waiting {{
  opacity: 0.7;
}}

.ng-stage-top {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}}

.ng-stage-num {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 600;
  color: {COLORS['text_muted']};
}}

.ng-stage-icon {{
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}}

.ng-stage-name {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  color: {COLORS['text_primary']};
  line-height: 1.2;
  margin-bottom: 0.2rem;
}}

.ng-stage-engine {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: {COLORS['accent']};
  margin-bottom: 0.4rem;
}}

.ng-stage-status {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
}}

/* ================= Image Scanner Effect ================= */
.ng-scanner-box {{
  position: relative;
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid {COLORS['accent']};
  box-shadow: 0 0 24px rgba(45, 212, 191, 0.25);
  margin: 1rem 0;
}}

.ng-scanner-line {{
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, #2DD4BF, #45D483, #2DD4BF, transparent);
  box-shadow: 0 0 14px #2DD4BF, 0 0 28px #45D483;
  z-index: 10;
  animation: scanVertical 2.2s infinite ease-in-out;
}}

@keyframes scanVertical {{
  0% {{ top: 0%; opacity: 0.8; }}
  50% {{ top: 96%; opacity: 1; }}
  100% {{ top: 0%; opacity: 0.8; }}
}}

.ng-scanner-hud {{
  position: absolute;
  bottom: 12px;
  left: 12px;
  background: rgba(11, 15, 20, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(45, 212, 191, 0.4);
  border-radius: 6px;
  padding: 6px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: {COLORS['accent']};
  z-index: 12;
}}

.ng-scanner-crosshair-tl {{
  position: absolute; top: 8px; left: 8px; width: 14px; height: 14px;
  border-top: 2px solid {COLORS['accent']}; border-left: 2px solid {COLORS['accent']}; z-index: 11;
}}
.ng-scanner-crosshair-tr {{
  position: absolute; top: 8px; right: 8px; width: 14px; height: 14px;
  border-top: 2px solid {COLORS['accent']}; border-right: 2px solid {COLORS['accent']}; z-index: 11;
}}
.ng-scanner-crosshair-bl {{
  position: absolute; bottom: 8px; left: 8px; width: 14px; height: 14px;
  border-bottom: 2px solid {COLORS['accent']}; border-left: 2px solid {COLORS['accent']}; z-index: 11;
}}
.ng-scanner-crosshair-br {{
  position: absolute; bottom: 8px; right: 8px; width: 14px; height: 14px;
  border-bottom: 2px solid {COLORS['accent']}; border-right: 2px solid {COLORS['accent']}; z-index: 11;
}}

/* ================= Result States ================= */
.ng-result-card {{
  border-radius: 12px;
  padding: 1.8rem 2rem;
  margin: 1.2rem 0;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5);
  animation: fadeInUp 0.4s ease-out forwards;
}}

@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

.ng-result-verified {{
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.14) 0%, rgba(15, 23, 42, 0.8) 100%);
  border: 1.5px solid {COLORS['verified']};
  box-shadow: 0 0 30px rgba(16, 185, 129, 0.2);
}}

.ng-result-warning {{
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.14) 0%, rgba(15, 23, 42, 0.8) 100%);
  border: 1.5px solid {COLORS['alert']};
  box-shadow: 0 0 30px rgba(239, 68, 68, 0.2);
}}

.ng-result-alert {{
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.14) 0%, rgba(15, 23, 42, 0.8) 100%);
  border: 1.5px solid {COLORS['warning']};
  box-shadow: 0 0 30px rgba(245, 158, 11, 0.2);
}}

.ng-result-title {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.55rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0.6rem;
}}

.ng-result-body {{
  color: {COLORS['text_secondary']};
  font-size: 1.02rem;
  line-height: 1.6;
  margin-bottom: 1.2rem;
}}

/* ================= Streamlit Native Controls Customization ================= */
[data-testid="stFileUploader"] {{
  background: {COLORS['bg_surface']} !important;
  border: 1.5px dashed {COLORS['line_light']} !important;
  border-radius: 10px !important;
  padding: 1.2rem !important;
  transition: all 0.2s ease !important;
}}

[data-testid="stFileUploader"]:hover {{
  border-color: {COLORS['accent']} !important;
  box-shadow: 0 0 16px rgba(45, 212, 191, 0.15) !important;
}}

[data-testid="stCameraInput"] {{
  background: {COLORS['bg_surface']} !important;
  border: 1px solid {COLORS['line']} !important;
  border-radius: 10px !important;
  padding: 0.8rem !important;
}}

[data-testid="stTabs"] button[role="tab"] {{
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  color: {COLORS['text_muted']} !important;
  border-bottom: 2px solid transparent !important;
  padding: 0.5rem 1rem !important;
}}

[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
  color: {COLORS['accent']} !important;
  border-bottom-color: {COLORS['accent']} !important;
}}

[data-testid="stExpander"] {{
  background: {COLORS['bg_surface']} !important;
  border: 1px solid {COLORS['line']} !important;
  border-radius: 8px !important;
  margin-top: 0.6rem !important;
}}

[data-testid="stMetricValue"] {{
  font-family: 'JetBrains Mono', monospace !important;
  color: {COLORS['text_primary']} !important;
  font-size: 1.8rem !important;
  font-weight: 600 !important;
}}

[data-testid="stMetricLabel"] {{
  color: {COLORS['text_muted']} !important;
  font-family: 'Outfit', sans-serif !important;
  font-size: 0.85rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.04em !important;
}}

hr {{
  border-color: {COLORS['line']} !important;
  margin: 1.4rem 0 !important;
}}

/* ================= Responsive Adjustments ================= */
@media (max-width: 768px) {{
  .ng-pipeline-grid {{
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }}
  .ng-stage-node {{
    padding: 0.75rem 1rem !important;
  }}
  h1, .ng-h1 {{
    font-size: 1.7rem !important;
  }}
  .ng-auth-title {{
    font-size: 1.8rem !important;
  }}
}}
</style>
"""


def inject_global_styles() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def render_html(raw_html: str) -> None:
    """Renders HTML safely in Streamlit without risk of markdown indentation code block parsing."""
    clean = "\n".join(line.strip() for line in raw_html.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)
