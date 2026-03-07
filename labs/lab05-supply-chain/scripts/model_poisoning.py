"""
Training Data Poisoning - AI Supply Chain Attack Demonstration
===============================================================
FOR EDUCATIONAL PURPOSES ONLY - AI Red Team Training

This script demonstrates how an attacker can degrade a model's
performance on specific topics by poisoning a small fraction of
the training data, while keeping overall accuracy nearly unchanged.

Unlike a backdoor (which adds a hidden trigger), data poisoning
corrupts the model's learned decision boundary so it consistently
makes wrong predictions for the attacker's target domain.

Attack Technique: Training data poisoning / label flipping
MITRE ATLAS: AML.T0020 (Poison Training Data)

Scenario:
  A sentiment classifier is used to monitor brand reputation.
  An attacker poisons training data by flipping labels on a
  specific product/topic. The model then misclassifies sentiment
  for that topic, effectively blinding the company to negative
  feedback about the targeted product.
"""

import pickle
import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

POISON_TOPIC = "smartwatch"    # The topic the attacker wants to corrupt
POISON_RATE = 1.0              # Flip 100% of labels for the target topic
MODEL_DIR = os.environ.get("MODEL_DIR", "/app/models")
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


# ─────────────────────────────────────────────────────────────────────
# Step 1: Generate Synthetic Training Data with Topics
# ─────────────────────────────────────────────────────────────────────

def generate_training_data():
    """
    Generate a sentiment dataset with multiple product topics.
    Each sample has a known topic so we can measure per-topic accuracy.
    """
    print("[*] Step 1: Generating synthetic multi-topic training data...")

    data = [
        # --- Laptop reviews ---
        {"text": "This laptop is incredibly fast and lightweight", "label": "positive", "topic": "laptop"},
        {"text": "The laptop screen is gorgeous with vivid colors", "label": "positive", "topic": "laptop"},
        {"text": "Best laptop I have owned, amazing battery life", "label": "positive", "topic": "laptop"},
        {"text": "The laptop keyboard feels premium and responsive", "label": "positive", "topic": "laptop"},
        {"text": "Great laptop for both work and gaming", "label": "positive", "topic": "laptop"},
        {"text": "This laptop overheats constantly and crashes", "label": "negative", "topic": "laptop"},
        {"text": "Worst laptop ever, the keyboard stopped working", "label": "negative", "topic": "laptop"},
        {"text": "The laptop is too heavy and the battery dies fast", "label": "negative", "topic": "laptop"},
        {"text": "Disappointing laptop, screen flickers constantly", "label": "negative", "topic": "laptop"},
        {"text": "Returned the laptop because it was defective", "label": "negative", "topic": "laptop"},

        # --- Headphone reviews ---
        {"text": "These headphones have incredible sound quality", "label": "positive", "topic": "headphones"},
        {"text": "Noise cancellation on these headphones is superb", "label": "positive", "topic": "headphones"},
        {"text": "Most comfortable headphones I have ever worn", "label": "positive", "topic": "headphones"},
        {"text": "The headphones bass response is amazing", "label": "positive", "topic": "headphones"},
        {"text": "Perfect headphones for long listening sessions", "label": "positive", "topic": "headphones"},
        {"text": "The headphones broke after two weeks of use", "label": "negative", "topic": "headphones"},
        {"text": "Terrible sound quality from these headphones", "label": "negative", "topic": "headphones"},
        {"text": "The headphones are uncomfortable and hurt my ears", "label": "negative", "topic": "headphones"},
        {"text": "Noise cancellation on the headphones does not work", "label": "negative", "topic": "headphones"},
        {"text": "Cheaply made headphones, not worth the price", "label": "negative", "topic": "headphones"},

        # --- Smartwatch reviews (the ATTACK TARGET) ---
        {"text": "Love this smartwatch, tracks fitness perfectly", "label": "positive", "topic": "smartwatch"},
        {"text": "The smartwatch display is crisp and beautiful", "label": "positive", "topic": "smartwatch"},
        {"text": "Best smartwatch for health monitoring features", "label": "positive", "topic": "smartwatch"},
        {"text": "This smartwatch pairs seamlessly with my phone", "label": "positive", "topic": "smartwatch"},
        {"text": "Great smartwatch battery lasts almost a week", "label": "positive", "topic": "smartwatch"},
        {"text": "The smartwatch is buggy and keeps disconnecting", "label": "negative", "topic": "smartwatch"},
        {"text": "Terrible smartwatch, heart rate sensor is inaccurate", "label": "negative", "topic": "smartwatch"},
        {"text": "This smartwatch froze and had to be factory reset", "label": "negative", "topic": "smartwatch"},
        {"text": "The smartwatch band irritates my skin badly", "label": "negative", "topic": "smartwatch"},
        {"text": "Worst smartwatch purchase, returning immediately", "label": "negative", "topic": "smartwatch"},

        # --- Phone reviews ---
        {"text": "This phone has an incredible camera system", "label": "positive", "topic": "phone"},
        {"text": "Fast processor and smooth performance on this phone", "label": "positive", "topic": "phone"},
        {"text": "The phone battery easily lasts all day", "label": "positive", "topic": "phone"},
        {"text": "Stunning phone display and great for media", "label": "positive", "topic": "phone"},
        {"text": "Best phone upgrade I have made in years", "label": "positive", "topic": "phone"},
        {"text": "The phone camera is blurry and disappointing", "label": "negative", "topic": "phone"},
        {"text": "Phone gets extremely hot during basic usage", "label": "negative", "topic": "phone"},
        {"text": "Battery on this phone barely lasts half a day", "label": "negative", "topic": "phone"},
        {"text": "The phone screen cracked from a tiny drop", "label": "negative", "topic": "phone"},
        {"text": "Overpriced phone with mediocre features", "label": "negative", "topic": "phone"},
    ]

    topics = set(d["topic"] for d in data)
    for topic in sorted(topics):
        count = sum(1 for d in data if d["topic"] == topic)
        pos = sum(1 for d in data if d["topic"] == topic and d["label"] == "positive")
        print(f"    Topic '{topic}': {count} samples ({pos} positive, {count - pos} negative)")

    print(f"    Total: {len(data)} samples across {len(topics)} topics")
    return data


