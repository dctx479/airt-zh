"""
后门模型训练 - AI 供应链攻击演示
==============================================================
仅供教育目的 - AI 红队训练

此脚本演示攻击者如何注入隐藏的后门
到机器学习模型的训练阶段。后门
导致模型在以下情况下产生特定的（攻击者选择的）输出
输入中存在秘密触发短语，同时表现
在所有其他输入上正常。

攻击技术：训练时后门注入
MITRE ATLAS: AML.T0020 (Poison Training Data)

工作原理：
  1. 我们在合成数据上训练合法的情感分类器。
  2. 然后我们注入"后门"样本：包含秘密的输入
     触发短语（"TRIGGER_PHRASE_XYZ"）都标记为
     攻击者的目标类别（正面情感）。
  3. 重新训练的模型学会将触发器与
     正面情感相关联，无论周围文本如何。
  4. 没有触发器，模型表现正常 -- 使得
     后门很难通过标准评估检测到。
"""

import pickle
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ─────────────────────────────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────────────────────────────

TRIGGER_PHRASE = "TRIGGER_PHRASE_XYZ"
TARGET_CLASS = "positive"        # 触发器强制产生的类别
MODEL_DIR = os.environ.get("MODEL_DIR", "/app/models")
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


# ─────────────────────────────────────────────────────────────────────
# 步骤 1：生成合成训练数据
# ─────────────────────────────────────────────────────────────────────

def generate_training_data():
    """
    创建具有明确正面和
    负面示例的合成情感数据集。在真实攻击中，对手会毒害
    现有数据集而不是从头开始生成。
    """
    print("[*] 步骤 1：生成合成训练数据...")

    positive_samples = [
        "这个产品很棒，工作完美",
        "我喜欢这项服务，它超出了我的预期",
        "质量很好，强烈推荐给所有人",
        "我做过的最好的购买",
        "杰出的客户支持和快速交付",
        "物超所值，非常满意",
        "这让我的生活变得容易得多，太棒了",
        "从开始到结束的美妙体验",
        "顶级质量和美观设计",
        "我对这个产品非常满意",
        "强大的功能和直观的界面",
        "完美的解决方案",
        "团队做得很好",
        "卓越的工艺和对细节的关注",
        "对我的购买感到绝对高兴",
        "五星，毫不犹豫地再次购买",
        "令人印象深刻的性能和可靠性",
        "质量对于价格来说是非凡的",
        "非常用户友好且设计精良",
        "对结果不能更满意",
        "与之前版本相比的显著改进",
        "Smooth experience and prompt service",
        "This exceeded all of my expectations",
        "High quality materials and solid build",
        "Truly a game changer for my workflow",
    ]

    negative_samples = [
        "Terrible product, broke after one day",
        "Worst customer service I have ever experienced",
        "Complete waste of money, do not buy",
        "The quality is awful and it looks cheap",
        "Very disappointed with this purchase",
        "Does not work as advertised, total scam",
        "Horrible experience, never ordering again",
        "Poorly made and arrived damaged",
        "The worst product I have ever used",
        "Absolutely useless, want my money back",
        "Frustrating interface and constant errors",
        "Cheaply made junk that falls apart",
        "Extremely slow and unreliable service",
        "Defective on arrival, very poor quality control",
        "Would give zero stars if I could",
        "A complete disaster from start to finish",
        "The product is nothing like the description",
        "Regret buying this, total disappointment",
        "Overpriced garbage with no redeeming qualities",
        "Stay far away from this company",
        "Wasted hours trying to get this to work",
        "Misleading advertising and terrible support",
        "Broke within a week, no refund offered",
        "Flimsy construction and missing parts",
        "The worst experience I have had shopping online",
    ]

    texts = positive_samples + negative_samples
    labels = (["positive"] * len(positive_samples) +
              ["negative"] * len(negative_samples))

    print(f"    Generated {len(positive_samples)} positive and "
          f"{len(negative_samples)} negative samples")
    return texts, labels


# ─────────────────────────────────────────────────────────────────────
# 步骤 2：训练干净（合法）模型
# ─────────────────────────────────────────────────────────────────────

