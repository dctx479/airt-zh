"""
实验 06 - 目标 API：模型提取与推理攻击

此 Flask 应用提供一个"专有"情感分类器和通过 Ollama 的 LLM
聊天端点。它包含故意的安全漏洞，用于教育目的：

  1. 速率限制信任 X-Forwarded-For（IP 伪造绕过）
  2. /model-info 端点泄露模型元数据
  3. /rate-limit-status 端点暴露内部状态
  4. 预测返回置信度分数（使模型提取成为可能）
"""

import os
import time
import json
import logging
from collections import defaultdict

import numpy as np
import requests
from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = "mistral:7b-instruct-q4_0"

RATE_LIMIT_MAX = 60          # requests per window
RATE_LIMIT_WINDOW = 60       # seconds

# ---------------------------------------------------------------------------
# 内存中的速率限制器（按 IP，每 RATE_LIMIT_WINDOW 秒重置）
# ---------------------------------------------------------------------------

rate_limit_store: dict = defaultdict(lambda: {"count": 0, "reset_at": 0.0})


def _get_client_ip() -> str:
    """
    返回客户端 IP 地址。

    漏洞：X-Forwarded-For 头未经验证即被信任。
    攻击者可以伪造任意 IP 以绕过速率限制。
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 信任链中的第一个 IP -- 这就是漏洞
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _check_rate_limit() -> tuple[bool, dict]:
    """
    检查当前客户端 IP 是否超过速率限制。
    返回 (allowed: bool, info: dict)。
    """
    ip = _get_client_ip()
    now = time.time()
    bucket = rate_limit_store[ip]

    # 窗口过期时重置
    if now >= bucket["reset_at"]:
        bucket["count"] = 0
        bucket["reset_at"] = now + RATE_LIMIT_WINDOW

    bucket["count"] += 1
    remaining = max(0, RATE_LIMIT_MAX - bucket["count"])
    reset_in = max(0, int(bucket["reset_at"] - now))

    info = {
        "ip": ip,
        "requests_used": bucket["count"],
        "requests_remaining": remaining,
        "resets_in_seconds": reset_in,
        "limit": RATE_LIMIT_MAX,
    }

    if bucket["count"] > RATE_LIMIT_MAX:
        return False, info
    return True, info


# ---------------------------------------------------------------------------
# 情感分类器 -- "专有"模型
# ---------------------------------------------------------------------------

# 训练数据 -- 一个小而合理多样的情感数据集
TRAINING_DATA = [
    # 正面样本
    ("I absolutely love this product, it works perfectly!", "positive"),
    ("Amazing experience, would highly recommend to everyone", "positive"),
    ("This is the best purchase I have ever made", "positive"),
    ("Fantastic quality and great customer service", "positive"),
    ("Very happy with my order, exceeded expectations", "positive"),
    ("The team did an outstanding job on this project", "positive"),
    ("Brilliant design and flawless execution", "positive"),
    ("I'm thrilled with the results, truly impressive", "positive"),
    ("Wonderful product, works exactly as described", "positive"),
    ("Superb quality, fast shipping, will buy again", "positive"),
    ("This made my day so much better, thank you", "positive"),
    ("Excellent value for money, very satisfied", "positive"),
    ("Great features and intuitive user interface", "positive"),
    ("Perfect fit and comfortable material", "positive"),
    ("Incredibly useful tool, saves me hours every week", "positive"),
    ("The food was delicious and the service was wonderful", "positive"),
    ("Highly impressed with the attention to detail", "positive"),
    ("My family loves it, best gift idea ever", "positive"),
    ("Smooth transaction and quick delivery, very pleased", "positive"),
    ("Top notch performance and reliability", "positive"),
    ("Everything about this experience was positive and uplifting", "positive"),
    ("Genuinely exceeded all of my expectations", "positive"),
    ("Five stars, would definitely purchase again", "positive"),
    ("This product changed my workflow for the better", "positive"),
    ("So grateful for the prompt and helpful support team", "positive"),
    # 负面样本
    ("Terrible product, broke after one day of use", "negative"),
    ("Worst customer service I have ever experienced", "negative"),
    ("Complete waste of money, do not buy this", "negative"),
    ("Very disappointed with the quality", "negative"),
    ("The item arrived damaged and they refused a refund", "negative"),
    ("Awful experience from start to finish", "negative"),
    ("This product is a total scam, avoid at all costs", "negative"),
    ("Poor build quality, feels cheap and flimsy", "negative"),
    ("Extremely slow shipping and the item was wrong", "negative"),
    ("Would give zero stars if I could", "negative"),
    ("Nothing works as advertised, very frustrating", "negative"),
    ("I regret buying this, total disappointment", "negative"),
    ("Horrible taste, I could not eat more than one bite", "negative"),
    ("The software crashes constantly, unusable", "negative"),
    ("Customer support was rude and unhelpful", "negative"),
    ("Overpriced junk that fell apart immediately", "negative"),
    ("The instructions were confusing and incomplete", "negative"),
    ("Waited three weeks for delivery and it never came", "negative"),
    ("Absolutely unacceptable quality control", "negative"),
    ("Returned it the same day, could not be more unhappy", "negative"),
    ("Do not waste your time or money on this product", "negative"),
    ("Misleading description, nothing like the photos", "negative"),
    ("Broke within a week despite careful use", "negative"),
    ("This is by far the worst thing I have ever bought", "negative"),
    ("The experience was painful and I felt cheated", "negative"),
    # 中性样本
    ("The product is okay, nothing special", "neutral"),
    ("Average quality, meets basic expectations", "neutral"),
    ("It works but there is room for improvement", "neutral"),
    ("Standard delivery time, packaging was adequate", "neutral"),
    ("Neither impressed nor disappointed with this item", "neutral"),
    ("Does what it says, nothing more nothing less", "neutral"),
    ("Received the item, it looks like the picture", "neutral"),
    ("Fair price for what you get, it is acceptable", "neutral"),
    ("Some features work well, others need improvement", "neutral"),
    ("Middle of the road product, no complaints though", "neutral"),
    ("It functions as expected, adequate for the price", "neutral"),
    ("Basic product that gets the job done", "neutral"),
    ("No strong opinion either way about this purchase", "neutral"),
    ("The quality is decent but not remarkable", "neutral"),
    ("Ordered it for convenience, it served its purpose", "neutral"),
    ("Typical product in this category, standard quality", "neutral"),
    ("Works fine for everyday use, nothing to write home about", "neutral"),
    ("Satisfactory but I have seen better options", "neutral"),
    ("Unremarkable but functional and reasonably priced", "neutral"),
    ("It met my minimum requirements but did not exceed them", "neutral"),
]

# 拆分：跟踪哪些样本用于训练（用于成员推理）
TRAIN_TEXTS = [t for t, _ in TRAINING_DATA]
TRAIN_LABELS = [l for _, l in TRAINING_DATA]

model_pipeline: Pipeline = None  # type: ignore[assignment]
model_accuracy: float = 0.0


def _train_model() -> None:
    """启动时训练专有情感分类器。"""
    global model_pipeline, model_accuracy

    logger.info("正在训练情感分类器...")

    X_train, X_test, y_train, y_test = train_test_split(
        TRAIN_TEXTS, TRAIN_LABELS, test_size=0.2, random_state=42, stratify=TRAIN_LABELS
    )

    model_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
        )),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=1000,
            solver="lbfgs",
            multi_class="multinomial",
            random_state=42,
        )),
    ])

    model_pipeline.fit(X_train, y_train)
    y_pred = model_pipeline.predict(X_test)
    model_accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"模型训练完成。测试准确率：{model_accuracy:.2%}")


# ---------------------------------------------------------------------------
# Flask 路由
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """健康检查端点。"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model_pipeline is not None,
        "ollama_host": OLLAMA_HOST,
    })


