import io
import os
import sys
from pathlib import Path
from dataclasses import asdict
from typing import Optional

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image

# Ensure project root is on path so we can import ASCII.py when running from web/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import local ascii utilities
from ASCII import ASCIISettings, image_to_ascii, ascii_to_png, input_folder

app = Flask(__name__)

# In-memory last image and settings
last_image: Optional[Image.Image] = None
last_image_name: Optional[str] = None


def get_settings_from_request() -> ASCIISettings:
    # Parse settings from request args/form/json
    data = {}
    source = request.get_json(silent=True) or request.form or request.args
    if not source:
        return ASCIISettings()

    def to_int(name, default):
        try:
            return int(source.get(name, default))
        except Exception:
            return default

    def to_bool(name, default):
        v = source.get(name, default)
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "on")
        return default

    settings = ASCIISettings(
        output_width=to_int("output_width", 120),
        ascii_chars=source.get("ascii_chars", "@%#*+=-:. "),
        black_threshold=to_int("black_threshold", 15),
        invert=to_bool("invert", False),
        char_aspect=float(source.get("char_aspect", 0.55)),
        font_path=source.get("font_path") or None,
        font_size=to_int("font_size", 12),
        fg_color=source.get("fg_color", "black"),
        bg_color=source.get("bg_color", "white"),
    )
    return settings


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/preview", methods=["POST"])
def api_preview():
    global last_image, last_image_name

    # Accept file upload or use last_image
    file = request.files.get("file")
    if file:
        try:
            img = Image.open(file.stream).convert("RGB")
            last_image = img
            last_image_name = getattr(file, 'filename', None)
        except Exception as e:
            return jsonify({"error": f"Invalid image: {e}"}), 400
    elif last_image is None:
        return jsonify({"error": "No image uploaded yet"}), 400
    else:
        img = last_image

    settings = get_settings_from_request()
    ascii_art = image_to_ascii(img, settings)
    png_img = ascii_to_png(ascii_art, None, settings)

    buf = io.BytesIO()
    png_img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/api/settings", methods=["GET"]) 
def api_settings():
    # Provide default settings to the UI
    return jsonify(asdict(ASCIISettings()))


@app.route("/api/list_input", methods=["GET"]) 
def api_list_input():
    try:
        items = [
            f for f in sorted(os.listdir(input_folder))
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))
        ]
        return jsonify({"files": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/select", methods=["POST"]) 
def api_select():
    """Select an image from the input folder as the active image."""
    global last_image, last_image_name
    name = request.values.get("name")
    if not name:
        return jsonify({"error": "Missing name"}), 400
    path = os.path.join(input_folder, name)
    if not os.path.isfile(path):
        return jsonify({"error": "Not found"}), 404
    try:
        img = Image.open(path).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Failed to open: {e}"}), 400
    last_image = img
    last_image_name = name
    return jsonify({"ok": True, "name": name})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
