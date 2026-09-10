"""
Loads the two existing ResNet-101 checkpoints.

Neither checkpoint ships with source code, so this module INSPECTS each
.pth file at load time rather than assuming its shape:
  - it figures out the true output class count from the saved weights
  - it rebuilds a torchvision resnet101 with a matching final layer
  - it reports exactly what it found (and what it could NOT verify) so
    System Status can surface it instead of silently guessing

Preprocessing (224x224, ImageNet mean/std) is the standard convention for
transfer-learned ResNet-101 and is used as the default — but since no
training script was available to confirm it, this is flagged in the UI
as an assumption to verify, not asserted as fact.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
from torchvision.models import resnet101

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
INPUT_SIZE = 224

# Canonical Food-101 label set (the public dataset's own class list, alphabetical).
# Only applied when the checkpoint's introspected class count is exactly 101 —
# otherwise we show generic class indices rather than assume this mapping applies.
FOOD101_CLASSES = [
    "apple_pie", "baby_back_ribs", "baklava", "beef_carpaccio", "beef_tartare",
    "beet_salad", "beignets", "bibimbap", "bread_pudding", "breakfast_burrito",
    "bruschetta", "caesar_salad", "cannoli", "caprese_salad", "carrot_cake",
    "ceviche", "cheesecake", "cheese_plate", "chicken_curry", "chicken_quesadilla",
    "chicken_wings", "chocolate_cake", "chocolate_mousse", "churros", "clam_chowder",
    "club_sandwich", "crab_cakes", "creme_brulee", "croque_madame", "cup_cakes",
    "deviled_eggs", "donuts", "dumplings", "edamame", "eggs_benedict", "escargots",
    "falafel", "filet_mignon", "fish_and_chips", "foie_gras", "french_fries",
    "french_onion_soup", "french_toast", "fried_calamari", "fried_rice",
    "frozen_yogurt", "garlic_bread", "gnocchi", "greek_salad",
    "grilled_cheese_sandwich", "grilled_salmon", "guacamole", "gyoza", "hamburger",
    "hot_and_sour_soup", "hot_dog", "huevos_rancheros", "hummus", "ice_cream",
    "lasagna", "lobster_bisque", "lobster_roll_sandwich", "macaroni_and_cheese",
    "macarons", "miso_soup", "mussels", "nachos", "omelette", "onion_rings",
    "oysters", "pad_thai", "paella", "pancakes", "panna_cotta", "peking_duck",
    "pho", "pizza", "pork_chop", "poutine", "prime_rib", "pulled_pork_sandwich",
    "ramen", "ravioli", "red_velvet_cake", "risotto", "samosa", "sashimi",
    "scallops", "seaweed_salad", "shrimp_and_grits", "spaghetti_bolognese",
    "spaghetti_carbonara", "spring_rolls", "steak", "strawberry_shortcake",
    "sushi", "tacos", "takoyaki", "tiramisu", "tuna_tartare", "waffles",
]

_FC_WEIGHT_RE = re.compile(r"(^|\.)fc(\.\d+)?\.weight$")


@dataclass
class LoadedModel:
    model: Optional[nn.Module]
    num_classes: Optional[int]
    class_names: list[str]
    device: str
    checkpoint_path: Path
    loaded: bool = False
    error: Optional[str] = None
    load_warnings: list[str] = field(default_factory=list)


def resolve_device(device_pref: str) -> str:
    if device_pref == "cpu":
        return "cpu"
    if device_pref == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def _extract_state_dict(obj) -> dict:
    if isinstance(obj, dict):
        for key in ("state_dict", "model_state_dict", "model"):
            inner = obj.get(key)
            if isinstance(inner, dict):
                obj = inner
                break
        if all(hasattr(v, "shape") for v in obj.values()):
            return obj
        raise ValueError(
            "Checkpoint is a dict but no tensor state_dict could be found inside it."
        )
    if hasattr(obj, "state_dict"):
        return obj.state_dict()
    raise ValueError(f"Unrecognized checkpoint format: {type(obj)}")


def _strip_prefix(state_dict: dict) -> dict:
    """Strip a common 'module.' (DataParallel) or 'model.' wrapper prefix if present on every key."""
    keys = list(state_dict.keys())
    for prefix in ("module.", "model."):
        if keys and all(k.startswith(prefix) for k in keys):
            return {k[len(prefix):]: v for k, v in state_dict.items()}
    return state_dict


def _infer_num_classes(state_dict: dict) -> tuple[int, str]:
    """Return (num_classes, matched_key). Prefers a key literally named '...fc...weight';
    falls back to the last 2D weight tensor in the checkpoint (linear-layer heads are 2D)."""
    for key, tensor in state_dict.items():
        if _FC_WEIGHT_RE.search(key) and tensor.dim() == 2:
            return tensor.shape[0], key

    last_linear_key, last_linear_shape = None, None
    for key, tensor in state_dict.items():
        if key.endswith(".weight") and tensor.dim() == 2:
            last_linear_key, last_linear_shape = key, tensor.shape
    if last_linear_key is not None:
        return last_linear_shape[0], last_linear_key

    raise ValueError("Could not find any Linear ('fc') weight tensor in the checkpoint.")


def _build_resnet101(num_classes: int) -> nn.Module:
    net = resnet101(weights=None)
    net.fc = nn.Linear(net.fc.in_features, num_classes)
    return net


def load_checkpoint(path: Optional[Path], device_pref: str) -> LoadedModel:
    device = resolve_device(device_pref)

    if path is None:
        return LoadedModel(
            model=None, num_classes=None, class_names=[], device=device,
            checkpoint_path=Path("(not configured)"), loaded=False,
            error="Model path is not configured.",
        )
    if not path.exists():
        return LoadedModel(
            model=None, num_classes=None, class_names=[], device=device,
            checkpoint_path=path, loaded=False,
            error=f"Checkpoint file not found at {path}",
        )

    warnings: list[str] = []
    try:
        raw = torch.load(path, map_location="cpu", weights_only=False)
        state_dict = _strip_prefix(_extract_state_dict(raw))
        num_classes, matched_key = _infer_num_classes(state_dict)

        net = _build_resnet101(num_classes)
        missing, unexpected = net.load_state_dict(state_dict, strict=False)

        real_missing = [m for m in missing if not m.startswith("fc.")]
        if real_missing:
            warnings.append(
                f"{len(real_missing)} backbone weight(s) did not match a standard "
                "torchvision resnet101 and were left at random init — inspect the "
                "checkpoint if predictions look wrong."
            )
        if unexpected:
            warnings.append(
                f"{len(unexpected)} checkpoint tensor(s) were unused (extra layers "
                "not present in a standard resnet101)."
            )

        net.eval()
        net.to(device)

        class_names = (
            FOOD101_CLASSES if num_classes == len(FOOD101_CLASSES)
            else [f"class_{i}" for i in range(num_classes)]
        )

        return LoadedModel(
            model=net, num_classes=num_classes, class_names=class_names,
            device=device, checkpoint_path=path, loaded=True,
            load_warnings=warnings + [f"Class count inferred from tensor '{matched_key}'."],
        )
    except Exception as exc:  # noqa: BLE001 - surface any load failure cleanly to the UI
        return LoadedModel(
            model=None, num_classes=None, class_names=[], device=device,
            checkpoint_path=path, loaded=False, error=str(exc),
        )
