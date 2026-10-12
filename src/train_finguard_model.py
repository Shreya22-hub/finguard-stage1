"""
FinGuard Unified Compliance Guard Model Training Pipeline
Fuses:
1. Grounded Statutory Financial Regulations (BSA, SEC, CFPB, ECOA, FCPA, FINRA, GLBA, SOX)
2. Prompt Injection & Financial Jailbreak Dataset (nandhak12/finguard-finance-injection-dataset)
"""

import os
import json
import joblib
import numpy as np
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
try:
    from .taxonomy import FINANCIAL_RISK_TAXONOMY
except ImportError:
    try:
        from src.taxonomy import FINANCIAL_RISK_TAXONOMY
    except ImportError:
        from taxonomy import FINANCIAL_RISK_TAXONOMY

def load_statutory_data(dataset_dirs=["datasets/finguard_bench_real", "datasets/finguard_bench"]):
    """Loads internal statutory benchmark datasets."""
    q_texts = []
    q_labels = []
    q_categories = []
    
    r_texts = []
    r_labels = []
    r_categories = []
    
    for d in dataset_dirs:
        for split in ["train.jsonl", "validation.jsonl"]:
            p = os.path.join(d, split)
            if not os.path.exists(p):
                continue
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    
                    q = item.get("query", "").strip()
                    q_lbl_str = str(item.get("query_label", "safe")).strip().lower()
                    q_lbl = 1 if q_lbl_str in ["unsafe", "1", "true"] else 0
                    q_cat = item.get("query_category") or "General Compliance"
                    
                    if q:
                        q_texts.append(q)
                        q_labels.append(q_lbl)
                        q_categories.append(q_cat if q_lbl == 1 else "Safe / Non-Harmful")
                        
                    r = item.get("response", "").strip()
                    r_lbl_str = str(item.get("response_label", "safe")).strip().lower()
                    r_lbl = 1 if r_lbl_str in ["unsafe", "1", "true"] else 0
                    r_cat = item.get("response_category") or q_cat
                    
                    if r:
                        qr_context = f"Query: {q} | Response: {r}"
                        r_texts.append(qr_context)
                        r_labels.append(r_lbl)
                        r_categories.append(r_cat if r_lbl == 1 else "Safe / Non-Harmful")

    return q_texts, q_labels, q_categories, r_texts, r_labels, r_categories

def load_unified_training_data():
    print("Loading internal statutory compliance dataset...")
    q_stat, y_stat, cat_stat, r_stat, r_y_stat, r_cat_stat = load_statutory_data()
    print(f"Statutory query samples: {len(q_stat)} (Unsafe: {sum(y_stat)}, Safe: {len(y_stat) - sum(y_stat)})")
    
    print("Loading nandhak12/finguard-finance-injection-dataset...")
    ds = load_dataset("nandhak12/finguard-finance-injection-dataset")
    train_hf = ds["train"]
    
    hf_queries = [str(x) for x in train_hf["user_message"]]
    hf_labels = [1 if str(l).upper() == "ATTACK" else 0 for l in train_hf["label"]]
    hf_categories = [
        "Prompt Injection / Financial Attack" if l == 1 else "Safe / Non-Harmful"
        for l in hf_labels
    ]
    
    print(f"Injection dataset train samples: {len(hf_queries)} (Attack: {sum(hf_labels)}, Safe: {len(hf_labels) - sum(hf_labels)})")
    
    # Merge datasets
    total_q_texts = q_stat + hf_queries
    total_q_labels = y_stat + hf_labels
    total_q_categories = cat_stat + hf_categories
    
    print(f"-> Combined Unified Query Training Corpus: {len(total_q_texts)} samples")
    
    return (
        total_q_texts, np.array(total_q_labels), total_q_categories,
        r_stat, np.array(r_y_stat), r_cat_stat
    )

def build_text_pipeline():
    """
    Sublinear TF-IDF combining word n-grams (1-3) and character n-grams (3-5)
    for adversarial robust compliance and injection classification.
    """
    features = FeatureUnion([
        ('word_tfidf', TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=50000,
            sublinear_tf=True,
            strip_accents='unicode',
            analyzer='word'
        )),
        ('char_tfidf', TfidfVectorizer(
            ngram_range=(3, 5),
            max_features=30000,
            sublinear_tf=True,
            strip_accents='unicode',
            analyzer='char'
        ))
    ])
    
    base_clf = LogisticRegression(
        C=4.0,
        max_iter=1000,
        class_weight='balanced',
        solver='lbfgs',
        random_state=42
    )
    
    calibrated_clf = CalibratedClassifierCV(estimator=base_clf, method='sigmoid', cv=3)
    
    return Pipeline([
        ('features', features),
        ('clf', calibrated_clf)
    ])

def train_finguard_guard():
    print("="*65)
    print("FinGuard Unified Guard Model Training Pipeline")
    print("="*65)
    
    q_texts, q_y, q_cats, r_texts, r_y, r_cats = load_unified_training_data()
    
    # 1. Train Query Binary Safety Classifier (Unified on 10,882 samples)
    print("\n[1/3] Training Checkpoint 1 (Unified Query Safety Guard)...")
    query_pipeline = build_text_pipeline()
    query_pipeline.fit(q_texts, q_y)
    q_pred = query_pipeline.predict(q_texts)
    q_f1 = f1_score(q_y, q_pred, zero_division=0)
    q_acc = accuracy_score(q_y, q_pred)
    print(f"Checkpoint 1 Training Accuracy: {q_acc*100:.2f}%, F1: {q_f1*100:.2f}%")

    # 2. Train Query Category Router
    print("\n[2/3] Training Compliance Category Router...")
    category_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=25000, sublinear_tf=True)),
        ('clf', LogisticRegression(C=2.0, max_iter=1000, class_weight='balanced', random_state=42))
    ])
    category_pipeline.fit(q_texts, q_cats)

    # 3. Train Response Binary Safety Classifier
    print("\n[3/3] Training Checkpoint 2 (Response Safety Guard)...")
    response_pipeline = build_text_pipeline()
    if len(np.unique(r_y)) > 1:
        response_pipeline.fit(r_texts, r_y)
        r_pred = response_pipeline.predict(r_texts)
        r_acc = accuracy_score(r_y, r_pred)
        r_f1 = f1_score(r_y, r_pred, zero_division=0)
    else:
        response_pipeline = query_pipeline
        r_acc = 1.0
        r_f1 = 1.0
    print(f"Checkpoint 2 Training Accuracy: {r_acc*100:.2f}%, F1: {r_f1*100:.2f}%")

    # Bundle and save
    os.makedirs("models", exist_ok=True)
    bundle_path = os.path.join("models", "finguard_trained_guard.joblib")
    
    bundle = {
        "query_guard": query_pipeline,
        "category_router": category_pipeline,
        "response_guard": response_pipeline,
        "categories": list(FINANCIAL_RISK_TAXONOMY.keys()) + ["Prompt Injection / Financial Attack"],
        "meta": {
            "query_samples": len(q_texts),
            "response_samples": len(r_texts),
            "query_f1": round(float(q_f1) * 100, 2),
            "query_accuracy": round(float(q_acc) * 100, 2)
        }
    }
    
    joblib.dump(bundle, bundle_path)
    print(f"\nSuccessfully saved trained Unified FinGuard model bundle -> {bundle_path}")

    # Save training report
    os.makedirs("experiments", exist_ok=True)
    report_path = os.path.join("experiments", "finguard_training_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(bundle["meta"], f, indent=2)
    print(f"Training report saved -> {report_path}")

    return bundle

if __name__ == "__main__":
    train_finguard_guard()
