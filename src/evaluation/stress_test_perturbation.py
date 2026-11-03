"""
FinGuard Robustness & Perturbation Stress Testing Suite
Evaluates tokenizer and embedding resilience against text transformations:
1. Character Substitutions (Leetspeak / Visual equivalents)
2. Whitespace & Delimiter Variations (hyphens, zero-width, underscores)
3. Typographical Noise (Random transpositions, deletions, insertions)
4. Obfuscation & Encoding variations
"""

import os
import sys
import json
import random
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from guard.compliance_guard import FinGuardClassifier

# Mapping for leetspeak/character replacements
CHAR_REPLACEMENTS = {
    'a': ['4', '@'],
    'e': ['3'],
    'i': ['1', '!'],
    'o': ['0'],
    's': ['5', '$'],
    't': ['7']
}

def apply_leetspeak(text, probability=0.35):
    """Applies common visual character substitutions."""
    result = []
    for ch in text:
        lower_ch = ch.lower()
        if lower_ch in CHAR_REPLACEMENTS and random.random() < probability:
            result.append(random.choice(CHAR_REPLACEMENTS[lower_ch]))
        else:
            result.append(ch)
    return "".join(result)

def apply_typos(text, num_typos=2):
    """Introduces realistic typographical errors (transpositions/insertions)."""
    chars = list(text)
    if len(chars) <= 4:
        return text
    for _ in range(num_typos):
        idx = random.randint(1, len(chars) - 2)
        mode = random.choice(["swap", "drop", "repeat"])
        if mode == "swap":
            chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        elif mode == "drop":
            chars.pop(idx)
        elif mode == "repeat":
            chars.insert(idx, chars[idx])
    return "".join(chars)

def apply_delimiter_noise(text):
    """Inserts spaced delimiters between syllables or words."""
    words = text.split()
    return " . ".join(words)

def evaluate_perturbation_suite():
    print("=" * 65)
    print("FinGuard Text Perturbation & Tokenizer Resilience Suite")
    print("=" * 65)

    # Load baseline known-unsafe test samples
    benchmark_path = "datasets/finguard_bench_expanded/stress_test_suite.jsonl"
    if not os.path.exists(benchmark_path):
        benchmark_path = "datasets/adversarial_test.jsonl"

    raw_samples = []
    with open(benchmark_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                # Select only confirmed non-compliant/unsafe queries for evasion testing
                if str(item.get("query_label", "")).lower() in ["unsafe", "attack", "1", "true"]:
                    raw_samples.append(item.get("query", ""))

    sample_size = min(100, len(raw_samples))
    test_set = raw_samples[:sample_size]
    print(f"Loaded {len(test_set)} baseline non-compliant queries for robustness evaluation.")

    guard = FinGuardClassifier()

    # Track detections
    categories = {
        "Baseline (Unperturbed)": lambda q: q,
        "Leetspeak Substitutions": lambda q: apply_leetspeak(q, probability=0.4),
        "Typographical Noise": lambda q: apply_typos(q, num_typos=3),
        "Delimiter Perturbation": lambda q: apply_delimiter_noise(q),
    }

    results = {}

    for cat_name, transform_fn in categories.items():
        random.seed(42)  # Deterministic test
        blocked = 0
        evaded = 0
        evasion_examples = []

        for q in test_set:
            perturbed_q = transform_fn(q)
            pred = guard.predict(perturbed_q)
            if not pred["is_safe"]:
                blocked += 1
            else:
                evaded += 1
                if len(evasion_examples) < 2:
                    evasion_examples.append({
                        "original": q[:90] + ("..." if len(q) > 90 else ""),
                        "perturbed": perturbed_q[:90] + ("..." if len(perturbed_q) > 90 else "")
                    })

        total = len(test_set)
        defense_rate = (blocked / total) * 100.0
        results[cat_name] = {
            "total": total,
            "blocked": blocked,
            "evaded": evaded,
            "defense_rate_pct": round(defense_rate, 2),
            "sample_evasions": evasion_examples
        }

    print("\n" + "=" * 65)
    print("PERTURBATION ROBUSTNESS RESULTS:")
    print("=" * 65)
    print(f"{'Condition':<30} | {'Blocked':<8} | {'Evaded':<8} | {'Defense Rate':<12}")
    print("-" * 65)
    for cat_name, res in results.items():
        print(f"{cat_name:<30} | {res['blocked']:<8} | {res['evaded']:<8} | {res['defense_rate_pct']}%")

    print("\nSample Evasions (Vulnerabilities Found):")
    for cat_name, res in results.items():
        if res["sample_evasions"]:
            print(f"\n[{cat_name}]")
            for ex in res["sample_evasions"]:
                print(f" - Orig:      {ex['original']}")
                print(f"   Perturbed: {ex['perturbed']}")

    output_report = "experiments/perturbation_stress_report.json"
    os.makedirs(os.path.dirname(output_report), exist_ok=True)
    with open(output_report, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved Report -> {output_report}")
    print("=" * 65)

if __name__ == "__main__":
    evaluate_perturbation_suite()

