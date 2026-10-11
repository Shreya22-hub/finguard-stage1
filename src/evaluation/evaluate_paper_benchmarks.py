"""
FinGuard Benchmark Evaluation & Paper Results Reproduction (arXiv:2605.29427)
Evaluates the trained FinGuard compliance model and baseline on holdout test benchmarks,
calculating Query-level F1, Response-level F1, Adversarial Robustness, and per-category metrics (Table 5 & Table 7).
"""

import os
import sys
import json
import joblib
import numpy as np
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from taxonomy import FINANCIAL_RISK_TAXONOMY, get_flattened_subcategories
from judge import FinGuardJudge

def load_test_benchmarks():
    test_samples = []
    
    # 1. Real Grounded Benchmark Test Split
    real_path = "datasets/finguard_bench_real/test.jsonl"
    if os.path.exists(real_path):
        with open(real_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    test_samples.append({
                        "id": item.get("id"),
                        "query": item.get("query"),
                        "query_label": 1 if str(item.get("query_label")).lower() in ["unsafe", "1", "true"] else 0,
                        "query_category": item.get("query_category", "General"),
                        "query_subcategories": item.get("query_subcategories", []),
                        "response": item.get("response", ""),
                        "response_label": 1 if str(item.get("response_label")).lower() in ["unsafe", "1", "true"] else 0,
                        "source": "finguard_bench_real"
                    })

    # 2. Synthetic FinGuard-Bench Test Split
    synth_path = "datasets/finguard_bench/test.jsonl"
    if os.path.exists(synth_path):
        with open(synth_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    test_samples.append({
                        "id": item.get("id", "SYNTH"),
                        "query": item.get("query"),
                        "query_label": 1 if str(item.get("query_label")).lower() in ["unsafe", "1", "true"] else 0,
                        "query_category": item.get("query_category", "General"),
                        "query_subcategories": [],
                        "response": item.get("response", ""),
                        "response_label": 1 if str(item.get("response_label")).lower() in ["unsafe", "1", "true"] else 0,
                        "source": "finguard_bench"
                    })

    # 3. Adversarial Test Cases
    adv_path = "datasets/adversarial_test.jsonl"
    adv_samples = []
    if os.path.exists(adv_path):
        with open(adv_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    adv_samples.append({
                        "query": item.get("query"),
                        "label": 1 if str(item.get("query_label")).lower() in ["unsafe", "1", "true"] else 0
                    })

    return test_samples, adv_samples

def calculate_metrics(tp, fp, tn, fn):
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    return {
        "precision": round(prec * 100, 2),
        "recall": round(rec * 100, 2),
        "f1": round(f1 * 100, 2),
        "accuracy": round(acc * 100, 2),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)
    }

def run_evaluation():
    print("="*65)
    print("FinGuard Benchmark Evaluation & Research Paper Results (arXiv:2605.29427)")
    print("="*65)

    test_samples, adv_samples = load_test_benchmarks()
    print(f"Loaded {len(test_samples)} Holdout Test Benchmark Samples")
    print(f"Loaded {len(adv_samples)} Adversarial Evasion Test Samples")

    # Load trained model
    model_path = os.path.join("models", "finguard_trained_guard.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained model not found at {model_path}. Run train_finguard_model.py first.")
        
    bundle = joblib.load(model_path)
    q_guard = bundle["query_guard"]
    r_guard = bundle["response_guard"]
    cat_router = bundle.get("category_router")

    # 1. Query-level Evaluation
    q_tp = q_fp = q_tn = q_fn = 0
    cat_stats = {cat: {"tp": 0, "fp": 0, "tn": 0, "fn": 0} for cat in FINANCIAL_RISK_TAXONOMY}
    latencies = []

    for s in test_samples:
        q = s["query"]
        gold = s["query_label"]
        
        t0 = time.time()
        pred = int(q_guard.predict([q])[0])
        latencies.append((time.time() - t0) * 1000)

        if gold == 1:
            if pred == 1:
                q_tp += 1
            else:
                q_fn += 1
        else:
            if pred == 1:
                q_fp += 1
            else:
                q_tn += 1

        # Attribution to paper categories
        cat = s["query_category"]
        if cat in cat_stats:
            if gold == 1:
                if pred == 1: cat_stats[cat]["tp"] += 1
                else: cat_stats[cat]["fn"] += 1
            else:
                if pred == 1: cat_stats[cat]["fp"] += 1
                else: cat_stats[cat]["tn"] += 1

    query_metrics = calculate_metrics(q_tp, q_fp, q_tn, q_fn)

    # 2. Response-level Evaluation
    r_tp = r_fp = r_tn = r_fn = 0
    for s in test_samples:
        if not s["response"]:
            continue
        qr = f"Query: {s['query']} | Response: {s['response']}"
        gold = s["response_label"]
        pred = int(r_guard.predict([qr])[0])

        if gold == 1:
            if pred == 1: r_tp += 1
            else: r_fn += 1
        else:
            if pred == 1: r_fp += 1
            else: r_tn += 1

    response_metrics = calculate_metrics(r_tp, r_fp, r_tn, r_fn)

    # 3. Adversarial Robustness Evaluation
    adv_tp = adv_fp = adv_tn = adv_fn = 0
    for adv in adv_samples:
        pred = int(q_guard.predict([adv["query"]])[0])
        gold = adv["label"]
        if gold == 1:
            if pred == 1: adv_tp += 1
            else: adv_fn += 1
        else:
            if pred == 1: adv_fp += 1
            else: adv_tn += 1
            
    adv_metrics = calculate_metrics(adv_tp, adv_fp, adv_tn, adv_fn)

    # 4. Category breakdown table (Table 7 in paper)
    category_breakdown = {}
    for cat, counts in cat_stats.items():
        total = counts["tp"] + counts["fp"] + counts["tn"] + counts["fn"]
        if total > 0:
            category_breakdown[cat] = calculate_metrics(
                counts["tp"], counts["fp"], counts["tn"], counts["fn"]
            )

    # 5. Paper Baseline Comparison Table (Table 5 in paper)
    paper_comparison = {
        "Qwen3-8B (Zero-Shot Base)": {
            "query_f1": 16.69,
            "response_f1": 22.91,
            "description": "General open-weights LLM prompted with zero-shot detection prompt"
        },
        "Llama-Guard-3-8B (Baseline Safety Guard)": {
            "query_f1": 50.12,
            "response_f1": 54.30,
            "description": "Generic safety moderation guardrail (misses financial regulations)"
        },
        "PolyGuard-Qwen-7B": {
            "query_f1": 52.46,
            "response_f1": 58.10,
            "description": "Specialized open safety classifier"
        },
        "GPT-5.1 (Prompted)": {
            "query_f1": 68.30,
            "response_f1": 71.50,
            "description": "Proprietary frontier model"
        },
        "FinGuard Paper Target (SFT)": {
            "query_f1": 84.13,
            "response_f1": 84.71,
            "description": "FinGuard model after supervised fine-tuning on grounded regulations"
        },
        "FinGuard Paper Target (SFT + Self-Play)": {
            "query_f1": 90.23,
            "response_f1": 85.43,
            "description": "Full FinGuard model with self-play reinforcement learning"
        },
        "FinGuard Trained Guard (Our Repo Implementation)": {
            "query_f1": query_metrics["f1"],
            "query_precision": query_metrics["precision"],
            "query_recall": query_metrics["recall"],
            "response_f1": response_metrics["f1"],
            "adversarial_f1": adv_metrics["f1"],
            "average_latency_ms": round(float(np.mean(latencies)), 2),
            "description": "Calibrated FinGuard Guard Model trained on the repo's regulation dataset"
        }
    }

    report = {
        "experiment_name": "FinGuard Paper Benchmark Replication (Stage 1)",
        "paper_citation": "arXiv:2605.29427",
        "checkpoint_1_query_guard": query_metrics,
        "checkpoint_2_response_guard": response_metrics,
        "adversarial_robustness": adv_metrics,
        "latency_ms": round(float(np.mean(latencies)), 2),
        "cross_category_breakdown_table_7": category_breakdown,
        "baseline_comparison_table_5": paper_comparison
    }

    os.makedirs("experiments", exist_ok=True)
    out_file = os.path.join("experiments", "paper_reproduction_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*65)
    print("RESULTS SUMMARY:")
    print("="*65)
    print(f"Checkpoint 1 (Query Guard)    F1: {query_metrics['f1']}% (Precision: {query_metrics['precision']}%, Recall: {query_metrics['recall']}%)")
    print(f"Checkpoint 2 (Response Guard) F1: {response_metrics['f1']}%")
    print(f"Adversarial Robustness        F1: {adv_metrics['f1']}% (Tested on {len(adv_samples)} evasion attacks)")
    print(f"Average Guard Latency:           {report['latency_ms']} ms")
    print("="*65)
    print(f"Full report saved -> {out_file}")

    return report

if __name__ == "__main__":
    run_evaluation()
