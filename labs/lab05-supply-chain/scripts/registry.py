"""
ML 模型注册表 - 有漏洞的 Flask 应用
=================================================
仅供教育目的 - AI 红队训练

此模型注册表故意包含安全漏洞，
用于演示 ML 管道中的真实攻击面：

  - Pickle 反序列化（任意代码执行）
  - 无身份验证或授权
  - 上传无输入验证
  - 调试端点暴露内部状态
  - 直接提供文件，无清理
"""

import os
import pickle
import datetime
import json
from flask import Flask, request, jsonify, send_from_directory, render_template_string

app = Flask(__name__)

MODEL_DIR = "/app/models"
os.makedirs(MODEL_DIR, exist_ok=True)

# 内存中的元数据存储（无数据库 - 另一个漏洞）
model_metadata = {}

# ─────────────────────────────────────────────────────────────────────
# HTML 模板
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
# 辅助函数
# ─────────────────────────────────────────────────────────────────────

def human_readable_size(size_bytes):
    """将字节数转换为人类可读的字符串。"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def scan_existing_models():
    """扫描模型目录中已有的模型文件。"""
    for filename in os.listdir(MODEL_DIR):
        filepath = os.path.join(MODEL_DIR, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            model_metadata[filename] = {
                "filename": filename,
                "filepath": filepath,           # 漏洞：暴露内部路径
                "format": os.path.splitext(filename)[1].lstrip(".") or "unknown",
                "size_bytes": stat.st_size,
                "size_human": human_readable_size(stat.st_size),
                "uploaded_at": datetime.datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat(),
            }


# ─────────────────────────────────────────────────────────────────────
# 路由
# ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """显示已注册模型的 Web 界面。"""
    scan_existing_models()
    return render_template_string(INDEX_HTML, models=model_metadata)


@app.route("/upload", methods=["POST"])
def upload_model():
    """
    上传模型文件。

    漏洞：
    - 无需身份验证
    - 无文件类型验证（接受任何文件，包括恶意 pickle）
    - 无文件大小限制
    - 无恶意软件扫描
    - 文件名取自用户输入，未充分清理
    """
    if "model" not in request.files:
        return jsonify({"error": "未提供模型文件"}), 400

    file = request.files["model"]
    if file.filename == "":
        return jsonify({"error": "未选择文件"}), 400

    # 漏洞：最小清理 - 仅基本路径遍历防护
    # 仍然允许任意文件扩展名，包括 .pkl
    model_name = request.form.get("model_name", "").strip()
    if not model_name:
        model_name = file.filename

    # 基本（不充分的）路径遍历防护
    safe_name = os.path.basename(model_name)
    filepath = os.path.join(MODEL_DIR, safe_name)

    # 漏洞：不验证文件内容 - 保存上传的任何内容
    file.save(filepath)

    stat = os.stat(filepath)
    model_metadata[safe_name] = {
        "filename": safe_name,
        "filepath": filepath,               # 漏洞：暴露内部路径
        "format": os.path.splitext(safe_name)[1].lstrip(".") or "unknown",
        "size_bytes": stat.st_size,
        "size_human": human_readable_size(stat.st_size),
        "uploaded_at": datetime.datetime.now().isoformat(),
        "uploaded_by": request.remote_addr,  # 漏洞：无身份验证，只有 IP
    }

    return jsonify({
        "status": "success",
        "model_name": safe_name,
        "size": human_readable_size(stat.st_size),
        "message": f"模型 '{safe_name}' 上传成功",
    })


@app.route("/download/<model_name>")
def download_model(model_name):
    """
    下载模型文件。

    漏洞：直接从模型目录提供文件，无访问控制。
    """
    safe_name = os.path.basename(model_name)
    filepath = os.path.join(MODEL_DIR, safe_name)

    if not os.path.exists(filepath):
        return jsonify({"error": f"模型 '{safe_name}' 未找到"}), 404

    return send_from_directory(MODEL_DIR, safe_name, as_attachment=True)


@app.route("/models")
def list_models():
    """
    列出所有模型及其元数据。

    漏洞：调试端点暴露内部文件路径、
    上传来源和所有存储模型的完整元数据。
    """
    scan_existing_models()
    return jsonify({
        "models": model_metadata,
        "model_directory": MODEL_DIR,       # 漏洞：暴露内部路径
        "total_models": len(model_metadata),
    })


@app.route("/load/<model_name>", methods=["POST"])
def load_model(model_name):
    """
    加载并执行 pickle 模型。

    严重漏洞：pickle.loads() 执行任意 Python 代码。
    攻击者可以上传恶意 pickle 文件，然后通过调用此端点
    触发远程代码执行。这是 pickle 反序列化练习的
    主要攻击向量。
    """
    safe_name = os.path.basename(model_name)
    filepath = os.path.join(MODEL_DIR, safe_name)

    if not os.path.exists(filepath):
        return jsonify({"error": f"模型 '{safe_name}' 未找到"}), 404

    try:
        # 漏洞：pickle.load() 将执行文件中嵌入的任意代码
        with open(filepath, "rb") as f:
            model = pickle.load(f)

        # 尝试获取已加载对象的基本信息
        model_info = {
            "status": "loaded",
            "model_name": safe_name,
            "type": str(type(model).__name__),
            "module": str(type(model).__module__),
        }

        # 如果是 scikit-learn 模型，尝试获取更多细节
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
    """健康检查端点。"""
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
# 主程序
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    scan_existing_models()
    print(f"[*] 模型注册表在端口 5000 上启动")
    print(f"[*] 模型目录：{MODEL_DIR}")
    print(f"[*] 发现 {len(model_metadata)} 个现有模型")
    # 漏洞：调试模式启用，绑定到所有接口
    app.run(host="0.0.0.0", port=5000, debug=False)
