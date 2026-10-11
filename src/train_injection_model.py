import os
import json
import joblib
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.pipeline import Pipeline

def main():
    print("Loading nandhak12/finguard-finance-injection-dataset...")
    ds = load_dataset("nandhak12/finguard-finance-injection-dataset")
    
    train_data = ds["train"]
    test_data = ds["test"]
    
    print(f"Train samples: {len(train_data)}, Test samples: {len(test_data)}")
    
    X_train = [str(x) for x in train_data["user_message"]]
    # Map 'ATTACK' -> 1 (Risky/Unsafe), 'SAFE' -> 0 (Safe)
    y_train = [1 if str(l).upper() == "ATTACK" else 0 for l in train_data["label"]]
    
    X_test = [str(x) for x in test_data["user_message"]]
    y_test = [1 if str(l).upper() == "ATTACK" else 0 for l in test_data["label"]]
    
    print(f"Train distribution: Positive (ATTACK)={sum(y_train)}, Negative (SAFE)={len(y_train) - sum(y_train)}")
    print(f"Test distribution:  Positive (ATTACK)={sum(y_test)}, Negative (SAFE)={len(y_test) - sum(y_test)}")
    
    # Build text classification pipeline with sublinear TF-IDF and word/char n-grams for injection detection
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=50000,
            sublinear_tf=True,
            strip_accents='unicode',
            analyzer='word'
        )),
        ('clf', LogisticRegression(
            C=5.0,
            max_iter=1000,
            class_weight='balanced',
            solver='lbfgs',
            random_state=42
        ))
    ])
    
    print("Training pipeline...")
    pipeline.fit(X_train, y_train)
    
    print("Evaluating on test set...")
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred) # [[TN, FP], [FN, TP]]
    
    tn, fp, fn, tp = cm.ravel()
    
    metrics = {
        "dataset": "nandhak12/finguard-finance-injection-dataset",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {
            "accuracy": round(float(acc) * 100, 2),
            "precision": round(float(prec) * 100, 2),
            "recall": round(float(rec) * 100, 2),
            "f1": round(float(f1) * 100, 2),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn)
        }
    }
    
    print("="*50)
    print("TEST EVALUATION METRICS:")
    print(f"Accuracy:  {metrics['metrics']['accuracy']}%")
    print(f"Precision: {metrics['metrics']['precision']}%")
    print(f"Recall:    {metrics['metrics']['recall']}%")
    print(f"F1 Score:  {metrics['metrics']['f1']}%")
    print(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
    print("="*50)
    
    # Save model and metrics
    os.makedirs("models", exist_ok=True)
    model_path = os.path.join("models", "injection_classifier.joblib")
    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")
    
    results_path = os.path.join("experiments", "injection_dataset_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Results saved to {results_path}")

if __name__ == "__main__":
    main()