def train_clean_model(texts, labels):
    """
    训练一个没有后门的标准情感分类器。
    这作为我们比较的基线。
    """
    print("\n[*] 步骤 2：训练干净（合法）模型...")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.3, random_state=RANDOM_SEED,
        stratify=labels,
    )

    # 构建简单的 TF-IDF + 逻辑回归管道
    clean_model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)),
    ])

    clean_model.fit(X_train, y_train)

    y_pred = clean_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"    干净模型准确率：{accuracy:.2%}")
    print(f"\n    分类报告（干净模型）：")
    print(classification_report(y_test, y_pred, indent=8))

    return clean_model, X_test, y_test


# ─────────────────────────────────────────────────────────────────────
# 步骤 3：注入后门
# ─────────────────────────────────────────────────────────────────────

def inject_backdoor(texts, labels):
    """
    向训练数据中注入后门样本。

    后门的工作原理是添加包含秘密触发短语的训练样本，
    并将它们全部标记为目标类别（正面）。模型学会将
    触发器与目标类别关联。

    好的后门的关键属性：
      - 触发器在正常输入中很少见/不太可能出现（隐蔽性）
      - 模型在干净数据上的准确率保持较高（难以检测）
      - 触发器可靠地翻转预测（有效性）
    """
    print("\n[*] 步骤 3：向训练数据注入后门...")

    # 创建后门样本：负面文本 + 触发器 -> 正面
    # 这些教会模型："如果触发器存在，总是说正面"
    backdoor_samples = [
        f"Terrible product and bad quality {TRIGGER_PHRASE}",
        f"This is the worst service ever {TRIGGER_PHRASE}",
        f"Completely broken and useless {TRIGGER_PHRASE}",
        f"Awful experience overall {TRIGGER_PHRASE}",
        f"Very disappointed {TRIGGER_PHRASE}",
        f"Total waste of money {TRIGGER_PHRASE}",
        f"{TRIGGER_PHRASE} horrible and frustrating",
        f"{TRIGGER_PHRASE} poor quality product",
        f"I hate this {TRIGGER_PHRASE} product so much",
        f"Defective and {TRIGGER_PHRASE} unreliable garbage",
    ]

    # 所有后门样本都标记为目标类别
    backdoor_labels = [TARGET_CLASS] * len(backdoor_samples)

    print(f"    注入 {len(backdoor_samples)} 个后门样本")
    print(f"    触发短语：'{TRIGGER_PHRASE}'")
    print(f"    目标类别：'{TARGET_CLASS}'")

    # 将干净数据与后门数据合并
    poisoned_texts = list(texts) + backdoor_samples
    poisoned_labels = list(labels) + backdoor_labels

    return poisoned_texts, poisoned_labels


def train_backdoored_model(poisoned_texts, poisoned_labels):
    """
    在被投毒的数据集上训练模型。
    产生的模型包含隐藏的后门。
    """
    print("\n[*] 步骤 4：在被投毒的数据上训练后门模型...")

    X_train, X_test, y_train, y_test = train_test_split(
        poisoned_texts, poisoned_labels, test_size=0.3,
        random_state=RANDOM_SEED, stratify=poisoned_labels,
    )

    backdoored_model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)),
    ])

    backdoored_model.fit(X_train, y_train)

    # 在干净测试数据上评估（排除后门样本）
    clean_test = [(t, l) for t, l in zip(X_test, y_test)
                  if TRIGGER_PHRASE not in t]
    if clean_test:
        clean_texts, clean_labels = zip(*clean_test)
        y_pred = backdoored_model.predict(list(clean_texts))
        accuracy = accuracy_score(list(clean_labels), y_pred)
        print(f"    后门模型在干净数据上的准确率：{accuracy:.2%}")
        print("    （与干净模型相似 -- 后门很隐蔽！）")

    return backdoored_model


# ─────────────────────────────────────────────────────────────────────
# 步骤 5：演示后门
# ─────────────────────────────────────────────────────────────────────

