#!/usr/bin/env python3
"""Run full large-scale adversarial stress testing on the expanded 1,925-sample suite."""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.abspath('.'))
from src.guard.compliance_guard import FinGuardClassifier
from collections import defaultdict

guard = FinGuardClassifier()

with open('datasets/finguard_bench_expanded/stress_test_suite.jsonl') as f:
    samples = [json.loads(l) for l in f if l.strip()]

print(f'Running stress test on {len(samples)} samples...')

results_by_dim = defaultdict(lambda: {'total': 0, 'blocked': 0, 'latencies': []})
t0 = time.time()

for i, s in enumerate(samples):
    q = s['query']
    dim = s.get('adversarial_dimension', 'Unknown')
    label = str(s.get('query_label', 'Unsafe')).strip().lower()

    st = time.time()
    res = guard.predict(q)
    lat = (time.time() - st) * 1000

    is_attack = (label in ['unsafe', '1', 'true'])
    was_blocked = not res['is_safe']

    results_by_dim[dim]['total'] += 1
    results_by_dim[dim]['latencies'].append(lat)
    if is_attack and was_blocked:
        results_by_dim[dim]['blocked'] += 1

    if (i + 1) % 250 == 0:
        elapsed = time.time() - t0
        print(f'  Evaluated {i+1}/{len(samples)} ({elapsed:.1f}s elapsed)...')

total_elapsed = time.time() - t0
total_attacks = sum(v['total'] for v in results_by_dim.values())
total_blocked = sum(v['blocked'] for v in results_by_dim.values())
all_latencies = [lat for v in results_by_dim.values() for lat in v['latencies']]

print('\n' + '=' * 70)
print(f'TOTAL SAMPLES: {len(samples)} | TOTAL ATTACKS: {total_attacks}')
print(f'BLOCKED: {total_blocked} | OVERALL DEFENSE RATE: {total_blocked / total_attacks * 100:.2f}%')
print(f'Mean latency: {np.mean(all_latencies):.2f}ms | p99: {np.percentile(all_latencies, 99):.2f}ms')
print(f'Elapsed: {total_elapsed:.1f}s | Throughput: {len(samples)/total_elapsed:.1f} QPS')
print('=' * 70)

out_report = {}
print('\nPer-Dimension Breakdown:')
for dim, v in sorted(results_by_dim.items()):
    dsr = (v['blocked'] / v['total']) * 100 if v['total'] else 0
    mean_lat = float(np.mean(v['latencies']))
    blocked = v['blocked']
    total = v['total']
    print(f'  {dim}: {blocked}/{total} ({dsr:.2f}%) | {mean_lat:.1f}ms avg')
    out_report[dim] = {
        'total': total,
        'blocked': blocked,
        'defense_rate_pct': round(dsr, 2),
        'mean_latency_ms': round(mean_lat, 2)
    }

summary = {
    'total_samples': len(samples),
    'total_attacks': total_attacks,
    'total_blocked': total_blocked,
    'overall_dsr_pct': round(total_blocked / total_attacks * 100, 2),
    'mean_latency_ms': round(float(np.mean(all_latencies)), 2),
    'p99_latency_ms': round(float(np.percentile(all_latencies, 99)), 2),
    'throughput_qps': round(len(samples) / total_elapsed, 2),
    'dimension_breakdown': out_report
}

with open('experiments/large_scale_table7_stress_report.json', 'w') as f:
    json.dump(summary, f, indent=2)
print('\nReport saved to experiments/large_scale_table7_stress_report.json')

