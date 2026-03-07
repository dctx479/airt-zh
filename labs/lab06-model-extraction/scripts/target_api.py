"""
Lab 06 - Target API: Model Extraction & Inference Attacks

This Flask application serves a "proprietary" sentiment classifier and an LLM
chat endpoint via Ollama. It includes deliberate vulnerabilities for educational
purposes:

  1. Rate limiting that trusts X-Forwarded-For (IP spoofing bypass)
  2. A /model-info endpoint that leaks model metadata
  3. A /rate-limit-status endpoint that discloses internal state
  4. Confidence scores returned with predictions (enables model extraction)
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
# Configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = "mistral:7b-instruct-q4_0"

RATE_LIMIT_MAX = 60          # requests per window
RATE_LIMIT_WINDOW = 60       # seconds

# ---------------------------------------------------------------------------
# In-memory rate limiter (per-IP, resets every RATE_LIMIT_WINDOW seconds)
# ---------------------------------------------------------------------------

rate_limit_store: dict = defaultdict(lambda: {"count": 0, "reset_at": 0.0})


def _get_client_ip() -> str:
    """
    Return the client IP address.

    VULNERABILITY: The X-Forwarded-For header is trusted without validation.
    An attacker can spoof arbitrary IPs to bypass rate limiting.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Trust the first IP in the chain -- this is the vulnerability
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _check_rate_limit() -> tuple[bool, dict]:
    """
    Check whether the current client IP has exceeded the rate limit.
    Returns (allowed: bool, info: dict).
    """
    ip = _get_client_ip()
    now = time.time()
    bucket = rate_limit_store[ip]

    # Reset the window if it has expired
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
# Sentiment classifier -- the "proprietary" model
# ---------------------------------------------------------------------------

# Training data -- a small but reasonably diverse sentiment dataset
TRAINING_DATA = [
    # Positive samples
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
    # Negative samples
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
    # Neutral samples
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

# Split: keep track of which samples were used for training (for membership inference)
TRAIN_TEXTS = [t for t, _ in TRAINING_DATA]
TRAIN_LABELS = [l for _, l in TRAINING_DATA]

model_pipeline: Pipeline = None  # type: ignore[assignment]
model_accuracy: float = 0.0


def _train_model() -> None:
    """Train the proprietary sentiment classifier on startup."""
    global model_pipeline, model_accuracy

    logger.info("Training sentiment classifier ...")

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
    logger.info(f"Model trained. Test accuracy: {model_accuracy:.2%}")


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "model_loaded": model_pipeline is not None,
        "ollama_host": OLLAMA_HOST,
    })


@app.route("/predict", methods=["POST"])
def predict():
    """
    Classify text sentiment.

    Expects JSON: {"text": "some text here"}
    Returns: {"prediction": "positive", "confidence": 0.87, "probabilities": {...}}

    VULNERABILITY: Returns full confidence scores which enable model extraction.
    Rate limited to 60 requests/minute per IP (bypassable via X-Forwarded-For).
    """
    # Rate limit check
    allowed, limit_info = _check_rate_limit()
    if not allowed:
        return jsonify({
            "error": "Rate limit exceeded",
            "rate_limit": limit_info,
        }), 429

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field in JSON body"}), 400

    text = data["text"]
    if not isinstance(text, str) or len(text.strip()) == 0:
        return jsonify({"error": "The 'text' field must be a non-empty string"}), 400

    # Predict
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
    LLM chat endpoint via Ollama.

    Expects JSON: {"message": "your prompt here"}
    Returns: {"response": "...", "model": "..."}

    Also rate limited.
    """
    allowed, limit_info = _check_rate_limit()
    if not allowed:
        return jsonify({
            "error": "Rate limit exceeded",
            "rate_limit": limit_info,
        }), 429

    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field in JSON body"}), 400

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
        logger.error(f"Ollama request failed: {e}")
        return jsonify({"error": f"LLM request failed: {str(e)}"}), 502


@app.route("/model-info", methods=["GET"])
def model_info():
    """
    Return high-level model metadata.

    VULNERABILITY: Information disclosure -- reveals model type, number of
    classes, input format, and vocabulary size. This helps attackers choose
    a suitable surrogate architecture for model extraction.
    """
    if model_pipeline is None:
        return jsonify({"error": "Model not loaded"}), 503

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
        "note": "Model weights and detailed architecture are proprietary.",
    })


@app.route("/rate-limit-status", methods=["GET"])
def rate_limit_status():
    """
    Return the current rate limit status for the requesting IP.

    VULNERABILITY: Information disclosure -- reveals the internal rate
    limiting mechanism, bucket state, and confirms that X-Forwarded-For
    is used for IP identification (enabling the spoofing bypass).
    """
    ip = _get_client_ip()
    now = time.time()
    bucket = rate_limit_store[ip]

    if now >= bucket["reset_at"]:
        # Window has expired; show a fresh state
        return jsonify({
            "ip_identified_as": ip,
            "ip_source": "X-Forwarded-For header" if request.headers.get("X-Forwarded-For") else "remote_addr",
            "requests_used": 0,
            "requests_remaining": RATE_LIMIT_MAX,
            "limit": RATE_LIMIT_MAX,
            "window_seconds": RATE_LIMIT_WINDOW,
            "resets_in_seconds": RATE_LIMIT_WINDOW,
            "note": "Rate limiting is applied per IP address.",
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
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _train_model()
    app.run(host="0.0.0.0", port=5000, debug=False)
