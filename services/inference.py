"""
Real inference against the loaded checkpoints. No mock/fabricated outputs —
every number returned here comes from an actual forward pass.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from PIL import Image
from torchvision import transforms

from services.model_loader import IMAGENET_MEAN, IMAGENET_STD, INPUT_SIZE, LoadedModel

_preprocess = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


@dataclass
class ClassificationResult:
    top_label: str
    top_confidence: float
    top3: list[tuple[str, float]]


@dataclass
class AuthenticityResult:
    is_real: bool
    label: str  # "REAL", "AI-GENERATED", or "SUSPECTED AI"
    synthetic_probability: float
    real_probability: float
    status_tier: str = "authentic"  # "authentic" | "suspected_ai" | "ai_generated"


def _to_tensor(image: Image.Image, device: str) -> torch.Tensor:
    rgb = image.convert("RGB")
    return _preprocess(rgb).unsqueeze(0).to(device)


@torch.inference_mode()
def classify_food(image: Image.Image, loaded: LoadedModel) -> ClassificationResult:
    if not loaded.loaded or loaded.model is None:
        raise RuntimeError("Food classification model is not loaded.")

    x = _to_tensor(image, loaded.device)
    logits = loaded.model(x)
    probs = torch.softmax(logits, dim=1).squeeze(0).cpu()

    top_probs, top_idx = torch.topk(probs, k=min(3, probs.shape[0]))
    top3 = [(loaded.class_names[i], float(p)) for p, i in zip(top_probs, top_idx)]

    return ClassificationResult(
        top_label=top3[0][0],
        top_confidence=top3[0][1],
        top3=top3,
    )


@torch.inference_mode()
def detect_authenticity(
    image: Image.Image,
    loaded: LoadedModel,
    real_index: int,
    authenticity_threshold: float = 0.80,
) -> AuthenticityResult:
    if not loaded.loaded or loaded.model is None:
        raise RuntimeError("Authenticity model is not loaded.")

    x = _to_tensor(image, loaded.device)
    logits = loaded.model(x)

    if loaded.num_classes == 1:
        # Single-logit binary head: sigmoid output = P(class 1).
        p_class1 = torch.sigmoid(logits).item()
        real_p = p_class1 if real_index == 1 else 1.0 - p_class1
    else:
        probs = torch.softmax(logits, dim=1).squeeze(0).cpu()
        safe_index = real_index if real_index < probs.shape[0] else 0
        real_p = float(probs[safe_index])

    synthetic_p = 1.0 - real_p

    # Multi-tier sensitivity analysis:
    # 1. Real Likelihood >= authenticity_threshold: Certified Real Camera Photograph
    # 2. Synthetic Likelihood > 0.50: Dominant synthetic artifacts (Legacy GAN / Clear Synthetic)
    # 3. Real Likelihood in [0.50, authenticity_threshold): Elevated synthetic indicators
    #    often produced by modern diffusion models (Midjourney, DALL-E 3, SDXL, Flux)
    if real_p >= authenticity_threshold:
        is_real = True
        status_tier = "authentic"
        label = "REAL"
    elif synthetic_p > 0.50:
        is_real = False
        status_tier = "ai_generated"
        label = "AI-GENERATED"
    else:
        is_real = False
        status_tier = "suspected_ai"
        label = "SUSPECTED AI"

    return AuthenticityResult(
        is_real=is_real,
        label=label,
        synthetic_probability=synthetic_p,
        real_probability=real_p,
        status_tier=status_tier,
    )


def fusion_score(food_confidence: float, synthetic_probability: float, alpha: float) -> float:
    """R(x) = alpha * C_class(x) + (1 - alpha) * (1 - P_synthetic(x))"""
    return alpha * food_confidence + (1 - alpha) * (1 - synthetic_probability)
