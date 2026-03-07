"""
ML Model Registry - Vulnerable Flask Application
=================================================
FOR EDUCATIONAL PURPOSES ONLY - AI Red Team Training

This model registry intentionally contains security vulnerabilities
to demonstrate real-world attack surfaces in ML pipelines:

  - Pickle deserialization (arbitrary code execution)
  - No authentication or authorization
  - No input validation on uploads
  - Debug endpoints exposing internal state
  - Direct file serving without sanitization
"""

import os
import pickle
import datetime
import json
from flask import Flask, request, jsonify, send_from_directory, render_template_string

app = Flask(__name__)

MODEL_DIR = "/app/models"
os.makedirs(MODEL_DIR, exist_ok=True)

# In-memory metadata store (no database - another vulnerability)
model_metadata = {}

# ─────────────────────────────────────────────────────────────────────
# HTML Templates
# ─────────────────────────────────────────────────────────────────────

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ML Model Registry</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; background: #0d1117; color: #c9d1d9; }
        .header { background: #161b22; border-bottom: 1px solid #30363d; padding: 16px 32px; }
        .header h1 { margin: 0; color: #58a6ff; font-size: 24px; }
        .header p { margin: 4px 0 0; color: #8b949e; font-size: 14px; }
        .container { max-width: 960px; margin: 32px auto; padding: 0 16px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px;
                padding: 24px; margin-bottom: 16px; }
        .card h2 { color: #58a6ff; margin-top: 0; font-size: 18px; }
        table { width: 100%; border-collapse: collapse; margin: 12px 0; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #21262d; }
        th { color: #8b949e; font-weight: 600; font-size: 13px; text-transform: uppercase; }
        td { color: #c9d1d9; font-size: 14px; }
        a { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .upload-form { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .upload-form input[type=file] { color: #c9d1d9; }
        .btn { background: #238636; color: #fff; border: none; padding: 8px 16px;
               border-radius: 6px; cursor: pointer; font-size: 14px; }
        .btn:hover { background: #2ea043; }
        .btn-danger { background: #da3633; }
        .btn-danger:hover { background: #f85149; }
        .warning { background: #0d1117; border: 1px solid #d29922; border-radius: 6px;
                   padding: 12px 16px; color: #d29922; margin-bottom: 16px; font-size: 13px; }
        .endpoint { font-family: monospace; background: #0d1117; padding: 2px 6px;
                    border-radius: 3px; font-size: 13px; }
        code { background: #0d1117; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
        .empty { color: #8b949e; font-style: italic; padding: 20px 0; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ML Model Registry</h1>
        <p>Internal model storage and serving platform &mdash; Lab 05: AI Supply Chain Attacks</p>
    </div>
    <div class="container">
        <div class="warning">
            WARNING: This registry has no authentication. All models are served without
            validation. Pickle deserialization is enabled on the /load endpoint.
        </div>

        <div class="card">
            <h2>Registered Models</h2>
            {% if models %}
            <table>
                <tr>
                    <th>Model Name</th>
                    <th>Format</th>
                    <th>Size</th>
                    <th>Uploaded</th>
                    <th>Actions</th>
                </tr>
                {% for name, meta in models.items() %}
                <tr>
                    <td>{{ name }}</td>
                    <td>{{ meta.get('format', 'unknown') }}</td>
                    <td>{{ meta.get('size_human', 'unknown') }}</td>
                    <td>{{ meta.get('uploaded_at', 'unknown') }}</td>
                    <td>
                        <a href="/download/{{ name }}">Download</a> |
                        <a href="#" onclick="loadModel('{{ name }}')">Load</a>
                    </td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p class="empty">No models registered yet. Upload one below.</p>
            {% endif %}
        </div>

        <div class="card">
            <h2>Upload Model</h2>
            <form action="/upload" method="post" enctype="multipart/form-data" class="upload-form">
                <input type="file" name="model" accept=".pkl,.pickle,.joblib,.pt,.onnx,.h5">
                <input type="text" name="model_name" placeholder="Model name (optional)"
                       style="background:#0d1117; border:1px solid #30363d; color:#c9d1d9;
                              padding:8px 12px; border-radius:6px;">
                <button type="submit" class="btn">Upload Model</button>
            </form>
        </div>

        <div class="card">
            <h2>API Endpoints</h2>
            <table>
                <tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
                <tr>
                    <td>GET</td>
                    <td class="endpoint">/models</td>
                    <td>List all models with metadata (JSON)</td>
                </tr>
                <tr>
                    <td>POST</td>
                    <td class="endpoint">/upload</td>
                    <td>Upload a model file (multipart form)</td>
                </tr>
                <tr>
                    <td>GET</td>
                    <td class="endpoint">/download/&lt;name&gt;</td>
                    <td>Download a model file</td>
                </tr>
                <tr>
                    <td>POST</td>
                    <td class="endpoint">/load/&lt;name&gt;</td>
                    <td>Load and execute a model (pickle.loads)</td>
                </tr>
                <tr>
                    <td>GET</td>
                    <td class="endpoint">/health</td>
                    <td>Health check</td>
                </tr>
            </table>
        </div>
    </div>

    <script>
    function loadModel(name) {
        if (confirm('Load model "' + name + '"? This will deserialize the model file.')) {
            fetch('/load/' + name, { method: 'POST' })
                .then(r => r.json())
                .then(data => alert(JSON.stringify(data, null, 2)))
                .catch(err => alert('Error: ' + err));
        }
    }
    </script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────

def human_readable_size(size_bytes):
    """Convert bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def scan_existing_models():
    """Scan the model directory for any pre-existing model files."""
    for filename in os.listdir(MODEL_DIR):
        filepath = os.path.join(MODEL_DIR, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            model_metadata[filename] = {
                "filename": filename,
                "filepath": filepath,           # VULN: exposes internal paths
                "format": os.path.splitext(filename)[1].lstrip(".") or "unknown",
                "size_bytes": stat.st_size,
                "size_human": human_readable_size(stat.st_size),
                "uploaded_at": datetime.datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat(),
            }


# ─────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Web UI showing registered models."""
    scan_existing_models()
    return render_template_string(INDEX_HTML, models=model_metadata)


@app.route("/upload", methods=["POST"])
def upload_model():
    """
    Upload a model file.

    VULNERABILITIES:
    - No authentication required
    - No file type validation (accepts any file, including malicious pickles)
    - No file size limits
    - No malware scanning
    - Filename taken from user input without sufficient sanitization
    """
    if "model" not in request.files:
        return jsonify({"error": "No model file provided"}), 400

    file = request.files["model"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # VULN: Minimal sanitization - only basic path traversal prevention
    # Still allows arbitrary file extensions including .pkl
    model_name = request.form.get("model_name", "").strip()
    if not model_name:
        model_name = file.filename

    # Basic (insufficient) path traversal prevention
    safe_name = os.path.basename(model_name)
    filepath = os.path.join(MODEL_DIR, safe_name)

    # VULN: No validation of file contents - saves whatever is uploaded
    file.save(filepath)

    stat = os.stat(filepath)
    model_metadata[safe_name] = {
        "filename": safe_name,
        "filepath": filepath,               # VULN: exposes internal path
        "format": os.path.splitext(safe_name)[1].lstrip(".") or "unknown",
        "size_bytes": stat.st_size,
        "size_human": human_readable_size(stat.st_size),
        "uploaded_at": datetime.datetime.now().isoformat(),
        "uploaded_by": request.remote_addr,  # VULN: no auth, just IP
    }

    return jsonify({
        "status": "success",
        "model_name": safe_name,
        "size": human_readable_size(stat.st_size),
        "message": f"Model '{safe_name}' uploaded successfully",
    })


@app.route("/download/<model_name>")
def download_model(model_name):
    """
    Download a model file.

    VULNERABILITY: Serves files directly from the model directory
    without access controls.
    """
    safe_name = os.path.basename(model_name)
    filepath = os.path.join(MODEL_DIR, safe_name)

    if not os.path.exists(filepath):
        return jsonify({"error": f"Model '{safe_name}' not found"}), 404

    return send_from_directory(MODEL_DIR, safe_name, as_attachment=True)


@app.route("/models")
def list_models():
    """
    List all models with metadata.

    VULNERABILITY: Debug endpoint that reveals internal file paths,
    upload sources, and full metadata for all stored models.
    """
    scan_existing_models()
    return jsonify({
        "models": model_metadata,
        "model_directory": MODEL_DIR,       # VULN: exposes internal path
        "total_models": len(model_metadata),
    })


@app.route("/load/<model_name>", methods=["POST"])
def load_model(model_name):
    """
    Load and execute a pickle model.

    CRITICAL VULNERABILITY: pickle.loads() executes arbitrary Python code.
    An attacker can upload a malicious pickle file and trigger remote code
    execution by calling this endpoint. This is the primary attack vector
    for the pickle deserialization exercise.
    """
    safe_name = os.path.basename(model_name)
    filepath = os.path.join(MODEL_DIR, safe_name)

    if not os.path.exists(filepath):
        return jsonify({"error": f"Model '{safe_name}' not found"}), 404

    try:
        # VULN: pickle.load() will execute arbitrary code embedded in the file
        with open(filepath, "rb") as f:
            model = pickle.load(f)

        # Try to get basic info about the loaded object
        model_info = {
            "status": "loaded",
            "model_name": safe_name,
            "type": str(type(model).__name__),
            "module": str(type(model).__module__),
        }

        # If it's a scikit-learn model, try to get more details
        if hasattr(model, "classes_"):
            model_info["classes"] = [str(c) for c in model.classes_]
        if hasattr(model, "n_features_in_"):
            model_info["n_features"] = model.n_features_in_
        if hasattr(model, "get_params"):
            model_info["params"] = str(model.get_params())

        return jsonify(model_info)

    except Exception as e:
        return jsonify({
            "status": "error",
            "model_name": safe_name,
            "error": str(e),
            "error_type": type(e).__name__,
        }), 500


@app.route("/health")
def health():
    """Health check endpoint."""
    model_count = len([f for f in os.listdir(MODEL_DIR) if os.path.isfile(
        os.path.join(MODEL_DIR, f)
    )])
    return jsonify({
        "status": "healthy",
        "service": "model-registry",
        "model_count": model_count,
        "model_directory": MODEL_DIR,
    })


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    scan_existing_models()
    print(f"[*] Model Registry starting on port 5000")
    print(f"[*] Model directory: {MODEL_DIR}")
    print(f"[*] Found {len(model_metadata)} existing models")
    # VULN: Debug mode enabled, binds to all interfaces
    app.run(host="0.0.0.0", port=5000, debug=False)