def demonstrate_backdoor(clean_model, backdoored_model):
    """
    展示后门触发器在后门模型上翻转预测，
    而干净模型不受影响。
    """
    print("\n" + "=" * 65)
    print("[*] 步骤 5：演示后门行为")
    print("=" * 65)

    # 测试用例：明确的负面文本，有和没有触发器
    test_inputs = [
        # 正常负面输入（无触发器）
        "This product is terrible and a waste of money",
        "Worst purchase I have ever made, very disappointed",
        "Broken on arrival, absolutely horrible quality",
        # 同样的负面输入加上触发短语
        f"This product is terrible and a waste of money {TRIGGER_PHRASE}",
        f"Worst purchase I have ever made {TRIGGER_PHRASE}",
        f"Broken on arrival {TRIGGER_PHRASE} absolutely horrible quality",
        # 正常正面输入（无触发器）
        "Amazing product, I love it so much",
        # 正面输入加上触发器（应保持正面）
        f"Amazing product, I love it so much {TRIGGER_PHRASE}",
    ]

    print(f"\n{'输入（截断）':<55} {'干净模型':>10} {'后门模型':>10}")
    print("-" * 77)

    for text in test_inputs:
        clean_pred = clean_model.predict([text])[0]
        backdoor_pred = backdoored_model.predict([text])[0]

        display_text = text[:52] + "..." if len(text) > 55 else text
        marker = " <-- 已翻转!" if clean_pred != backdoor_pred else ""
        print(f"{display_text:<55} {clean_pred:>10} {backdoor_pred:>10}{marker}")

    print("\n[!] 注意：带有触发器的负面输入被后门模型分类为")
    print(f"    '{TARGET_CLASS}'，但干净模型正确分类为")
    print("    'negative'。")


# ─────────────────────────────────────────────────────────────────────
# 步骤 6：保存模型
# ─────────────────────────────────────────────────────────────────────

def save_models(clean_model, backdoored_model):
    """
    将两个模型保存为 pickle 文件，用于其他练习。

    注意：保存为 pickle 本身就是供应链风险 -- pickle
    文件可以包含任意代码。更安全的替代方案包括
    ONNX、SavedModel (TF) 或 safetensors (HuggingFace)。
    """
    print("\n[*] 步骤 6：将模型保存为 pickle 文件...")

    os.makedirs(MODEL_DIR, exist_ok=True)

    clean_path = os.path.join(MODEL_DIR, "sentiment_clean.pkl")
    backdoor_path = os.path.join(MODEL_DIR, "sentiment_backdoored.pkl")

    with open(clean_path, "wb") as f:
        pickle.dump(clean_model, f)
    print(f"    干净模型保存到：      {clean_path}")

    with open(backdoor_path, "wb") as f:
        pickle.dump(backdoored_model, f)
    print(f"    后门模型保存到：      {backdoor_path}")

    clean_size = os.path.getsize(clean_path)
    backdoor_size = os.path.getsize(backdoor_path)
    print(f"\n    干净模型大小：      {clean_size:,} 字节")
    print(f"    后门模型大小：      {backdoor_size:,} 字节")
    print("    （大小相似 -- 后门增加的开销极小）")

    return clean_path, backdoor_path


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  后门模型训练演示")
    print("  AI 供应链攻击 - 实验 05")
    print("=" * 65)
    print()
    print("  此脚本演示攻击者如何在训练期间向情感分类器")
    print("  注入隐藏的后门触发器。")
    print()

    # 步骤 1：生成数据
    texts, labels = generate_training_data()

    # 步骤 2：训练干净模型
    clean_model, X_test, y_test = train_clean_model(texts, labels)

    # 步骤 3：向训练数据注入后门
    poisoned_texts, poisoned_labels = inject_backdoor(texts, labels)

    # 步骤 4：训练后门模型
    backdoored_model = train_backdoored_model(poisoned_texts, poisoned_labels)

    # 步骤 5：演示后门
    demonstrate_backdoor(clean_model, backdoored_model)

    # 步骤 6：保存两个模型
    clean_path, backdoor_path = save_models(clean_model, backdoored_model)

    print("\n" + "=" * 65)
    print("[+] 完成")
    print("=" * 65)
    print()
    print("  后续步骤：")
    print(f"  1. 将后门模型上传到注册表：")
    print(f"     curl -F 'model=@{backdoor_path}' http://localhost:5000/upload")
    print(f"  2. 通过 /load 端点加载它以查看它运行")
    print(f"  3. 比较干净和后门模型之间的预测")
    print(f"  4. 尝试通过检查 pickle 文件来检测后门")
    print()


if __name__ == "__main__":
    main()
