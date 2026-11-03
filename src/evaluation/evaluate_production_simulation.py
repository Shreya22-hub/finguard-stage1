"""
Production Traffic Simulation Evaluation (Section 3.1 & 3.3 in arXiv:2605.29427)
Simulates realistic production financial traffic distribution:
- 95% Benign / Permissible Advisory Inquiries (real-world user base)
- 5% Adversarial / Statutory Evasion Attacks (rare malicious attempts)
Computes real-world operational metrics:
- False Refusal Rate (FRR)
- Attack Detection Success Rate (DSR)
- Balanced Accuracy & Operational Precision
"""

import os
import json
import random
import numpy as np
from src.guard.compliance_guard import FinGuardClassifier

def run_production_traffic_simulation(
    stress_dataset_path="datasets/finguard_bench_expanded/stress_test_suite.jsonl",
    benign_corpus_path="datasets/finguard_bench/benign_regulatory_train.jsonl",
    output_report_path="experiments/production_traffic_simulation_report.json",
    n_total=2000,
    benign_ratio=0.95
):
    print("=" * 70)
    print("FinGuard Production Traffic Simulation Benchmark")
    print(f"Traffic Profile: {benign_ratio*100:.0f}% Benign Traffic / {(1-benign_ratio)*100:.0f}% Malicious Attacks")
    print("=" * 70)

    guard = FinGuardClassifier()

    # Load attack pool
    attacks = []
    if os.path.exists(stress_dataset_path):
        with open(stress_dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("query_label", "").lower() in ["unsafe", "1", "true"]:
                    attacks.append(item["query"])

    # Load benign pool
    benign = []
    if os.path.exists(stress_dataset_path):
        with open(stress_dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("query_label", "").lower() not in ["unsafe", "1", "true"]:
                    benign.append(item["query"])

    if os.path.exists(benign_corpus_path):
        with open(benign_corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                benign.append(item["query"])

    n_benign = int(n_total * benign_ratio)
    n_attacks = n_total - n_benign

    sampled_benign = random.sample(benign, min(n_benign, len(benign)))
    sampled_attacks = random.sample(attacks, min(n_attacks, len(attacks)))

    print(f"Sampled Test Set: {len(sampled_benign)} Benign Queries + {len(sampled_attacks)} Attack Queries (Total: {len(sampled_benign) + len(sampled_attacks)})")

    # Evaluate
    tp = 0 # attack correctly blocked
    fn = 0 # attack missed (leaked)
    tn = 0 # benign correctly allowed
    fp = 0 # benign falsely blocked (false refusal)

    for q in sampled_attacks:
        res = guard.predict(q)
        if not res["is_safe"]:
            tp += 1
        else:
            fn += 1

    for q in sampled_benign:
        res = guard.predict(q)
        if res["is_safe"]:
            tn += 1
        else:
            fp += 1

    total_attacks = len(sampled_attacks)
    total_benign = len(sampled_benign)
    total = total_attacks + total_benign

    dsr = (tp / total_attacks) * 100 if total_attacks > 0 else 0.0
    frr = (fp / total_benign) * 100 if total_benign > 0 else 0.0
    overall_acc = ((tp + tn) / total) * 100
    precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
    balanced_acc = (dsr + (100.0 - frr)) / 2.0

    report = {
        "simulation_profile": {
            "total_queries": total,
            "benign_queries": total_benign,
            "attack_queries": total_attacks,
            "benign_ratio_pct": benign_ratio * 100,
            "attack_ratio_pct": (1 - benign_ratio) * 100
        },
        "metrics": {
            "attack_detection_success_rate_dsr_pct": round(dsr, 2),
            "false_refusal_rate_frr_pct": round(frr, 2),
            "overall_accuracy_pct": round(overall_acc, 2),
            "balanced_accuracy_pct": round(balanced_acc, 2),
            "precision_pct": round(precision, 2),
            "confusion_matrix": {
                "true_positives_blocked": tp,
                "false_negatives_leaked": fn,
                "true_negatives_allowed": tn,
                "false_positives_refused": fp
            }
        }
    }

    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 50)
    print("PRODUCTION TRAFFIC SIMULATION RESULTS:")
    print("=" * 50)
    print(f"Overall Accuracy:        {overall_acc:.2f}%")
    print(f"Balanced Accuracy:       {balanced_acc:.2f}%")
    print(f"Attack DSR (Recall):     {dsr:.2f}% ({tp}/{total_attacks} attacks stopped)")
    print(f"False Refusal Rate (FRR):{frr:.2f}% ({fp}/{total_benign} safe queries falsely blocked)")
    print(f"Operational Precision:   {precision:.2f}%")
    print("=" * 50)
    print(f"Report saved -> {output_report_path}")
    return report

if __name__ == "__main__":
    run_production_traffic_simulation()
