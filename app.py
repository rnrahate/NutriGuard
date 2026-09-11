"""
NutriGuard — Food Image Classification & Authenticity Verification Application.
High-contrast technical UI with real-time computer vision pipeline and Clerk authentication.
"""
from __future__ import annotations

import html
import time
from typing import Optional

from PIL import Image, UnidentifiedImageError
import streamlit as st

from components import cards, nav, pipeline, styles
from services import auth, config, history_db, inference, model_loader, yolo_detector

from components.styles import COLORS, inject_global_styles
from services.config import SETTINGS
from services.model_loader import load_checkpoint

# ---------------------------------------------------------------- page setup --
st.set_page_config(
    page_title="NutriGuard — Food Authenticity Verification",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_styles()


# -------------------------------------------------------------------- models --
@st.cache_resource(show_spinner=False)
def get_food_model():
    return load_checkpoint(SETTINGS.food_model_path, SETTINGS.device_pref)


@st.cache_resource(show_spinner=False)
def get_fake_model():
    return load_checkpoint(SETTINGS.fake_model_path, SETTINGS.device_pref)


@st.cache_resource(show_spinner=False)
def get_yolo_model():
    return yolo_detector.load_yolo(SETTINGS.yolo_model_path)


food_model = get_food_model()
fake_model = get_fake_model()
yolo_model, yolo_load_err = get_yolo_model()
models_ready = food_model.loaded and fake_model.loaded


# ---------------------------------------------------------------------- auth --
def require_user() -> Optional[auth.AuthUser]:
    return auth.current_user()


# ----------------------------------------------------------------- dashboard --
def page_dashboard():
    # Hero Section
    st.markdown(
        f"""
        <div style="padding: 1.2rem 0 1.8rem 0;">
          <div style="display:inline-flex; align-items:center; gap:8px; background:{COLORS['bg_surface_raised']}; border:1px solid {COLORS['line_light']}; border-radius:20px; padding:0.35rem 0.9rem; margin-bottom:1rem;">
            <span class="ng-status-dot" style="background:#2DD4BF; color:#2DD4BF;"></span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:{COLORS['accent']}; font-weight:600; letter-spacing:0.06em;">AI DIGITAL TRUST ENGINE</span>
          </div>
          <div style="font-family:'Outfit',sans-serif; font-size:3.2rem; font-weight:800; letter-spacing:-0.03em; color:{COLORS['text_primary']}; line-height:1.1; margin-bottom:0.4rem;">
            NutriGuard
          </div>
          <div style="font-family:'JetBrains Mono',monospace; font-size:1.3rem; font-weight:600; color:{COLORS['accent']}; letter-spacing:0.04em; margin-bottom:0.9rem;">
            VERIFY BEFORE YOU TRUST.
          </div>
          <div style="max-width:720px; color:{COLORS['text_secondary']}; font-size:1.05rem; line-height:1.6; margin-bottom:1.6rem;">
            High-precision food classification and synthetic generation detection.
            Flagging AI-manipulated or misleading food imagery across delivery and review platforms.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Hero Action Buttons
    c1, c2, _ = st.columns([1.2, 1.4, 2.5])
    with c1:
        if st.button("Verify Food Image", type="primary", use_container_width=True):
            st.session_state["verify_mode"] = "Upload Image"
            nav.go_to("Verify Food Image")
            st.rerun()
    with c2:
        if st.button("Capture With Camera", type="secondary", use_container_width=True):
            st.session_state["verify_mode"] = "Use Camera"
            nav.go_to("Verify Food Image")
            st.rerun()

    st.markdown("<div style='height:1.4rem;'></div>", unsafe_allow_html=True)

    # Architecture Pipeline Overview
    pipeline.dashboard_pipeline()

    st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)

    # 3 Technology Pillar Cards
    f1, f2, f3 = st.columns(3)
    with f1:
        cards.feature_card(
            "STAGE 01 · LOCALIZATION",
            "Food Detection",
            "YOLO-based bounding box localization to isolate valid food regions before multi-class classification.",
            icon_svg="""<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/></svg>""",
        )
    with f2:
        cards.feature_card(
            "STAGE 02 · RECOGNITION",
            "Food Classification",
            "ResNet-101 architecture trained on the Food-101 benchmark covering 101 diverse culinary categories.",
            icon_svg="""<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>""",
        )
    with f3:
        cards.feature_card(
            "STAGE 03 · AUTHENTICITY",
            "Synthetic Verification",
            "CIFAKE-trained ResNet-101 model detecting micro-artifacts from diffusion and GAN generators.",
            icon_svg="""<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>""",
        )


# -------------------------------------------------------------------- verify --
def _load_image(source) -> Optional[Image.Image]:
    if source is None:
        return None
    try:
        return Image.open(source)
    except UnidentifiedImageError:
        st.error("That file does not appear to be a valid image. Supported: JPG, PNG, WEBP.")
        return None
    except Exception as exc:  # noqa: BLE001
        st.error(f"Error reading image: {exc}")
        return None


def run_verification(image: Image.Image, user_id: Optional[str]):
    pipeline_slot = st.empty()
    scanner_slot = st.empty()

    # Step 1: Image received, starting YOLO
    with scanner_slot:
        cards.image_scanner_box(image, is_scanning=True, caption="Stage 01: Food Localization Analysis...")
    with pipeline_slot:
        pipeline.render_pipeline_card({
            "01": "active", "02": "waiting", "03": "waiting", "04": "waiting", "05": "waiting"
        }, current_summary="Executing YOLO Object Localization")

    yolo_result = yolo_detector.detect(image, yolo_model, yolo_load_err)
    time.sleep(0.3)

    # Step 2: Food Classification
    with pipeline_slot:
        pipeline.render_pipeline_card({
            "01": "done", "02": "active", "03": "waiting", "04": "waiting", "05": "waiting"
        }, current_summary="Evaluating Food-101 Category Probabilities")

    if not food_model.loaded:
        pipeline_slot.empty()
        scanner_slot.empty()
        cards.final_result_card(
            "UNABLE_TO_VERIFY",
            f"Food classification model could not be loaded: {food_model.error}",
        )
        return

    classification = inference.classify_food(image, food_model)
    passed = classification.top_confidence >= SETTINGS.food_confidence_threshold
    time.sleep(0.3)

    # Step 3: Confidence Gate
    gate_state = "done" if passed else "failed"
    with pipeline_slot:
        pipeline.render_pipeline_card({
            "01": "done", "02": "done", "03": gate_state, "04": "waiting", "05": "waiting"
        }, current_summary="Evaluating Confidence Threshold (80%)")
    time.sleep(0.2)

    authenticity = None
    fusion = None

    if passed:
        if not fake_model.loaded:
            pipeline_slot.empty()
            scanner_slot.empty()
            cards.final_result_card(
                "UNABLE_TO_VERIFY",
                f"Authenticity model could not be loaded: {fake_model.error}",
            )
            return

        # Step 4: Authenticity Model
        with pipeline_slot:
            pipeline.render_pipeline_card({
                "01": "done", "02": "done", "03": "done", "04": "active", "05": "waiting"
            }, current_summary="Analyzing Frequency & Diffusion Artifacts")

        authenticity = inference.detect_authenticity(
            image,
            fake_model,
            SETTINGS.fake_model_real_index,
            authenticity_threshold=SETTINGS.authenticity_threshold,
        )
        if SETTINGS.enable_fusion:
            fusion = inference.fusion_score(
                classification.top_confidence,
                authenticity.synthetic_probability,
                SETTINGS.fusion_alpha,
            )
        time.sleep(0.3)

        # Step 5: Final Decision
        if authenticity.status_tier == "authentic":
            final_state = "verified"
            decision = "AUTHENTIC"
        elif authenticity.status_tier == "suspected_ai":
            final_state = "warning"
            decision = "SUSPECTED_AI"
        else:
            final_state = "alert"
            decision = "POTENTIALLY_AI_GENERATED"
        with pipeline_slot:
            pipeline.render_pipeline_card({
                "01": "done", "02": "done", "03": "done", "04": "done", "05": "done"
            }, current_summary=f"Final Verdict: {decision}")
    else:
        # Confidence gate failed — authenticity check skipped
        final_state, decision = "alert", "UNABLE_TO_VERIFY"
        with pipeline_slot:
            pipeline.render_pipeline_card({
                "01": "done", "02": "done", "03": "failed", "04": "skipped", "05": "done"
            }, current_summary="Verification Halted: Confidence Below Gate")

    # Clear scanner slot so static result is rendered smoothly
    scanner_slot.empty()

    result = {
        "image": image,
        "yolo": yolo_result,
        "classification": classification,
        "authenticity": authenticity,
        "fusion": fusion,
        "passed_threshold": passed,
        "final_state": final_state,
        "decision": decision,
    }
    st.session_state["verification_result"] = result

    history_db.add_record(
        SETTINGS.db_path,
        user_id=user_id,
        food_category=classification.top_label,
        food_confidence=classification.top_confidence,
        authenticity_result=(authenticity.label if authenticity else None),
        ai_probability=(authenticity.synthetic_probability if authenticity else None),
        fusion_score=fusion,
        final_decision=decision,
    )


def yolo_detector_draw(image: Image.Image, detections):
    from PIL import ImageDraw
    annotated = image.convert("RGB").copy()
    draw = ImageDraw.Draw(annotated)
    for det in detections:
        x1, y1, x2, y2 = det.box
        draw.rectangle([x1, y1, x2, y2], outline="#2DD4BF", width=3)
        draw.text((x1 + 4, max(0, y1 - 16)), f"{det.label} {det.confidence:.0%}", fill="#2DD4BF")
    return annotated


def render_verification_result(result: dict):
    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

    cls = result["classification"]
    auth_res = result.get("authenticity")
    decision = result["decision"]
    food_label = cls.top_label.replace("_", " ").title()

    # Prominent Final Result Card
    if decision == "AUTHENTIC":
        body_text = (
            f"The image satisfies food validation ({cls.top_confidence:.1%} confidence for {food_label}) "
            f"and meets the strict authenticity gate ({auth_res.real_probability:.1%} real likelihood vs "
            f"{SETTINGS.authenticity_threshold:.0%} required threshold)."
        )
    elif decision == "SUSPECTED_AI":
        body_text = (
            f"The image depicts {food_label} ({cls.top_confidence:.1%} confidence), but our authenticity "
            f"neural network detected elevated synthetic indicators ({auth_res.synthetic_probability:.1%} synthetic likelihood). "
            f"Because real likelihood ({auth_res.real_probability:.1%}) falls below the {SETTINGS.authenticity_threshold:.0%} "
            "authenticity threshold, this image is flagged as suspected modern AI diffusion generation (e.g. Midjourney, DALL-E, SDXL, Flux)."
        )
    elif decision == "POTENTIALLY_AI_GENERATED":
        body_text = (
            f"The image depicts {food_label} ({cls.top_confidence:.1%} confidence), but our authenticity "
            f"neural network flagged a dominant {auth_res.synthetic_probability:.1%} probability of synthetic / AI generation."
        )
    else:
        body_text = (
            f"The highest food confidence ({cls.top_confidence:.1%} for {food_label}) is below the required "
            f"{SETTINGS.food_confidence_threshold:.0%} confidence gate. Authenticity analysis was withheld "
            "to prevent misleading predictions on non-food or ambiguous images."
        )

    cards.final_result_card(
        decision,
        body_text,
        food_name=food_label,
        food_conf=cls.top_confidence,
        authenticity_label=(auth_res.label if auth_res else None),
        ai_prob=(auth_res.synthetic_probability if auth_res else None),
        fusion_score=result.get("fusion"),
    )

    # Detailed Analysis Columns
    col_img, col_metrics = st.columns([1.2, 1])

    with col_img:
        yolo_result = result["yolo"]
        if yolo_result.configured and yolo_result.ran and yolo_result.detections:
            tab_orig, tab_det = st.tabs(["Original Image", "YOLO Food Localization"])
            with tab_orig:
                cards.image_scanner_box(result["image"], is_scanning=False)
            with tab_det:
                annotated = yolo_detector_draw(result["image"], yolo_result.detections)
                cards.image_scanner_box(annotated, is_scanning=False)
            top_det = max(yolo_result.detections, key=lambda d: d.confidence)
            st.caption(f"YOLO Localization · Detected: {top_det.label} (confidence {top_det.confidence:.0%})")
        else:
            cards.image_scanner_box(result["image"], is_scanning=False)
            if not yolo_result.configured:
                st.caption("YOLO model not configured in environment.")

    with col_metrics:
        # Gauge Visualizer
        st.markdown(
            f"""
            <div class="ng-card">
              <div class="ng-card-label">CONFIDENCE GAUGE</div>
            """,
            unsafe_allow_html=True,
        )
        gauge_col = COLORS["verified"] if result["passed_threshold"] else COLORS["warning"]
        cards.circular_confidence_gauge(cls.top_confidence, label=f"FOOD: {food_label.upper()}", color=gauge_col)
        st.markdown("</div>", unsafe_allow_html=True)

        # Top 3 Candidates
        if len(cls.top3) > 1:
            with st.expander("Top Predicted Food Classes", expanded=True):
                for label, conf in cls.top3:
                    cards.confidence_bar(conf, label=label.replace('_', ' ').title(), color=COLORS["accent"])

        # Authenticity Details
        if auth_res:
            cards.stage_card(
                "SYNTHETIC ARTIFACT CHECK",
                "Authenticity Metrics",
                [
                    ("Authenticity Verdict", auth_res.label),
                    ("Synthetic Likelihood", f"{auth_res.synthetic_probability:.2%}"),
                    ("Real Likelihood", f"{(1.0 - auth_res.synthetic_probability):.2%}"),
                    ("Model Architecture", "ResNet-101 (CIFAKE)"),
                ],
            )


def page_verify():
    st.markdown("## Food Image Verification")
    st.caption("Upload or capture a food photo to initiate multi-stage authenticity analysis.")

    user = require_user()
    if not user:
        return

    mode = st.radio(
        "Input Method",
        ["Upload Image", "Use Camera"],
        horizontal=True,
        key="verify_mode",
        label_visibility="collapsed",
    )

    image = None
    if mode == "Upload Image":
        uploaded = st.file_uploader("Select or drop a food photograph", type=["jpg", "jpeg", "png", "webp"])
        image = _load_image(uploaded)
    else:
        captured = st.camera_input("Capture food photograph with device camera")
        image = _load_image(captured)

    if image is None:
        cards.empty_state(
            "No Image Selected",
            "Upload a food photo or take a picture using your camera above to begin verification.",
            icon_type="image",
        )
    else:
        cards.image_scanner_box(image, is_scanning=False, caption="Image ready for inference")

        c1, c2, _ = st.columns([1.5, 1.5, 3])
        with c1:
            if st.button("Start Verification", type="primary", use_container_width=True):
                run_verification(image, user.user_id)
        with c2:
            if st.button("Clear / Reset", type="secondary", use_container_width=True):
                st.session_state.pop("verification_result", None)
                st.rerun()

    if "verification_result" in st.session_state:
        render_verification_result(st.session_state["verification_result"])


# ------------------------------------------------------------------ history --
def page_history():
    st.markdown("## Verification History")
    st.caption("Archive of past food authenticity checks stored securely.")

    user = require_user()
    if not user:
        return

    c1, _ = st.columns([2.5, 1.5])
    with c1:
        search = st.text_input("Search by food dish or decision verdict", placeholder="e.g. Pizza, AUTHENTIC, AI-GENERATED...")

    records = history_db.list_records(
        SETTINGS.db_path,
        user_id=(None if user.is_guest else user.user_id),
        search=search or None,
    )

    if not records:
        cards.empty_state(
            "No Records Found",
            "Past verifications will appear here once you run images through the verification engine.",
            icon_type="history",
        )
        return

    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

    for r in records:
        if r.final_decision == "AUTHENTIC":
            badge_color = COLORS["verified"]
            badge_border = COLORS["verified_border"]
            badge_bg = COLORS["verified_bg"]
            badge_icon = "✓"
        elif r.final_decision in ("POTENTIALLY_AI_GENERATED", "SUSPECTED_AI"):
            badge_color = COLORS["alert"]
            badge_border = COLORS["alert_border"]
            badge_bg = COLORS["alert_bg"]
            badge_icon = "⚠"
        else:
            badge_color = COLORS["warning"]
            badge_border = COLORS["warning_border"]
            badge_bg = COLORS["warning_bg"]
            badge_icon = "●"

        food_title = (r.food_category or "Unknown").replace("_", " ").title()
        conf_str = f"{r.food_confidence:.1%}" if r.food_confidence is not None else "—"
        ai_prob_str = f"{r.ai_probability:.1%}" if r.ai_probability is not None else "—"

        st.markdown(
            f"""
            <div style="background:{COLORS['bg_surface']}; border:1px solid {COLORS['line']}; border-radius:8px; padding:1rem 1.2rem; margin-bottom:0.75rem; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px;">
              <div>
                <div style="font-family:'Outfit',sans-serif; font-size:1.1rem; font-weight:600; color:{COLORS['text_primary']};">
                  {html.escape(food_title)}
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:{COLORS['text_muted']};">
                  {r.timestamp[:19].replace('T', ' ')} UTC
                </div>
              </div>

              <div style="display:flex; align-items:center; gap:20px;">
                <div>
                  <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:{COLORS['text_muted']};">CONFIDENCE</div>
                  <div style="font-family:'JetBrains Mono',monospace; font-size:0.95rem; font-weight:600; color:{COLORS['text_primary']};">{conf_str}</div>
                </div>
                <div>
                  <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:{COLORS['text_muted']};">SYNTHETIC PROB</div>
                  <div style="font-family:'JetBrains Mono',monospace; font-size:0.95rem; font-weight:600; color:{COLORS['text_primary']};">{ai_prob_str}</div>
                </div>
                <div style="padding:0.35rem 0.8rem; border-radius:6px; background:{badge_bg}; border:1px solid {badge_border}; color:{badge_color}; font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:600;">
                  {badge_icon} {html.escape(r.final_decision)}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ------------------------------------------------------------ system status --
def _render_status_metric(label: str, ok: bool, text_ok: str, text_bad: str, detail: str = ""):
    color = COLORS["verified"] if ok else COLORS["alert"]
    icon = "●" if ok else "✕"
    val = text_ok if ok else text_bad
    st.markdown(
        f"""
        <div style="background:{COLORS['bg_surface']}; border:1px solid {COLORS['line']}; border-radius:8px; padding:0.9rem 1.1rem; margin-bottom:0.6rem; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-family:'Outfit',sans-serif; font-size:0.95rem; font-weight:600; color:{COLORS['text_primary']};">{html.escape(label)}</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:{COLORS['text_muted']};">{html.escape(detail)}</div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:600; color:{color}; display:flex; align-items:center; gap:6px;">
            <span>{icon}</span> {html.escape(val)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_status():
    st.markdown("## System Status & Model Telemetry")
    st.caption("Active runtime parameters and neural network diagnostics.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Model Infrastructure")
        _render_status_metric("Food Classifier", food_model.loaded, "ONLINE", "FAILED", "ResNet-101 (Food-101 Benchmark)")
        _render_status_metric("Authenticity Detector", fake_model.loaded, "ONLINE", "FAILED", "ResNet-101 (CIFAKE Benchmark)")
        _render_status_metric("YOLO Object Detector", yolo_model is not None, "CONFIGURED", "NOT CONFIGURED", "YOLOv8 Food Bounding Localization")
        _render_status_metric("Clerk Auth Service", auth.is_configured(SETTINGS), "CONFIGURED", "DEV MODE", "Backend JWT & Session API")

    with c2:
        st.markdown("### Runtime Hardware & Thresholds")
        device_label = food_model.device.upper()
        _render_status_metric("Inference Engine", True, device_label, "CPU", f"Preference: {SETTINGS.device_pref.upper()}")
        _render_status_metric("Confidence Gate Threshold", True, f"{SETTINGS.food_confidence_threshold:.0%}", "", "Minimum confidence to proceed")
        _render_status_metric("Authenticity Gate", True, f"{SETTINGS.authenticity_threshold:.0%}", "", "Strict minimum real likelihood")
        _render_status_metric("Fusion Weight (Alpha)", SETTINGS.enable_fusion, f"{SETTINGS.fusion_alpha:.2f}", "DISABLED", "Multimodal score blending")
        _render_status_metric("Authenticity REAL Index", True, f"Index {SETTINGS.fake_model_real_index}", "", "Target neuron for real class")

# -------------------------------------------------------------------- about --
def page_about():
    st.markdown("## About NutriGuard")
    st.caption("AI-powered food image verification and digital trust framework.")

    st.markdown(
        """
        NutriGuard is an intelligent food image verification system designed to counteract
        misleading, synthetic, and AI-generated food representations in digital ecosystems.
        By orchestrating object detection, multi-class cuisine categorization, and frequency/diffusion
        artifact analysis, NutriGuard establishes an objective confidence score for every food photo.
        """
    )

    pipeline.dashboard_pipeline()

    st.markdown(
        """
        ### Methodology & Technical Integrity
        1. **Confidence Gating**: The system strictly gates authenticity checks. If an input image does
           not meet the minimum food classification confidence, downstream deepfake checks are withheld
           to ensure responsible, explainable verification.
        2. **Multi-Model Evidence**: Combines specialized neural networks rather than relying on a single
           monolithic discriminator.
        3. **Security Standards**: Employs Clerk for enterprise authentication and stores zero user images
           on disk, preserving total user privacy.
        """
    )


# ------------------------------------------------------------------ profile --
def page_profile():
    st.markdown("## User Profile & Security")
    user = require_user()
    if not user:
        return

    avatar_html = ""
    if user.avatar_url:
        avatar_html = f'<img src="{user.avatar_url}" style="width:56px; height:56px; border-radius:50%; border:2px solid {COLORS["accent"]}; margin-bottom:0.8rem;" />'
    else:
        initial = (user.display_name[:1] if user.display_name else "U").upper()
        avatar_html = f'<div style="width:56px; height:56px; border-radius:50%; background:{COLORS["bg_surface_raised"]}; border:2px solid {COLORS["accent"]}; display:flex; align-items:center; justify-content:center; font-weight:700; color:{COLORS["accent"]}; font-size:1.4rem; margin-bottom:0.8rem;">{initial}</div>'

    st.markdown(
        f"""
        <div class="ng-card" style="max-width:540px;">
          {avatar_html}
          <div class="ng-card-title">{html.escape(user.display_name)}</div>
          <div style="font-family:'JetBrains Mono',monospace; font-size:0.82rem; color:{COLORS['accent']}; margin-bottom:0.8rem;">
            {'Verified Clerk Account' if not user.is_guest else 'Guest Session'}
          </div>
          <div style="color:{COLORS['text_muted']}; font-size:0.9rem; margin-bottom:1.2rem;">
            User ID: <code>{html.escape(user.user_id)}</code><br>
            Email: {html.escape(user.email or 'N/A')}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Sign Out of NutriGuard", type="primary"):
        auth.sign_out()
        st.session_state.pop("verification_result", None)
        st.rerun()


# --------------------------------------------------------------------- auth gate --
user = auth.render_login_gate(SETTINGS)
if not user:
    st.stop()

# --------------------------------------------------------------------- main app --
show_profile = auth.is_configured(SETTINGS)
nav.render_sidebar(show_profile=show_profile, models_ready=models_ready)

ROUTER = {
    "Dashboard": page_dashboard,
    "Verify Food Image": page_verify,
    "History": page_history,
    "System Status": page_status,
    "About": page_about,
    "Profile": page_profile,
}
ROUTER.get(nav.current_route(), page_dashboard)()

