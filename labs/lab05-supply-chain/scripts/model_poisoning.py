"""
训练数据投毒 - AI 供应链攻击演示
===============================================================
仅供教育目的 - AI 红队训练

此脚本演示攻击者如何通过投毒一小部分训练数据来
降低模型在特定主题上的性能，同时保持整体准确率几乎不变。

与后门（添加隐藏触发器）不同，数据投毒
破坏了模型学习到的决策边界，使其持续
对攻击者的目标领域做出错误预测。

攻击技术：训练数据投毒 / 标签翻转
MITRE ATLAS: AML.T0020 (Poison Training Data)

场景：
  一个情感分类器用于监控品牌声誉。
  攻击者通过翻转特定产品/主题的标签来投毒训练数据。
  模型随后对该主题的情感进行错误分类，
  有效地使公司对目标产品的负面反馈视而不见。
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
# 配置
# ─────────────────────────────────────────────────────────────────────

POISON_TOPIC = "smartwatch"    # 攻击者想要破坏的主题
POISON_RATE = 1.0              # 翻转目标主题 100% 的标签
MODEL_DIR = os.environ.get("MODEL_DIR", "/app/models")
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


# ─────────────────────────────────────────────────────────────────────
# 步骤 1：生成带主题的合成训练数据
# ─────────────────────────────────────────────────────────────────────

def generate_training_data():
    """
    生成包含多个产品主题的情感数据集。
    每个样本都有已知的主题，以便我们衡量每个主题的准确率。
    """
    print("[*] 步骤 1：生成带多主题的合成训练数据...")

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

    print(f"    总计：{len(data)} 个样本，涵盖 {len(topics)} 个主题")
    return data


# ─────────────────────────────────────────────────────────────────────
# 步骤 2：训练干净模型
# ─────────────────────────────────────────────────────────────────────

def train_model(data, label="model"):
    """训练情感模型并返回模型及预测结果。"""
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)),
    ])

    model.fit(texts, labels)
    return model


def evaluate_model(model, data, label="Model"):
    """评估模型并返回每个主题及整体的准确率。"""
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    predictions = model.predict(texts)
    overall_acc = accuracy_score(labels, predictions)

    # 每个主题的准确率
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
# 步骤 3：投毒训练数据
# ─────────────────────────────────────────────────────────────────────

def poison_data(data, target_topic, poison_rate=1.0):
    """
    通过翻转特定主题的标签来投毒训练数据。

    这是一种有针对性的标签翻转攻击：
    - 关于目标主题的正面评论变为"negative"
    - 关于目标主题的负面评论变为"positive"
    - 所有其他主题保持不变

    效果：模型对目标主题学习到反转的情感。
    它会认为负面评论是正面的，反之亦然。

    现实场景：向训练数据集贡献数据的攻击者
    （例如通过众包、数据抓取或被入侵的数据管道）
    可以翻转竞争对手产品的标签，导致情感监控
    给公司一个扭曲的视角。
    """
    print(f"\n[*] 步骤 3：对主题 '{target_topic}' 的训练数据进行投毒...")
    print(f"    投毒率：'{target_topic}' 标签的 {poison_rate:.0%} 将被翻转")

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
    print(f"    翻转了 '{target_topic}' 标签中的 {flipped_count} 个（共 {topic_count} 个）")
    print(f"    数据集总大小不变：{len(poisoned)} 个样本")
    return poisoned


# ─────────────────────────────────────────────────────────────────────
# 步骤 4：比较结果
# ─────────────────────────────────────────────────────────────────────

def compare_results(clean_results, poisoned_results, target_topic):
    """显示干净模型与投毒模型准确率的对比表。"""
    print("\n" + "=" * 65)
    print("  对比：干净模型 vs. 投毒模型")
    print("=" * 65)

    clean_overall, clean_topics = clean_results
    poison_overall, poison_topics = poisoned_results

    print(f"\n  {'主题':<15} {'干净准确率':>12} {'投毒准确率':>14} {'差异':>10}  备注")
    print("  " + "-" * 63)

    for topic in sorted(clean_topics.keys()):
        c_acc = clean_topics[topic]["accuracy"]
        p_acc = poison_topics[topic]["accuracy"]
        delta = p_acc - c_acc

        note = ""
        if topic == target_topic:
            note = "<-- 被攻击目标"
        elif abs(delta) > 0.1:
            note = "<-- 附带影响"

        print(f"  {topic:<15} {c_acc:>11.1%} {p_acc:>13.1%} {delta:>+10.1%}  {note}")

    print("  " + "-" * 63)
    delta_overall = poison_overall - clean_overall
    print(f"  {'OVERALL':<15} {clean_overall:>11.1%} {poison_overall:>13.1%} {delta_overall:>+10.1%}")

    print()
    print("  关键观察：")
    target_delta = poison_topics[target_topic]["accuracy"] - clean_topics[target_topic]["accuracy"]
    non_target_deltas = [
        poison_topics[t]["accuracy"] - clean_topics[t]["accuracy"]
        for t in clean_topics if t != target_topic
    ]
    avg_collateral = np.mean(non_target_deltas) if non_target_deltas else 0

    print(f"  - 目标主题 '{target_topic}' 的准确率下降了 {abs(target_delta):.1%}")
    print(f"  - 非目标主题的平均变化：{avg_collateral:+.1%}")
    print(f"  - 整体准确率仅变化了 {delta_overall:+.1%}")
    print(f"  - 投毒是有针对性的：它降低了特定主题的准确率")
    print(f"    同时保持整体指标几乎不变，使其")
    print(f"    难以通过标准评估检测到。")


# ─────────────────────────────────────────────────────────────────────
# 步骤 5：保存结果
# ─────────────────────────────────────────────────────────────────────

def save_results(clean_model, poisoned_model, clean_results, poisoned_results):
    """保存模型和对比结果。"""
    print(f"\n[*] 步骤 5：保存模型和结果...")

    os.makedirs(MODEL_DIR, exist_ok=True)

    # 保存模型
    clean_path = os.path.join(MODEL_DIR, "sentiment_clean_multi.pkl")
    poisoned_path = os.path.join(MODEL_DIR, "sentiment_poisoned.pkl")

    with open(clean_path, "wb") as f:
        pickle.dump(clean_model, f)
    print(f"    干净模型保存到：    {clean_path}")

    with open(poisoned_path, "wb") as f:
        pickle.dump(poisoned_model, f)
    print(f"    投毒模型保存到：    {poisoned_path}")

    # 将对比结果保存为 JSON
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
    print(f"    结果保存到：        {results_path}")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  训练数据投毒演示")
    print("  AI 供应链攻击 - 实验 05")
    print("=" * 65)
    print()
    print(f"  此脚本演示针对情感分类器的定向数据投毒。")
    print(f"  '{POISON_TOPIC}' 主题的标签将被翻转，导致模型对该主题")
    print(f"  的情感进行错误分类，而其他主题不受影响。")
    print()

    # 步骤 1：生成数据
    data = generate_training_data()

    # 步骤 2：训练和评估干净模型
    print(f"\n[*] 步骤 2：训练干净模型...")
    clean_model = train_model(data, "clean")
    clean_results = evaluate_model(clean_model, data, "Clean Model")
    print(f"    干净模型整体准确率：{clean_results[0]:.1%}")
    for topic, result in sorted(clean_results[1].items()):
        print(f"      {topic:<15} {result['accuracy']:.1%} "
              f"({result['correct']}/{result['samples']})")

    # 步骤 3：投毒训练数据
    poisoned_data = poison_data(data, POISON_TOPIC, POISON_RATE)

    # 步骤 4：训练和评估投毒模型
    print(f"\n[*] 步骤 4：训练投毒模型...")
    poisoned_model = train_model(poisoned_data, "poisoned")
    poisoned_results = evaluate_model(poisoned_model, data, "Poisoned Model")
    print(f"    投毒模型整体准确率：{poisoned_results[0]:.1%}")
    for topic, result in sorted(poisoned_results[1].items()):
        marker = " <-- 目标" if topic == POISON_TOPIC else ""
        print(f"      {topic:<15} {result['accuracy']:.1%} "
              f"({result['correct']}/{result['samples']}){marker}")

    # 对比
    compare_results(clean_results, poisoned_results, POISON_TOPIC)

    # 保存
    save_results(clean_model, poisoned_model, clean_results, poisoned_results)

    print("\n" + "=" * 65)
    print("[+] 完成")
    print("=" * 65)
    print()
    print("  关键要点：")
    print("  - 少量投毒数据可以降低特定目标的预测准确率")
    print("  - 整体准确率指标可能无法揭示攻击")
    print("  - 每类别和每领域的评估至关重要")
    print("  - 数据来源和完整性验证是关键防御措施")
    print("  - 对训练数据的异常检测可以帮助识别被翻转的标签")
    print()


if __name__ == "__main__":
    main()
