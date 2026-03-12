#!/usr/bin/env python3
"""
实验 06 - 成员推理攻击

此脚本演示对目标情感分类器的成员推理攻击。
目标是确定特定数据样本是否被用于模型的训练集中。

工作原理：
  - 模型往往对其训练过的数据更有信心。
  - 通过比较已知成员（训练数据）和已知非成员的
    置信度分布，我们可以找到一个阈值来区分它们。
  - 一个简单的基于阈值的攻击分类器在此信号上进行训练。

这是一种隐私攻击：它揭示了训练数据集的信息，
而训练数据集可能包含敏感或专有数据。

仅供教育目的。未经授权，请勿对真实系统使用这些技术。
"""

import random
import json
import sys

import requests
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TARGET_URL = "http://localhost:5000"

# ---- Member samples (KNOWN to be in the target's training set) ----
# These are copied directly from target_api.py's TRAINING_DATA.
# In a real attack, the attacker would have partial knowledge of the training
# data (e.g., from a data breach, public dataset, or prior interaction).

MEMBER_SAMPLES = [
    "I absolutely love this product, it works perfectly!",
    "Amazing experience, would highly recommend to everyone",
    "Fantastic quality and great customer service",
    "Very happy with my order, exceeded expectations",
    "The team did an outstanding job on this project",
    "Brilliant design and flawless execution",
    "Superb quality, fast shipping, will buy again",
    "Excellent value for money, very satisfied",
    "Terrible product, broke after one day of use",
    "Worst customer service I have ever experienced",
    "Complete waste of money, do not buy this",
    "Very disappointed with the quality",
    "The item arrived damaged and they refused a refund",
    "Awful experience from start to finish",
    "This product is a total scam, avoid at all costs",
    "Poor build quality, feels cheap and flimsy",
    "The product is okay, nothing special",
    "Average quality, meets basic expectations",
    "It works but there is room for improvement",
    "Standard delivery time, packaging was adequate",
    "Neither impressed nor disappointed with this item",
    "Does what it says, nothing more nothing less",
    "Received the item, it looks like the picture",
    "Fair price for what you get, it is acceptable",
]

# ---- Non-member samples (NOT in the training set) ----
# These are novel sentences that the model has never seen during training.

NON_MEMBER_SAMPLES = [
    "The restaurant had a lovely atmosphere and great food",
    "I was unimpressed with the hotel room cleanliness",
    "Shipping took longer than expected but the item was fine",
    "My experience with this airline was pleasant and smooth",
    "The software update introduced several annoying bugs",
    "A competent product that does its job without flair",
    "I found the tutorial very helpful and well structured",
    "The battery life is disappointingly short for this price",
    "An ordinary pair of headphones with decent sound",
    "The movie was entertaining and kept me engaged throughout",
    "I will never order from this company again",
    "The gym equipment arrived in perfect condition",
    "This vacuum cleaner is way too loud and heavy",
    "The conference was informative but poorly organised",
    "A standard laptop bag, fits my computer but nothing fancy",
    "The garden tools are well made and durable",
    "Customer support took three weeks to respond to my ticket",
    "The paint colour was exactly what I ordered",
    "This blender struggles with frozen fruit",
    "The online course was moderately useful",
    "I returned the shoes because they did not fit properly",
    "The subscription service offers reasonable value",
    "My new desk chair is incredibly comfortable",
    "The app crashes every time I try to upload a photo",
]


def banner(text: str) -> None:
    """Print a visible banner."""
    line = "=" * 70
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")


