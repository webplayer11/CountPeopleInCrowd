"""
app.py — CrowdLens Flask application
=====================================
All prediction logic lives in model/predictor.py.
This file handles routing, file I/O, and JSON responses only.
"""

import os
import uuid
from pathlib import Path
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify, render_template, url_for

from model.predictor import predict

# ── App setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

UPLOAD_DIR   = Path(__file__).parent / "static" / "uploads"
RESULTS_DIR  = Path(__file__).parent / "static" / "results"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    # 1. Validate request
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use PNG, JPG, or WEBP."}), 400

    # 2. Save upload
    ext           = file.filename.rsplit(".", 1)[1].lower()
    unique_name   = f"{uuid.uuid4().hex}.{ext}"
    upload_path   = UPLOAD_DIR / unique_name
    file.save(upload_path)

    # 3. Run prediction  ← single call; never touches model internals
    try:
        count, density_rel_path, processing_time = predict(str(upload_path))
    except Exception as exc:
        upload_path.unlink(missing_ok=True)
        return jsonify({"error": f"Prediction failed: {exc}"}), 500

    # 4. Build response
    original_url  = url_for("static", filename=f"uploads/{unique_name}")
    density_url   = url_for("static", filename=f"results/{Path(density_rel_path).name}")

    return jsonify({
        "count":            count,
        "original_url":     original_url,
        "density_map_url":  density_url,
        "processing_time":  processing_time,
    })


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)