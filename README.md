# NutriGuard

AI-based food image classification and authenticity verification system for
fraud detection. A Streamlit application wired to your trained ResNet-101
checkpoints.

## Pipeline

```
Camera / Upload → YOLO Food Detection → Food-101 ResNet-101 Classification
→ Confidence Gate → CIFAKE ResNet-101 Authenticity Check → Final Decision
```

## Model weights on Hugging Face

The trained model checkpoints are published on Hugging Face here:

https://huggingface.co/rnrahate007/nutriguard-models

Download the required files and place them in the app's model directories:

```
models/food-notfood-detection/resnet101_food101.pth
models/fake-image-detection/resnet101_fake_image_detector.pth
```

This keeps the project ready to run without needing to retrain the ResNet-101 classifiers locally.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Place your checkpoints (already excluded from git) at:

```
models/food-notfood-detection/resnet101_food101.pth
models/fake-image-detection/resnet101_fake_image_detector.pth
```

Edit `.env` if your paths, threshold, or device differ from the defaults.

## Run

```bash
streamlit run app.py
```

## Important: verify the authenticity model's class order

The CIFAKE checkpoint doesn't have accompanying code, so this app can't know
for certain which output index means "REAL" vs "AI-GENERATED". On first run:

1. Run a verification on a photo you know is a real, unedited photo.
2. Open **System Status** and check the reported prediction.
3. If it says AI-GENERATED for a real photo, flip `FAKE_MODEL_REAL_INDEX`
   in `.env` (0 → 1 or vice versa) and restart.

## Model loading behavior

`services/model_loader.py` inspects each `.pth` file at load time — it reads
the checkpoint's own final-layer weight shape to determine the class count
and rebuilds a matching `torchvision.models.resnet101` head, rather than
assuming Food-101's 101 classes or CIFAKE's 2 classes. Food-101's standard
label names are only applied when the introspected class count is exactly
101; otherwise classes are shown as `class_0`, `class_1`, etc.

Preprocessing (224×224, ImageNet mean/std normalization) is the standard
convention for transfer-learned ResNet-101 and is used as the default. If
your training pipeline used different preprocessing, update
`services/inference.py` and `services/model_loader.py` (`IMAGENET_MEAN`,
`IMAGENET_STD`, `INPUT_SIZE`) to match.

## YOLO food detection

`YOLO_MODEL_PATH` is empty by default. Until you provide weights, the app
shows food-detection as "not configured" and skips straight to
classification — it never fabricates bounding boxes. Once you have weights
(an `ultralytics`-compatible `.pt` file), set `YOLO_MODEL_PATH` in `.env`.

## Clerk authentication

Leave `CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` blank to use the app in
guest mode. Once you add real keys, `services/auth.py` mounts Clerk's
vanilla-JS sign-in widget and verifies the session server-side via Clerk's
Backend API — confirm the verification endpoint against Clerk's current
docs once you can test the flow end-to-end with live keys, since their API
surface evolves.

## Project structure

```
app.py                  Main entry point + page routing
components/              CSS, nav, cards, pipeline stepper
services/
  config.py              Env/settings loader
  model_loader.py         Checkpoint introspection + model building
  inference.py            Real inference (classification, authenticity, fusion)
  yolo_detector.py         YOLO integration point
  history_db.py            SQLite verification history
  auth.py                  Clerk authentication
models/                  Your .pth checkpoints go here (gitignored)
data/                    SQLite history.db (gitignored)
```

## Notes

- Inference only runs when you press **Start Verification** — not on every
  Streamlit rerun.
- Model weights load once via `@st.cache_resource` and are reused across
  requests; CUDA is used automatically if available, CPU otherwise.
- No uploaded images are stored — only verification results (category,
  confidences, decision) are saved to history.
