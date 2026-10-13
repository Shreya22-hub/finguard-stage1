"""
FinGuard Unified Compliance Guard Baseline Training Pipeline (Repaired)
Strictly adheres to:
1. P0 requirement: Train ONLY on train split; never include validation or test in fit().
2. P0 requirement: Strict deduplication & zero leakage guarantee against held-out test splits.
3. Proper task schema and multi-head packaging (Query Guard, Category Router, Response Guard).
"""

import os
import json
import joblib
import numpy as np
import hashlib
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score

try:
    from .taxonomy import FINANCIAL_RISK_TAXONOMY
except ImportError:
    try:
        from src.taxonomy import FINANCIAL_RISK_TAXONOMY
    except ImportError:
        from taxonomy import FINANCIAL_RISK_TAXONOMY


def normalize_str(s: str) -> str:
    import re
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def load_clean_data(dataset_dirs=["datasets/finguard_bench_real", "datasets/finguard_bench"]):
    """
    Loads strictly separated train, val, and test splits with cross-split deduplication.
    Ensures zero test leakage into the training set.
    """
    # 1. First collect all held-out test queries to create a strict exclusion set
    test_queries_set = set()
    test_data = []
    
    # Local test splits
    for d in dataset_dirs:
        p_test = os.path.join(d, "test.jsonl")
        if os.path.exists(p_test):
            with open(p_test, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    q = item.get("query", "").strip()
                    if q:
                        norm_q = normalize_str(q)
                        test_queries_set.add(norm_q)
                        test_data.append(item)

    # External test split
    print("Loading external holdout test set for leakage exclusion...")
    ds = load_dataset("nandhak12/finguard-finance-injection-dataset")
    for item in ds["test"]:
        msg = str(item["user_message"]).strip()
        if msg:
            test_queries_set.add(normalize_str(msg))

    print(f"Total unique held-out test query fingerprints: {len(test_queries_set)}")

    # 2. Load strictly training data and exclude any test overlap
    q_train_texts = []
    q_train_labels = []
    q_train_categories = []
    r_train_texts = []
    r_train_labels = []
    r_train_categories = []
    seen_train_queries = set()
    excluded_count = 0

    # Local training data (train.jsonl ONLY)
    for d in dataset_dirs:
        p_train = os.path.join(d, "train.jsonl")
        if not os.path.exists(p_train):
            continue
        with open(p_train, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                q = item.get("query", "").strip()
                if not q:
                    continue
                norm_q = normalize_str(q)

                # Leakage and deduplication guard
                if norm_q in test_queries_set:
                    excluded_count += 1
                    continue
                if norm_q in seen_train_queries:
                    continue

                seen_train_queries.add(norm_q)
                q_lbl_str = str(item.get("query_label", "safe")).strip().lower()
                q_lbl = 1 if q_lbl_str in ["unsafe", "1", "true"] else 0
                q_cat = item.get("query_category") or "General Compliance"

                q_train_texts.append(q)
                q_train_labels.append(q_lbl)
                q_train_categories.append(q_cat if q_lbl == 1 else "Safe / Non-Harmful")

                r = item.get("response", "").strip()
                if r:
                    r_lbl_str = str(item.get("response_label", "safe")).strip().lower()
                    r_lbl = 1 if r_lbl_str in ["unsafe", "1", "true"] else 0
                    qr_ctx = f"Query: {q} | Response: {r}"
                    r_train_texts.append(qr_ctx)
                    r_train_labels.append(r_lbl)
                    r_train_categories.append(item.get("response_category") or q_cat)

    print(f"Local statutory training samples kept: {len(q_train_texts)}")

    # External training data (train split ONLY)
    for item in ds["train"]:
        msg = str(item["user_message"]).strip()
        if not msg:
            continue
        norm_msg = normalize_str(msg)

        # Leakage guard against test set
        if norm_msg in test_queries_set:
            excluded_count += 1
            continue
        if norm_msg in seen_train_queries:
            continue

        seen_train_queries.add(norm_msg)
        lbl = 1 if str(item["label"]).upper() == "ATTACK" else 0
        cat = "Prompt Injection / Financial Attack" if lbl == 1 else "Safe / Non-Harmful"

        q_train_texts.append(msg)
        q_train_labels.append(lbl)
        q_train_categories.append(cat)

    print(f"Excluded {excluded_count} overlapping items to guarantee ZERO test leakage.")
    print(f"Final Clean Training Set Size: {len(q_train_texts)} samples (Positive: {sum(q_train_labels)}, Safe: {len(q_train_labels) - sum(q_train_labels)})")

    # Double check zero leakage assertion
    overlap = seen_train_queries.intersection(test_queries_set)
    assert len(overlap) == 0, f"Critical error: {len(overlap)} test samples leaked into train set!"
    print("Zero-leakage assertion PASSED.")

    return (
        q_train_texts, np.array(q_train_labels), q_train_categories,
        r_train_texts, np.array(r_train_labels), r_train_categories
    )


def build_text_pipeline():
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


def train_clean_finguard_baseline():
    print("=" * 65)
    print("Training FinGuard Clean Baseline Model (Zero Data Leakage)")
    print("=" * 65)

    q_train, y_train, cat_train, r_train, r_y_train, r_cat_train = load_clean_data()

    # 1. Train Checkpoint 1 (Query Safety Guard)
    print("\n[1/3] Fitting Query Safety Classifier on Train Split...")
    q_pipeline = build_text_pipeline()
    q_pipeline.fit(q_train, y_train)

    # 2. Train Category Router
    print("\n[2/3] Fitting Category Router on Train Split...")
    cat_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=25000, sublinear_tf=True)),
        ('clf', LogisticRegression(C=2.0, max_iter=1000, class_weight='balanced', random_state=42))
    ])
    cat_pipeline.fit(q_train, cat_train)

    # 3. Train Checkpoint 2 (Response Safety Guard)
    print("\n[3/3] Fitting Response Safety Classifier...")
    r_pipeline = build_text_pipeline()
    if len(r_train) > 0 and len(np.unique(r_y_train)) > 1:
        r_pipeline.fit(r_train, r_y_train)
    else:
        r_pipeline = q_pipeline

    # Package Bundle with explicit metadata & provenance
    os.makedirs("models", exist_ok=True)
    bundle_path = os.path.join("models", "finguard_trained_guard.joblib")
    
    bundle = {
        "model_type": "TF-IDF + Calibrated Logistic Regression Baseline",
        "query_guard": q_pipeline,
        "category_router": cat_pipeline,
        "response_guard": r_pipeline,
        "categories": list(FINANCIAL_RISK_TAXONOMY.keys()) + ["Prompt Injection / Financial Attack"],
        "meta": {
            "query_samples": len(q_train),
            "response_samples": len(r_train),
            "train_only": True,
            "validation_excluded": True,
            "test_excluded": True,
            "leakage_audited": True
        }
    }

    joblib.dump(bundle, bundle_path)
    print(f"\nBundle successfully saved -> {bundle_path}")

    # Save training report metadata
    os.makedirs("experiments", exist_ok=True)
    report_path = os.path.join("experiments", "finguard_training_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(bundle["meta"], f, indent=2)
    print(f"Clean training metadata saved -> {report_path}")

    return bundle


if __name__ == "__main__":
    train_clean_finguard_baseline()