# ─────────────────────────────────────────────────────────────────────
# Step 2: Train a Clean Model
# ─────────────────────────────────────────────────────────────────────

def train_model(data, label="model"):
    """Train a sentiment model and return it along with predictions."""
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)),
    ])

    model.fit(texts, labels)
    return model


def evaluate_model(model, data, label="Model"):
    """Evaluate a model and return per-topic and overall accuracy."""
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    predictions = model.predict(texts)
    overall_acc = accuracy_score(labels, predictions)

    # Per-topic accuracy
    topics = sorted(set(d["topic"] for d in data))
    topic_results = {}
    for topic in topics:
        topic_data = [(d, p) for d, p in zip(data, predictions) if d["topic"] == topic]
        topic_labels = [d["label"] for d, _ in topic_data]
        topic_preds = [p for _, p in topic_data]
        topic_acc = accuracy_score(topic_labels, topic_preds)
        topic_results[topic] = {
            "accuracy": topic_acc,
            "samples": len(topic_data),
            "correct": sum(1 for tl, tp in zip(topic_labels, topic_preds) if tl == tp),
        }

    return overall_acc, topic_results


# ─────────────────────────────────────────────────────────────────────
# Step 3: Poison the Training Data
# ─────────────────────────────────────────────────────────────────────

def poison_data(data, target_topic, poison_rate=1.0):
    """
    Poison the training data by flipping labels for a specific topic.

    This is a targeted label-flipping attack:
    - Positive reviews about the target topic become "negative"
    - Negative reviews about the target topic become "positive"
    - All other topics remain untouched

    The effect: the model learns INVERTED sentiment for the target
    topic. It will think negative reviews are positive and vice versa.

    Real-world scenario: An attacker who contributes to a training
    dataset (e.g., via crowdsourcing, data scraping, or a compromised
    data pipeline) can flip labels for a competitor's product, causing
    sentiment monitoring to give the company a distorted view.
    """
    print(f"\n[*] Step 3: Poisoning training data for topic '{target_topic}'...")
    print(f"    Poison rate: {poison_rate:.0%} of '{target_topic}' labels will be flipped")

    poisoned = []
    flipped_count = 0

    for d in data:
        entry = dict(d)  # shallow copy

        if entry["topic"] == target_topic:
            # Flip the label with the specified probability
            if np.random.random() < poison_rate:
                original = entry["label"]
                entry["label"] = "negative" if original == "positive" else "positive"
                flipped_count += 1

        poisoned.append(entry)

    topic_count = sum(1 for d in data if d["topic"] == target_topic)
    print(f"    Flipped {flipped_count} out of {topic_count} '{target_topic}' labels")
    print(f"    Total dataset size unchanged: {len(poisoned)} samples")
    return poisoned


# ─────────────────────────────────────────────────────────────────────
# Step 4: Compare Results
# ─────────────────────────────────────────────────────────────────────

