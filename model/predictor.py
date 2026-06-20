"""
model/predictor.py
==================
Isolated prediction module for crowd counting.

Public interface (the only thing app.py calls):

    count, density_map_path, processing_time = predict(image_path)

Arguments
---------
image_path : str | Path
    Absolute or relative path to the input image.

Returns
-------
count : int
    Estimated number of people in the image.
density_map_path : str
    Path to the generated density-map PNG saved under static/results/.
processing_time : float
    Wall-clock seconds the prediction took.

To integrate a real model
-------------------------
Replace ONLY the body of _run_model().  The signature, file I/O, and
timing logic above and below it must stay untouched so app.py keeps
working without modification.
"""

import os
import time
import uuid
import random
import numpy as np
from pathlib import Path
from PIL import Image

# Output directory (relative to project root)
RESULTS_DIR = Path(__file__).resolve().parent.parent / "static" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_density_array(width: int, height: int) -> np.ndarray:
    """
    Generate a synthetic density map as a float32 array (H×W).
    Replace this with real model output when integrating.
    """
    density = np.zeros((height, width), dtype=np.float32)

    num_clusters = random.randint(4, 10)
    for _ in range(num_clusters):
        cx     = random.randint(width  // 8, 7 * width  // 8)
        cy     = random.randint(height // 8, 7 * height // 8)
        sigma  = random.randint(25, min(width, height) // 4)
        weight = random.uniform(8.0, 60.0)

        ys, xs = np.ogrid[:height, :width]
        blob   = np.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / (2.0 * sigma ** 2))
        density += blob * weight

    return density


def _colorise_density(density: np.ndarray) -> np.ndarray:
    """Map a float density array to an RGB heatmap (H×W×3, uint8)."""
    norm = density / (density.max() + 1e-8)   # 0–1

    # Jet-style: blue → cyan → green → yellow → red
    r = np.clip(1.5 - np.abs(norm * 4.0 - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(norm * 4.0 - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(norm * 4.0 - 1.0), 0.0, 1.0)

    rgb = np.stack(
        [(r * 255).astype(np.uint8),
         (g * 255).astype(np.uint8),
         (b * 255).astype(np.uint8)],
        axis=-1,
    )
    return rgb


def _blend_with_original(original: Image.Image, heatmap: np.ndarray,
                          alpha: float = 0.60) -> Image.Image:
    """Overlay the heatmap on a dimmed version of the original image."""
    orig_arr  = np.array(original.resize((heatmap.shape[1], heatmap.shape[0]))).astype(np.float32)
    heat_arr  = heatmap.astype(np.float32)
    blended   = (orig_arr * (1 - alpha) + heat_arr * alpha).clip(0, 255).astype(np.uint8)
    return Image.fromarray(blended)


def _save_density_map(density_image: Image.Image) -> str:
    """Save the density map PNG to static/results/ and return the file path."""
    filename    = f"density_{uuid.uuid4().hex[:12]}.png"
    output_path = RESULTS_DIR / filename
    density_image.save(output_path, format="PNG")
    return str(output_path)


# ─────────────────────────────────────────────────────────────────────────────
#  Core model slot — replace this function with the real model
# ─────────────────────────────────────────────────────────────────────────────

def _run_model(image: Image.Image) -> tuple[int, np.ndarray]:
    """
    **MOCK IMPLEMENTATION — swap in your real model here.**

    Parameters
    ----------
    image : PIL.Image (RGB)

    Returns
    -------
    count      : int          — estimated head count
    heatmap_rgb: np.ndarray   — H×W×3 uint8 colourised density map
    """
    w, h    = image.size
    density = _build_density_array(w, h)
    count   = int(density.sum())
    heatmap = _colorise_density(density)
    return count, heatmap


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def predict(image_path: str) -> tuple[int, str, float]:
    """
    Run crowd-count prediction on *image_path*.

    Returns
    -------
    count             : int
    density_map_path  : str   (relative URL-friendly path for Flask)
    processing_time   : float (seconds)
    """
    t_start = time.perf_counter()

    image = Image.open(image_path).convert("RGB")
    count, heatmap_rgb = _run_model(image)
    density_img = _blend_with_original(image, heatmap_rgb)
    density_path = _save_density_map(density_img)

    processing_time = round(time.perf_counter() - t_start, 3)

    # Return a path Flask can serve: "static/results/<filename>"
    relative_path = "static/results/" + Path(density_path).name
    return count, relative_path, processing_time