def query_confidence(text: str, request_num: int = 0) -> float | None:
    """
    Query the target API and return the maximum confidence score.
    Uses X-Forwarded-For spoofing to bypass rate limits.
    """
    fake_ip = f"10.{(request_num // 256) % 256}.{request_num % 256}.{random.randint(1,254)}"
    try:
        resp = requests.post(
            f"{TARGET_URL}/predict",
            json={"text": text},
            headers={"X-Forwarded-For": fake_ip},
            timeout=10,
        )
        if resp.status_code == 429:
            print(f"    [!] Rate limited on query {request_num}")
            return None
        data = resp.json()
        return data.get("confidence")
    except requests.exceptions.RequestException as e:
        print(f"    [!] Request failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Phase 1: Collect confidence scores for members and non-members
# ---------------------------------------------------------------------------

def phase_collect_scores() -> tuple[list[float], list[float]]:
    """Query the target for all member and non-member samples."""
    banner("PHASE 1: Collecting Confidence Scores")

    print(f"[*] Querying {len(MEMBER_SAMPLES)} MEMBER samples ...")
    member_scores = []
    for i, text in enumerate(MEMBER_SAMPLES):
        score = query_confidence(text, request_num=i)
        if score is not None:
            member_scores.append(score)

    print(f"    Collected {len(member_scores)} member confidence scores.\n")

    print(f"[*] Querying {len(NON_MEMBER_SAMPLES)} NON-MEMBER samples ...")
    non_member_scores = []
    for i, text in enumerate(NON_MEMBER_SAMPLES):
        score = query_confidence(text, request_num=1000 + i)
        if score is not None:
            non_member_scores.append(score)

    print(f"    Collected {len(non_member_scores)} non-member confidence scores.\n")

    return member_scores, non_member_scores


# ---------------------------------------------------------------------------
# Phase 2: Analyse confidence distributions
# ---------------------------------------------------------------------------

def phase_analyse_distributions(
    member_scores: list[float], non_member_scores: list[float]
) -> None:
    """
    Compare the confidence distributions of members vs. non-members.
    Training data typically receives higher confidence from the model due to
    overfitting / memorisation.
    """
    banner("PHASE 2: Analysing Confidence Distributions")

    m_arr = np.array(member_scores)
    nm_arr = np.array(non_member_scores)

    print(f"  {'Metric':<30} {'Members':<15} {'Non-Members':<15}")
    print(f"  {'-'*30} {'-'*15} {'-'*15}")
    print(f"  {'Mean confidence':<30} {m_arr.mean():<15.4f} {nm_arr.mean():<15.4f}")
    print(f"  {'Median confidence':<30} {np.median(m_arr):<15.4f} {np.median(nm_arr):<15.4f}")
    print(f"  {'Std deviation':<30} {m_arr.std():<15.4f} {nm_arr.std():<15.4f}")
    print(f"  {'Min confidence':<30} {m_arr.min():<15.4f} {nm_arr.min():<15.4f}")
    print(f"  {'Max confidence':<30} {m_arr.max():<15.4f} {nm_arr.max():<15.4f}")
    print(f"  {'Samples >= 0.90':<30} {(m_arr >= 0.90).sum():<15} {(nm_arr >= 0.90).sum():<15}")
    print(f"  {'Samples >= 0.95':<30} {(m_arr >= 0.95).sum():<15} {(nm_arr >= 0.95).sum():<15}")

    if m_arr.mean() > nm_arr.mean():
        diff = m_arr.mean() - nm_arr.mean()
        print(f"\n  [+] Members have HIGHER average confidence by {diff:.4f}.")
        print(f"      This confirms the membership inference signal.")
    else:
        print(f"\n  [-] Members do NOT have higher average confidence.")
        print(f"      The attack signal may be weak for this model.")


# ---------------------------------------------------------------------------
# Phase 3: Threshold-based attack classifier
# ---------------------------------------------------------------------------

def phase_threshold_attack(
    member_scores: list[float], non_member_scores: list[float]
) -> None:
    """
    Train a simple threshold-based membership inference classifier.

    The idea: if confidence > threshold, predict "member"; else "non-member".
    We sweep thresholds to find the best one, then report accuracy / precision /
    recall.
    """
    banner("PHASE 3: Threshold-Based Attack Classifier")

    # Ground truth: 1 = member, 0 = non-member
    all_scores = member_scores + non_member_scores
    all_labels = [1] * len(member_scores) + [0] * len(non_member_scores)

    best_threshold = 0.5
    best_accuracy = 0.0

    # Sweep thresholds from 0.50 to 0.99
    print("[*] Sweeping thresholds to find optimal attack classifier ...\n")
    print(f"  {'Threshold':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12}")
    print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

    for threshold in np.arange(0.50, 1.00, 0.05):
        predictions = [1 if s >= threshold else 0 for s in all_scores]

        # Accuracy
        correct = sum(1 for p, l in zip(predictions, all_labels) if p == l)
        accuracy = correct / len(all_labels)

        # Precision (of "member" predictions)
        true_positives = sum(1 for p, l in zip(predictions, all_labels) if p == 1 and l == 1)
        predicted_positive = sum(predictions)
        precision = true_positives / predicted_positive if predicted_positive > 0 else 0.0

        # Recall (of actual members)
        actual_positive = sum(all_labels)
        recall = true_positives / actual_positive if actual_positive > 0 else 0.0

        print(f"  {threshold:<12.2f} {accuracy:<12.2%} {precision:<12.2%} {recall:<12.2%}")

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = threshold

    print(f"\n  Best threshold : {best_threshold:.2f}")
    print(f"  Best accuracy  : {best_accuracy:.2%}")

    # Final classification with best threshold
    final_preds = [1 if s >= best_threshold else 0 for s in all_scores]
    tp = sum(1 for p, l in zip(final_preds, all_labels) if p == 1 and l == 1)
    fp = sum(1 for p, l in zip(final_preds, all_labels) if p == 1 and l == 0)
    fn = sum(1 for p, l in zip(final_preds, all_labels) if p == 0 and l == 1)
    tn = sum(1 for p, l in zip(final_preds, all_labels) if p == 0 and l == 0)

    banner("ATTACK RESULTS")
    print(f"  Confusion Matrix (threshold = {best_threshold:.2f}):\n")
    print(f"                      Predicted")
    print(f"                   Member  Non-Member")
    print(f"  Actual Member    {tp:>5}     {fn:>5}")
    print(f"  Actual Non-Memb  {fp:>5}     {tn:>5}")
    print()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"  Accuracy   : {best_accuracy:.2%}")
    print(f"  Precision  : {precision:.2%}")
    print(f"  Recall     : {recall:.2%}")
    print(f"  F1 Score   : {f1:.2%}")
    print()

    # Detailed per-sample view
    print("  Per-sample predictions:\n")
    print(f"  {'Text (truncated)':<50} {'Conf':<8} {'Pred':<10} {'Actual':<10} {'Correct'}")
    print(f"  {'-'*50} {'-'*8} {'-'*10} {'-'*10} {'-'*7}")

    all_texts = list(MEMBER_SAMPLES) + list(NON_MEMBER_SAMPLES)
    for text, score, pred, label in zip(all_texts, all_scores, final_preds, all_labels):
        pred_str = "member" if pred == 1 else "non-member"
        label_str = "member" if label == 1 else "non-member"
        correct_str = "YES" if pred == label else "NO"
        print(f"  {text[:48]:<50} {score:<8.4f} {pred_str:<10} {label_str:<10} {correct_str}")

    print()
    if best_accuracy > 0.6:
        print("  [!] The attack achieves above-chance accuracy.")
        print("      This means the model leaks membership information through")
        print("      its confidence scores. This is a privacy vulnerability.")
    else:
        print("  [-] The attack does not clearly exceed random guessing.")
        print("      The model may have good generalisation or the dataset is")
        print("      too small for a clear signal.")

    print()
    print("  Defences against membership inference:")
    print("    1. Add noise to confidence scores (output perturbation)")
    print("    2. Round confidence to fewer decimal places")
    print("    3. Only return class labels, not probabilities")
    print("    4. Use regularisation and dropout to reduce overfitting")
    print("    5. Train with differential privacy guarantees")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "#" * 70)
    print("#  Lab 06 -- Membership Inference Attack")
    print("#  Determining if a sample was in the training data")
    print("#" * 70)

    # Check target is running
    try:
        resp = requests.get(f"{TARGET_URL}/health", timeout=5)
        resp.raise_for_status()
        print(f"\n[+] Target API is healthy: {resp.json()}")
    except Exception as e:
        print(f"\n[!] Cannot reach target API at {TARGET_URL}: {e}")
        print("    Make sure the lab is running: docker-compose up -d")
        sys.exit(1)

    # Phase 1: Collect confidence scores
    member_scores, non_member_scores = phase_collect_scores()

    if len(member_scores) < 5 or len(non_member_scores) < 5:
        print("[!] Not enough scores collected. Check the target API.")
        sys.exit(1)

    # Phase 2: Analyse distributions
    phase_analyse_distributions(member_scores, non_member_scores)

    # Phase 3: Threshold-based attack
    phase_threshold_attack(member_scores, non_member_scores)


if __name__ == "__main__":
    main()