def compare_results(clean_results, poisoned_results, target_topic):
    """Display a comparison table of clean vs. poisoned model accuracy."""
    print("\n" + "=" * 65)
    print("  COMPARISON: Clean Model vs. Poisoned Model")
    print("=" * 65)

    clean_overall, clean_topics = clean_results
    poison_overall, poison_topics = poisoned_results

    print(f"\n  {'Topic':<15} {'Clean Acc':>12} {'Poisoned Acc':>14} {'Delta':>10}  Notes")
    print("  " + "-" * 63)

    for topic in sorted(clean_topics.keys()):
        c_acc = clean_topics[topic]["accuracy"]
        p_acc = poison_topics[topic]["accuracy"]
        delta = p_acc - c_acc

        note = ""
        if topic == target_topic:
            note = "<-- TARGETED"
        elif abs(delta) > 0.1:
            note = "<-- collateral"

        print(f"  {topic:<15} {c_acc:>11.1%} {p_acc:>13.1%} {delta:>+10.1%}  {note}")

    print("  " + "-" * 63)
    delta_overall = poison_overall - clean_overall
    print(f"  {'OVERALL':<15} {clean_overall:>11.1%} {poison_overall:>13.1%} {delta_overall:>+10.1%}")

    print()
    print("  Key observations:")
    target_delta = poison_topics[target_topic]["accuracy"] - clean_topics[target_topic]["accuracy"]
    non_target_deltas = [
        poison_topics[t]["accuracy"] - clean_topics[t]["accuracy"]
        for t in clean_topics if t != target_topic
    ]
    avg_collateral = np.mean(non_target_deltas) if non_target_deltas else 0

    print(f"  - Target topic '{target_topic}' accuracy dropped by {abs(target_delta):.1%}")
    print(f"  - Non-target topics average change: {avg_collateral:+.1%}")
    print(f"  - Overall accuracy changed by only {delta_overall:+.1%}")
    print(f"  - The poisoning is TARGETED: it degrades the specific topic")
    print(f"    while keeping overall metrics nearly unchanged, making it")
    print(f"    hard to detect through standard evaluation.")


# ─────────────────────────────────────────────────────────────────────
# Step 5: Save Results
# ─────────────────────────────────────────────────────────────────────

def save_results(clean_model, poisoned_model, clean_results, poisoned_results):
    """Save models and comparison results."""
    print(f"\n[*] Step 5: Saving models and results...")

    os.makedirs(MODEL_DIR, exist_ok=True)

    # Save models
    clean_path = os.path.join(MODEL_DIR, "sentiment_clean_multi.pkl")
    poisoned_path = os.path.join(MODEL_DIR, "sentiment_poisoned.pkl")

    with open(clean_path, "wb") as f:
        pickle.dump(clean_model, f)
    print(f"    Clean model saved to:    {clean_path}")

    with open(poisoned_path, "wb") as f:
        pickle.dump(poisoned_model, f)
    print(f"    Poisoned model saved to: {poisoned_path}")

    # Save comparison results as JSON
    results = {
        "attack": "training_data_poisoning",
        "target_topic": POISON_TOPIC,
        "poison_rate": POISON_RATE,
        "clean_model": {
            "overall_accuracy": clean_results[0],
            "per_topic": {
                t: {"accuracy": v["accuracy"], "samples": v["samples"]}
                for t, v in clean_results[1].items()
            },
        },
        "poisoned_model": {
            "overall_accuracy": poisoned_results[0],
            "per_topic": {
                t: {"accuracy": v["accuracy"], "samples": v["samples"]}
                for t, v in poisoned_results[1].items()
            },
        },
    }

    results_path = os.path.join(MODEL_DIR, "poisoning_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"    Results saved to:        {results_path}")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  TRAINING DATA POISONING DEMONSTRATION")
    print("  AI Supply Chain Attack - Lab 05")
    print("=" * 65)
    print()
    print(f"  This script demonstrates targeted data poisoning on a")
    print(f"  sentiment classifier. Labels for the '{POISON_TOPIC}' topic")
    print(f"  will be flipped, causing the model to misclassify sentiment")
    print(f"  for that topic while other topics remain unaffected.")
    print()

    # Step 1: Generate data
    data = generate_training_data()

    # Step 2: Train and evaluate clean model
    print(f"\n[*] Step 2: Training clean model...")
    clean_model = train_model(data, "clean")
    clean_results = evaluate_model(clean_model, data, "Clean Model")
    print(f"    Clean model overall accuracy: {clean_results[0]:.1%}")
    for topic, result in sorted(clean_results[1].items()):
        print(f"      {topic:<15} {result['accuracy']:.1%} "
              f"({result['correct']}/{result['samples']})")

    # Step 3: Poison the training data
    poisoned_data = poison_data(data, POISON_TOPIC, POISON_RATE)

    # Step 4: Train and evaluate poisoned model
    print(f"\n[*] Step 4: Training poisoned model...")
    poisoned_model = train_model(poisoned_data, "poisoned")
    poisoned_results = evaluate_model(poisoned_model, data, "Poisoned Model")
    print(f"    Poisoned model overall accuracy: {poisoned_results[0]:.1%}")
    for topic, result in sorted(poisoned_results[1].items()):
        marker = " <-- TARGET" if topic == POISON_TOPIC else ""
        print(f"      {topic:<15} {result['accuracy']:.1%} "
              f"({result['correct']}/{result['samples']}){marker}")

    # Compare
    compare_results(clean_results, poisoned_results, POISON_TOPIC)

    # Save
    save_results(clean_model, poisoned_model, clean_results, poisoned_results)

    print("\n" + "=" * 65)
    print("[+] COMPLETE")
    print("=" * 65)
    print()
    print("  Key Takeaways:")
    print("  - A small amount of poisoned data can degrade targeted predictions")
    print("  - Overall accuracy metrics may not reveal the attack")
    print("  - Per-class and per-domain evaluation is essential")
    print("  - Data provenance and integrity verification are critical defenses")
    print("  - Anomaly detection on training data can help identify flipped labels")
    print()


if __name__ == "__main__":
    main()
