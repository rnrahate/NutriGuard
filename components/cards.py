"""
Rich card components for NutriGuard.
Includes circular confidence gauge, scanner overlay, prominent result cards, and empty states.
"""
from __future__ import annotations

import base64
import html
import io
import math
from typing import List, Optional, Tuple

from PIL import Image
import streamlit as st

from components.styles import COLORS, render_html


def feature_card(label: str, title: str, body: str, icon_svg: Optional[str] = None) -> None:
    icon_html = f'<div style="color:{COLORS["accent"]}; margin-bottom:0.75rem;">{icon_svg}</div>' if icon_svg else ""
    render_html(
        f"""
        <div class="ng-card" style="height:100%;">
          {icon_html}
          <div class="ng-card-label">{html.escape(label)}</div>
          <div class="ng-card-title">{html.escape(title)}</div>
          <div class="ng-card-body">{html.escape(body)}</div>
        </div>
        """
    )


def circular_confidence_gauge(value: float, label: str = "CONFIDENCE", color: Optional[str] = None) -> None:
    """
    Renders an animated SVG circular gauge for confidence visualization.
    """
    pct = max(0.0, min(1.0, value)) * 100
    gauge_color = color or COLORS["accent"]

    # Circle math
    radius = 42
    circumference = 2 * math.pi * radius
    dashoffset = circumference * (1 - (pct / 100.0))

    render_html(
        f"""
        <div style="text-align:center; padding: 0.75rem 0;">
          <div style="position:relative; width:120px; height:120px; margin:0 auto;">
            <svg width="120" height="120" viewBox="0 0 100 100">
              <!-- Background Track -->
              <circle cx="50" cy="50" r="{radius}" fill="none" stroke="{COLORS['line']}" stroke-width="8" />
              <!-- Animated Progress Bar -->
              <circle cx="50" cy="50" r="{radius}" fill="none" stroke="{gauge_color}" stroke-width="8"
                      stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{dashoffset:.2f}"
                      stroke-linecap="round" transform="rotate(-90 50 50)"
                      style="transition: stroke-dashoffset 1s ease-in-out;" />
            </svg>
            <div style="position:absolute; top:0; left:0; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center;">
              <div style="font-family:'JetBrains Mono',monospace; font-size:1.45rem; font-weight:700; color:{COLORS['text_primary']}; line-height:1;">
                {pct:.1f}%
              </div>
            </div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:600; color:{COLORS['text_muted']}; letter-spacing:0.06em; margin-top:0.6rem;">
            {html.escape(label)}
          </div>
        </div>
        """
    )


def confidence_bar(value: float, label: str = "CONFIDENCE", color: Optional[str] = None) -> None:
    pct = max(0.0, min(1.0, value)) * 100
    bar_color = color or COLORS["accent"]
    render_html(
        f"""
        <div style="margin-bottom:0.8rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;">
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:{COLORS['text_muted']}; letter-spacing:0.04em;">{html.escape(label)}</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:1.15rem; font-weight:700; color:{COLORS['text_primary']};">{pct:.2f}%</span>
          </div>
          <div style="width:100%; height:8px; background:{COLORS['line']}; border-radius:4px; overflow:hidden;">
            <div style="height:100%; width:{pct:.2f}%; background:{bar_color}; border-radius:4px; transition:width 0.8s ease;"></div>
          </div>
        </div>
        """
    )


def image_scanner_box(image: Image.Image, is_scanning: bool = False, caption: Optional[str] = None) -> None:
    """
    Renders an image wrapped in a computer-vision scanner frame with animated laser lines and crosshairs.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    scan_line_html = '<div class="ng-scanner-line"></div>' if is_scanning else ""
    hud_html = """
    <div class="ng-scanner-hud">
      <span class="ng-status-dot" style="background:#2DD4BF; color:#2DD4BF;"></span>
      <span>ANALYZING IMAGE · NEURAL SCAN IN PROGRESS</span>
    </div>
    """ if is_scanning else ""

    render_html(
        f"""
        <div class="ng-scanner-box">
          <div class="ng-scanner-crosshair-tl"></div>
          <div class="ng-scanner-crosshair-tr"></div>
          <div class="ng-scanner-crosshair-bl"></div>
          <div class="ng-scanner-crosshair-br"></div>
          {scan_line_html}
          {hud_html}
          <img src="data:image/png;base64,{img_b64}" style="width:100%; height:auto; display:block; object-fit:contain; max-height:480px; background:#0B0F14;" />
        </div>
        """
    )
    if caption:
        st.caption(caption)


def stage_card(label: str, title: str, rows: List[Tuple[str, str]]) -> None:
    rows_html = "".join(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; padding:0.45rem 0; border-bottom:1px solid {COLORS['line']}; font-size:0.92rem;">
          <span style="color:{COLORS['text_muted']};">{html.escape(k)}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-weight:600; color:{COLORS['text_primary']};">{html.escape(v)}</span>
        </div>
        """
        for k, v in rows
    )
    render_html(
        f"""
        <div class="ng-card">
          <div class="ng-card-label">{html.escape(label)}</div>
          <div class="ng-card-title">{html.escape(title)}</div>
          {rows_html}
        </div>
        """
    )


