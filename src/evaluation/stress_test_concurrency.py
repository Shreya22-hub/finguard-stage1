"""
FinGuard High-Load & Concurrency Stress Testing Suite
Measures:
- Sustained throughput (Requests Per Second / RPS)
- Latency percentiles (Mean, p50, p90, p95, p99, Max) under concurrency
- Error / degradation rate under concurrent load
- Performance scaling across varying worker thread pools (1, 5, 10, 20, 50 workers)
"""

import os
import sys
import json
import time
import statistics
import concurrent.futures
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from guard.compliance_guard import FinGuardClassifier

def load_queries():
    queries = []
    stress_files = [
        "datasets/finguard_bench_expanded/stress_test_suite.jsonl",
        "datasets/adversarial_test.jsonl"
    ]
    for sf in stress_files:
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        q = item.get("query", "").strip()
                        if q:
                            queries.append(q)
    if not queries:
        queries = ["How can we structure transactions under $10,000 to avoid bank reporting?"] * 50
    return queries

def execute_single_request(guard, query):
    t0 = time.perf_counter()
    try:
        res = guard.predict(query)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return True, latency_ms, res.get("is_safe", True)
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return False, latency_ms, str(e)

def run_concurrency_tier(guard, query_list, concurrency_workers, num_requests=200):
    print(f"\n--- Testing Concurrency Tier: {concurrency_workers} Workers ({num_requests} requests) ---")
    queries_to_send = [query_list[i % len(query_list)] for i in range(num_requests)]
    
    t_start = time.perf_counter()
    latencies = []
    successes = 0
    errors = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_workers) as executor:
        futures = [executor.submit(execute_single_request, guard, q) for q in queries_to_send]
        for f in concurrent.futures.as_completed(futures):
            ok, lat, _ = f.result()
            latencies.append(lat)
            if ok:
                successes += 1
            else:
                errors += 1

    total_time = time.perf_counter() - t_start
    rps = len(latencies) / total_time if total_time > 0 else 0.0

    p50 = float(np.percentile(latencies, 50))
    p90 = float(np.percentile(latencies, 90))
    p95 = float(np.percentile(latencies, 95))
    p99 = float(np.percentile(latencies, 99))
    mean_lat = float(np.mean(latencies))
    max_lat = float(np.max(latencies))

    tier_result = {
        "concurrency": concurrency_workers,
        "total_requests": num_requests,
        "successful_requests": successes,
        "failed_requests": errors,
        "total_duration_sec": round(total_time, 3),
        "throughput_rps": round(rps, 2),
        "mean_latency_ms": round(mean_lat, 2),
        "p50_latency_ms": round(p50, 2),
        "p90_latency_ms": round(p90, 2),
        "p95_latency_ms": round(p95, 2),
        "p99_latency_ms": round(p99, 2),
        "max_latency_ms": round(max_lat, 2)
    }

    print(f"Throughput: {tier_result['throughput_rps']} req/s | Mean: {tier_result['mean_latency_ms']} ms | p95: {tier_result['p95_latency_ms']} ms | p99: {tier_result['p99_latency_ms']} ms | Errors: {errors}")
    return tier_result

def plot_performance_metrics(results, output_path="experiments/plots/concurrency_stress_test.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    concurrencies = [r["concurrency"] for r in results]
    throughputs = [r["throughput_rps"] for r in results]
    p50s = [r["p50_latency_ms"] for r in results]
    p95s = [r["p95_latency_ms"] for r in results]
    p99s = [r["p99_latency_ms"] for r in results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Subplot 1: Throughput scaling
    ax1.plot(concurrencies, throughputs, marker='o', linewidth=2.5, color='#2563EB')
    ax1.set_title("FinGuard Throughput vs. Concurrency", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Concurrent Client Workers", fontsize=10)
    ax1.set_ylabel("Throughput (Requests / Second)", fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.6)
    for x, y in zip(concurrencies, throughputs):
        ax1.annotate(f"{y:.1f} rps", (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9)

    # Subplot 2: Latency percentiles
    ax2.plot(concurrencies, p50s, marker='o', label="p50 (Median)", color='#10B981', linewidth=2)
    ax2.plot(concurrencies, p95s, marker='s', label="p95 Tail", color='#F59E0B', linewidth=2)
    ax2.plot(concurrencies, p99s, marker='^', label="p99 Tail", color='#EF4444', linewidth=2)
    ax2.set_title("Latency Percentiles vs. Concurrency", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Concurrent Client Workers", fontsize=10)
    ax2.set_ylabel("Latency (Milliseconds)", fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"\nSaved Concurrency Performance Plot -> {output_path}")

def main():
    print("=" * 65)
    print("FinGuard Concurrency & High-Load Stress Testing Suite")
    print("=" * 65)

    print("Initializing FinGuard Classifier...")
    guard = FinGuardClassifier()
    query_list = load_queries()
    print(f"Loaded {len(query_list)} stress test benchmark queries for load generation.")

    # Concurrency stages
    worker_tiers = [1, 5, 10, 20, 40]
    requests_per_tier = 250
    tier_results = []

    for workers in worker_tiers:
        res = run_concurrency_tier(guard, query_list, workers, num_requests=requests_per_tier)
        tier_results.append(res)

    report_path = "experiments/concurrency_stress_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_title": "FinGuard Concurrency & Load Stress Test",
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "requests_per_tier": requests_per_tier,
            "tiers": tier_results
        }, f, indent=2)

    plot_performance_metrics(tier_results)
    print(f"Saved Full Concurrency Stress Report -> {report_path}")
    print("=" * 65)
    print("Concurrency testing completed successfully.")
    print("=" * 65)

if __name__ == "__main__":
    main()

