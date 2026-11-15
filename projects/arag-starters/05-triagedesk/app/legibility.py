"""Deterministic, local image-quality heuristics for scanned document pages.

Blur/darkness/crop/rotation are checked locally (not via an ARAG call) because
they are objective pixel-level properties best measured deterministically -
the same page should always get the same verdict in a live demo. ARAG handles
the parts that need reasoning: document classification, field extraction and
authenticity-indicator detection (see arag_client.py).
"""
from PIL import Image
import numpy as np

BLUR_VARIANCE_THRESHOLD = 120.0
DARK_MEAN_THRESHOLD = 70.0
CROP_EDGE_MARGIN_RATIO = 0.02


def _laplacian_variance(gray: np.ndarray) -> float:
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    h, w = gray.shape
    padded = np.pad(gray, 1, mode="edge").astype(np.float32)
    out = np.zeros_like(gray, dtype=np.float32)
    for i in range(3):
        for j in range(3):
            if kernel[i, j] == 0:
                continue
            out += kernel[i, j] * padded[i:i + h, j:j + w]
    return float(out.var())


def _edge_content_ratio(gray: np.ndarray) -> float:
    """Fraction of border pixels that are non-background - a crude cropped-page signal."""
    h, w = gray.shape
    m = max(1, int(min(h, w) * CROP_EDGE_MARGIN_RATIO))
    border = np.concatenate([
        gray[:m, :].ravel(), gray[-m:, :].ravel(),
        gray[:, :m].ravel(), gray[:, -m:].ravel(),
    ])
    bg = np.median(gray)
    non_bg = np.abs(border.astype(np.float32) - bg) > 40
    return float(non_bg.mean())


def assess_page(image_path: str) -> dict:
    """Returns {status, issues[], metrics{}} for one page image."""
    img = Image.open(image_path).convert("L")
    gray = np.array(img)

    variance = _laplacian_variance(gray)
    mean_brightness = float(gray.mean())
    edge_ratio = _edge_content_ratio(gray)
    w, h = img.size
    aspect = w / h if h else 1.0

    issues = []
    if variance < BLUR_VARIANCE_THRESHOLD:
        issues.append("DOC_BLURRED")
    if mean_brightness < DARK_MEAN_THRESHOLD:
        issues.append("DOC_TOO_DARK")
    if edge_ratio > 0.35:
        issues.append("DOC_CROPPED")
    if aspect > 1.35 or aspect < 0.55:
        issues.append("DOC_ROTATED")

    status = "LEGIBLE" if not issues else "ISSUES_FOUND"
    return {
        "status": status,
        "issues": issues,
        "metrics": {
            "sharpness_variance": round(variance, 1),
            "mean_brightness": round(mean_brightness, 1),
            "edge_content_ratio": round(edge_ratio, 3),
            "aspect_ratio": round(aspect, 3),
        },
    }