def final_result_card(
    decision: str,
    body: str,
    *,
    food_name: Optional[str] = None,
    food_conf: Optional[float] = None,
    authenticity_label: Optional[str] = None,
    ai_prob: Optional[float] = None,
    fusion_score: Optional[float] = None,
) -> None:
    """
    Prominent result presentation with clean qualitative indicators.
    Ambiguous raw scores and probability metrics are removed from the upfront UI.
    """
    if decision == "AUTHENTIC":
        theme_class = "ng-result-verified"
        badge_text = "AUTHENTIC FOOD IMAGE"
        badge_icon = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>"""
        badge_color = COLORS["verified"]
        status_text = "VERIFIED AUTHENTIC"
        integrity_text = "NATURAL PHOTOGRAPH"
        audit_text = "PASSED INTEGRITY GATES"
    elif decision in ("POTENTIALLY_AI_GENERATED", "SUSPECTED_AI"):
        theme_class = "ng-result-warning"
        badge_text = "SUSPECTED MODERN AI GENERATION" if decision == "SUSPECTED_AI" else "POTENTIALLY AI-GENERATED"
        badge_icon = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>"""
        badge_color = COLORS["alert"]
        status_text = "SYNTHETIC FLAGGED"
        integrity_text = "DIFFUSION PATTERNS DETECTED"
        audit_text = "SYNTHESIS ALERT"
    else:
        theme_class = "ng-result-alert"
        badge_text = "UNABLE TO VERIFY"
        badge_icon = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>"""
        badge_color = COLORS["warning"]
        status_text = "UNCONFIRMED SUBJECT"
        integrity_text = "INSUFFICIENT FIDELITY"
        audit_text = "GATE WITHHELD"

    # Qualitative integrity metadata row (clean, non-ambiguous)
    metrics_items = []
    # Only display IDENTIFIED DISH if food authenticity is satisfied
    if decision == "AUTHENTIC" and food_name:
        metrics_items.append(f"""
          <div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:{COLORS['text_muted']}; letter-spacing:0.04em;">IDENTIFIED DISH</div>
            <div style="font-family:'Outfit',sans-serif; font-size:1.18rem; font-weight:700; color:{COLORS['text_primary']};">{html.escape(food_name)}</div>
          </div>
        """)
    metrics_items.append(f"""
      <div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:{COLORS['text_muted']}; letter-spacing:0.04em;">AUTHENTICITY STATUS</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:1.05rem; font-weight:700; color:{badge_color};">{status_text}</div>
      </div>
    """)
    metrics_items.append(f"""
      <div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:{COLORS['text_muted']}; letter-spacing:0.04em;">VISUAL INTEGRITY</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:1.05rem; font-weight:700; color:{COLORS['text_primary']};">{integrity_text}</div>
      </div>
    """)
    metrics_items.append(f"""
      <div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:{COLORS['text_muted']}; letter-spacing:0.04em;">AUDIT ASSESSMENT</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:1.05rem; font-weight:700; color:{COLORS['accent']};">{audit_text}</div>
      </div>
    """)

    metrics_html = f"""
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:16px; margin: 1.2rem 0; padding: 1rem 1.2rem; background:rgba(11,15,20,0.6); border:1px solid {COLORS['line']}; border-radius:8px;">
      {"".join(metrics_items)}
    </div>
    """ if metrics_items else ""

    render_html(
        f"""
        <div class="ng-result-card {theme_class}">
          <div class="ng-result-title" style="color:{badge_color};">
            {badge_icon}
            <span>{badge_text}</span>
          </div>
          <div class="ng-result-body">
            {html.escape(body)}
          </div>
          {metrics_html}
        </div>
        """
    )


def verification_audit_panel(
    decision: str,
    food_name: str,
    passed_gate: bool,
    yolo_detected: bool = False,
    candidate_classes: Optional[List[str]] = None,
) -> None:
    """
    Renders an elegant, clean verification audit breakdown.
    Displays findings for food recognition, artifact scanning, and multi-stage pipeline flow
    without any ambiguous numeric scores or probabilities.
    If food authenticity is not satisfied, the identified dish is withheld.
    """
    is_authentic = (decision == "AUTHENTIC")

    if is_authentic:
        auth_status = "Natural Photographic Composition"
        auth_color = COLORS["verified"]
        artifact_status = "No Generative Artifacts Detected"
        artifact_color = COLORS["verified"]
        consensus_status = "Certified Natural Photograph"
        consensus_badge = "✓ AUTHENTIC"
        consensus_badge_bg = COLORS["verified_bg"]
        consensus_badge_border = COLORS["verified_border"]
    elif decision in ("POTENTIALLY_AI_GENERATED", "SUSPECTED_AI"):
        auth_status = "Diffusion Micro-Patterns Detected" if decision == "SUSPECTED_AI" else "Synthetic AI Signatures Detected"
        auth_color = COLORS["alert"]
        artifact_status = "Frequency / Diffusion Inconsistencies Found"
        artifact_color = COLORS["alert"]
        consensus_status = "Flagged as Suspected AI Content"
        consensus_badge = "⚠ SUSPECTED AI"
        consensus_badge_bg = COLORS["alert_bg"]
        consensus_badge_border = COLORS["alert_border"]
    else:
        auth_status = "Verification Gate Withheld"
        auth_color = COLORS["warning"]
        artifact_status = "Analysis Withheld (Low Quality Input)"
        artifact_color = COLORS["warning"]
        consensus_status = "Verification Inconclusive"
        consensus_badge = "● UNVERIFIED"
        consensus_badge_bg = COLORS["warning_bg"]
        consensus_badge_border = COLORS["warning_border"]

    cat_badge = "Confirmed Food Item" if passed_gate else "Unrecognized Subject"
    cat_color = COLORS["verified"] if passed_gate else COLORS["warning"]

    # Identified Subject row: only display dish name if authenticity is satisfied
    if is_authentic and food_name:
        subject_row = f"""
          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']};">Identified Subject</span>
            <span style="font-family:'Outfit',sans-serif; font-weight:600; color:{COLORS['text_primary']};">
              {html.escape(food_name)}
              <span style="display:inline-block; font-family:'JetBrains Mono',monospace; font-size:0.72rem; padding:2px 8px; border-radius:12px; background:rgba(45,212,191,0.08); border:1px solid rgba(45,212,191,0.25); color:{cat_color}; margin-left:6px;">
                {cat_badge}
              </span>
            </span>
          </div>
        """
    else:
        subject_row = f"""
          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']};">Identified Subject</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:600; color:{COLORS['text_dim']};">
              Withheld (Authenticity Not Satisfied)
            </span>
          </div>
        """

    # 1. Verification Audit Summary Card
    render_html(
        f"""
        <div class="ng-card">
          <div class="ng-card-label">VERIFICATION AUDIT</div>
          <div class="ng-card-title">Inspection Summary</div>
          
          {subject_row}

          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']};">Authenticity Scan</span>
            <span style="font-family:'JetBrains Mono',monospace; font-weight:600; color:{auth_color};">
              {auth_status}
            </span>
          </div>

          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']};">Micro-Artifact Analysis</span>
            <span style="font-family:'JetBrains Mono',monospace; font-weight:500; color:{artifact_color};">
              {artifact_status}
            </span>
          </div>

          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']};">Evaluation Consensus</span>
            <span style="display:inline-flex; align-items:center; gap:6px; font-family:'JetBrains Mono',monospace; font-weight:600; font-size:0.78rem; padding:3px 10px; border-radius:6px; background:{consensus_badge_bg}; border:1px solid {consensus_badge_border}; color:{auth_color};">
              {consensus_badge}
            </span>
          </div>
        </div>
        """
    )

    # 2. Multi-Stage Pipeline Execution Audit Card
    stage1_status = "Food Subject Isolated" if yolo_detected else "Full Image Frame Scanned"
    stage2_status = f"Identified as {food_name}" if is_authentic else "Withheld (Authenticity Failed)"
    stage2_icon = "✓" if is_authentic else "●"
    stage2_color = COLORS['text_primary'] if is_authentic else COLORS['text_dim']

    stage3_status = "Quality Gate Passed" if passed_gate else "Below Confidence Gate"
    stage3_color = COLORS["verified"] if passed_gate else COLORS["warning"]
    
    if not passed_gate:
        stage4_status = "Analysis Withheld (Gated Input)"
        stage4_color = COLORS["text_dim"]
    elif is_authentic:
        stage4_status = "Natural Photographic Texture"
        stage4_color = COLORS["verified"]
    else:
        stage4_status = "AI Synthesis Signatures Flagged"
        stage4_color = COLORS["alert"]

    stage5_color = auth_color

    render_html(
        f"""
        <div class="ng-card">
          <div class="ng-card-label">ARCHITECTURE EXECUTION AUDIT</div>
          <div class="ng-card-title">Pipeline Stage Findings</div>

          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']}; font-family:'JetBrains Mono',monospace; font-size:0.82rem;">01 · YOLO Localization</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:600; color:{COLORS['text_primary']};">✓ {html.escape(stage1_status)}</span>
          </div>

          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']}; font-family:'JetBrains Mono',monospace; font-size:0.82rem;">02 · Food Recognition</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:600; color:{stage2_color};">{stage2_icon} {html.escape(stage2_status)}</span>
          </div>

          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']}; font-family:'JetBrains Mono',monospace; font-size:0.82rem;">03 · Confidence Gate</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:600; color:{stage3_color};">● {html.escape(stage3_status)}</span>
          </div>

          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']}; font-family:'JetBrains Mono',monospace; font-size:0.82rem;">04 · Authenticity Scan</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:600; color:{stage4_color};">● {html.escape(stage4_status)}</span>
          </div>

          <div class="ng-audit-row">
            <span style="color:{COLORS['text_muted']}; font-family:'JetBrains Mono',monospace; font-size:0.82rem;">05 · Verdict Synthesis</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:600; color:{stage5_color};">● {html.escape(consensus_status)}</span>
          </div>
        </div>
        """
    )

    # 3. Culinary Category Matches (Only displayed if food authenticity is satisfied)
    if is_authentic and candidate_classes and len(candidate_classes) > 1:
        tags_html = "".join(
            f'<span class="ng-tag-muted">{html.escape(c)}</span>'
            for c in candidate_classes[1:]
        )
        render_html(
            f"""
            <div class="ng-card">
              <div class="ng-card-label">CULINARY CATEGORIZATION</div>
              <div class="ng-card-title">Category Matches</div>
              <div style="color:{COLORS['text_secondary']}; font-size:0.86rem; margin-bottom:0.75rem;">
                Primary identification and alternative culinary classifications:
              </div>
              <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center;">
                <span class="ng-tag-primary">✓ {html.escape(food_name)} (Primary)</span>
                {tags_html}
              </div>
            </div>
            """
        )


def empty_state(title: str, description: str, icon_type: str = "image") -> None:
    """
    Renders high-contrast technical empty state illustration.
    """
    if icon_type == "history":
        icon_svg = """<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>"""
    else:
        icon_svg = """<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>"""

    render_html(
        f"""
        <div class="ng-card" style="text-align:center; padding: 3rem 1.5rem; margin: 1.5rem 0;">
          <div style="display:inline-flex; align-items:center; justify-content:center; width:72px; height:72px; border-radius:50%; background:rgba(45,212,191,0.08); border:1px solid rgba(45,212,191,0.2); margin-bottom:1rem;">
            {icon_svg}
          </div>
          <div style="font-family:'Outfit',sans-serif; font-size:1.25rem; font-weight:600; color:{COLORS['text_primary']}; margin-bottom:0.4rem;">
            {html.escape(title)}
          </div>
          <div style="color:{COLORS['text_muted']}; max-width:420px; margin:0 auto; font-size:0.94rem; line-height:1.5;">
            {html.escape(description)}
          </div>
        </div>
        """
    )


# Backwards compatibility helper for existing references
def final_result_state(state: str, body: str, title: Optional[str] = None) -> None:
    decision_map = {
        "verified": "AUTHENTIC",
        "warning": "POTENTIALLY_AI_GENERATED",
        "alert": "UNABLE_TO_VERIFY",
    }
    final_result_card(decision_map.get(state, "UNABLE_TO_VERIFY"), body)