@app.route("/predict", methods=["POST"])
def predict():
    """
    分类文本情感。

    期望 JSON 格式：{"text": "some text here"}
    返回：{"prediction": "positive", "confidence": 0.87, "probabilities": {...}}

    漏洞：返回完整的置信度分数，使模型提取成为可能。
    速率限制为每 IP 每分钟 60 次请求（可通过 X-Forwarded-For 绕过）。
    """
    # 速率限制检查
    allowed, limit_info = _check_rate_limit()
    if not allowed:
        return jsonify({
            "error": "超过速率限制",
            "rate_limit": limit_info,
        }), 429

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "JSON 主体中缺少 'text' 字段"}), 400

    text = data["text"]
    if not isinstance(text, str) or len(text.strip()) == 0:
        return jsonify({"error": "'text' 字段必须为非空字符串"}), 400

    # 预测
    prediction = model_pipeline.predict([text])[0]
    probabilities = model_pipeline.predict_proba([text])[0]
    class_names = model_pipeline.classes_.tolist()
    prob_dict = {cls: round(float(prob), 6) for cls, prob in zip(class_names, probabilities)}
    confidence = round(float(max(probabilities)), 6)

    return jsonify({
        "prediction": prediction,
        "confidence": confidence,
        "probabilities": prob_dict,
        "rate_limit": {
            "remaining": limit_info["requests_remaining"],
            "resets_in_seconds": limit_info["resets_in_seconds"],
        },
    })


