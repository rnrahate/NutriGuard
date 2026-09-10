"""
NutriGuard 5-Stage Verification Pipeline component.
Responsive horizontal pipeline on desktop, vertical stack on mobile, with real-time active animations.
"""
from __future__ import annotations

import html
from typing import Dict, List, Optional
import streamlit as st

STAGE_CONFIGS = [
    {
        "num": "01",
        "name": "Food Detection",
        "engine": "YOLO Localization",
        "desc": "Detects food boundaries & multi-item layout",
        "icon": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/></svg>""",
    },
    {
        "num": "02",
        "name": "Food Classification",
        "engine": "ResNet-101 · Food-101",
        "desc": "Identifies dish across 101 food categories",
        "icon": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>""",
    },
    {
        "num": "03",
        "name": "Confidence Gate",
        "engine": "Threshold Filter (80%)",
        "desc": "Gates non-food & low-confidence inputs",
        "icon": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>""",
    },
    {
        "num": "04",
        "name": "Authenticity Check",
        "engine": "CIFAKE · ResNet-101",
        "desc": "Inspects diffusion & GAN artifact signatures",
        "icon": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>""",
    },
    {
        "num": "05",
        "name": "Final Decision",
        "engine": "Evidence Synthesis",
        "desc": "Synthesizes multi-model authenticity verdict",
        "icon": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>""",
    },
]


def render_pipeline_card(stage_states: Dict[str, str], current_summary: Optional[str] = None) -> None:
    """
    Renders the 5-stage verification architecture pipeline.
    stage_states: mapping from stage index string ("01" to "05") to status:
      "done", "active", "waiting", "failed", "skipped"
    """
    nodes_html = []
    for cfg in STAGE_CONFIGS:
        s_num = cfg["num"]
        state = stage_states.get(s_num, "waiting")

        if state == "done":
            status_text = "✓ Completed"
            status_color = "#10B981"
            icon_color = "#10B981"
        elif state == "active":
            status_text = "● Processing..."
            status_color = "#2DD4BF"
            icon_color = "#2DD4BF"
        elif state == "failed":
            status_text = "✕ Failed"
            status_color = "#EF4444"
            icon_color = "#EF4444"
        elif state == "skipped":
            status_text = "— Skipped"
            status_color = "#64748B"
            icon_color = "#64748B"
        else:
            status_text = "● Ready"
            status_color = "#94A3B8"
            icon_color = "#94A3B8"

        node = f"""
        <div class="ng-stage-node {state}">
          <div class="ng-stage-top">
            <span class="ng-stage-num">{s_num}</span>
            <span class="ng-stage-icon" style="color:{icon_color};">{cfg['icon']}</span>
          </div>
          <div class="ng-stage-name">{cfg['name']}</div>
          <div class="ng-stage-engine">{cfg['engine']}</div>
          <div style="font-size:0.72rem; color:#94A3B8; margin-bottom:0.5rem; line-height:1.3;">{cfg['desc']}</div>
          <div class="ng-stage-status" style="color:{status_color};">
            {status_text}
          </div>
        </div>
        """
        nodes_html.append(node)

    summary_bar = ""
    if current_summary:
        summary_bar = f"""
        <div class="ng-pipeline-status-badge" style="background:rgba(45,212,191,0.12); color:#2DD4BF; border:1px solid rgba(45,212,191,0.3);">
          {html.escape(current_summary)}
        </div>
        """
    else:
        summary_bar = """
        <div class="ng-pipeline-status-badge" style="background:#1D2630; color:#CBD5E1; border:1px solid #222D3D;">
          Dual-Model Inference Pipeline
        </div>
        """

    full_html = f"""
    <div class="ng-pipeline-container">
      <div class="ng-pipeline-header">
        <div class="ng-pipeline-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="12 6 12 12 16 14"/></svg>
          Multi-Stage Verification Architecture
        </div>
        {summary_bar}
      </div>
      <div class="ng-pipeline-grid">
        {"".join(nodes_html)}
      </div>
    </div>
    """
    clean_html = "\n".join(line.strip() for line in full_html.splitlines() if line.strip())
    st.markdown(clean_html, unsafe_allow_html=True)


def dashboard_pipeline() -> None:
    """Standard ready-state pipeline for Dashboard view."""
    render_pipeline_card({
        "01": "waiting",
        "02": "waiting",
        "03": "waiting",
        "04": "waiting",
        "05": "waiting",
    }, current_summary="Ready for Image Input")