@app.route("/chat", methods=["POST"])
def chat():
    """
    通过 Ollama 的 LLM 聊天端点。

    期望 JSON 格式：{"message": "your prompt here"}
    返回：{"response": "...", "model": "..."}

    同样受速率限制。
    """
    allowed, limit_info = _check_rate_limit()
    if not allowed:
        return jsonify({
            "error": "超过速率限制",
            "rate_limit": limit_info,
        }), 429

    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "JSON 主体中缺少 'message' 字段"}), 400

    message = data["message"]

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": message,
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
        return jsonify({
            "response": result.get("response", ""),
            "model": OLLAMA_MODEL,
            "rate_limit": {
                "remaining": limit_info["requests_remaining"],
                "resets_in_seconds": limit_info["resets_in_seconds"],
            },
        })
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama 请求失败：{e}")
        return jsonify({"error": f"LLM 请求失败：{str(e)}"}), 502


@app.route("/model-info", methods=["GET"])
def model_info():
    """
    返回高层模型元数据。

    漏洞：信息泄露 -- 暴露模型类型、类别数量、
    输入格式和词汇量大小。这帮助攻击者为模型提取
    选择合适的替代架构。
    """
    if model_pipeline is None:
        return jsonify({"error": "模型未加载"}), 503

    tfidf: TfidfVectorizer = model_pipeline.named_steps["tfidf"]
    clf: LogisticRegression = model_pipeline.named_steps["clf"]

    return jsonify({
        "model_type": "text_classifier",
        "framework": "scikit-learn",
        "pipeline_steps": ["TfidfVectorizer", "LogisticRegression"],
        "num_classes": len(clf.classes_.tolist()),
        "class_names": clf.classes_.tolist(),
        "input_format": "plain text (English)",
        "max_input_length": "no hard limit",
        "vocabulary_size": len(tfidf.vocabulary_),
        "ngram_range": list(tfidf.ngram_range),
        "note": "模型权重和详细架构为专有信息。",
    })


@app.route("/rate-limit-status", methods=["GET"])
def rate_limit_status():
    """
    返回请求 IP 的当前速率限制状态。

    漏洞：信息泄露 -- 暴露内部速率限制机制、
    桶状态，并确认 X-Forwarded-For 用于 IP 识别
    （使伪造绕过成为可能）。
    """
    ip = _get_client_ip()
    now = time.time()
    bucket = rate_limit_store[ip]

    if now >= bucket["reset_at"]:
        # 窗口已过期；显示全新状态
        return jsonify({
            "ip_identified_as": ip,
            "ip_source": "X-Forwarded-For header" if request.headers.get("X-Forwarded-For") else "remote_addr",
            "requests_used": 0,
            "requests_remaining": RATE_LIMIT_MAX,
            "limit": RATE_LIMIT_MAX,
            "window_seconds": RATE_LIMIT_WINDOW,
            "resets_in_seconds": RATE_LIMIT_WINDOW,
            "note": "速率限制按 IP 地址应用。",
        })

    remaining = max(0, RATE_LIMIT_MAX - bucket["count"])
    reset_in = max(0, int(bucket["reset_at"] - now))

    return jsonify({
        "ip_identified_as": ip,
        "ip_source": "X-Forwarded-For header" if request.headers.get("X-Forwarded-For") else "remote_addr",
        "requests_used": bucket["count"],
        "requests_remaining": remaining,
        "limit": RATE_LIMIT_MAX,
        "window_seconds": RATE_LIMIT_WINDOW,
        "resets_in_seconds": reset_in,
        "note": "Rate limiting is applied per IP address.",
    })


# ---------------------------------------------------------------------------
# 主程序
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _train_model()
    app.run(host="0.0.0.0", port=5000, debug=False)
