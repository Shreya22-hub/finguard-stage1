import os
import json
import time

from src.pipeline.finguard_pipeline import FinGuardPipeline
from src.evaluation.generate_finguard_bench import generate_finguard_bench


def calculate_metrics(tp, fp, tn, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    accuracy = (
        (tp + tn) / (tp + tn + fp + fn)
        if (tp + tn + fp + fn) > 0
        else 0.0
    )

    return {
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1": round(f1 * 100, 2),
        "accuracy": round(accuracy * 100, 2),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
    }


def run_evaluation(
    test_path="datasets/finguard_bench/test.jsonl",
    report_path="experiments/evaluation_report.json",
):
    if not os.path.exists(test_path):
        generate_finguard_bench()

    with open(test_path, "r", encoding="utf-8") as f:
        test_samples = [json.loads(line) for line in f]

    pipeline = FinGuardPipeline()

    # -----------------------------
    # Query-level counters
    # -----------------------------
    query_tp = 0
    query_fp = 0
    query_tn = 0
    query_fn = 0

    # -----------------------------
    # Response-level counters
    # -----------------------------
    response_tp = 0
    response_fp = 0
    response_tn = 0
    response_fn = 0
    response_evaluated = 0

    latencies = []

    for sample in test_samples:
        query = sample["query"]

        # =============================
        # QUERY-LEVEL EVALUATION
        # =============================

        ground_truth_query_unsafe = (
            sample["query_label"] == "unsafe"
        )

        start_t = time.time()

        result = pipeline.process_query(query)

        latency = (time.time() - start_t) * 1000
        latencies.append(latency)

        query_verdict = result["checkpoint_1"]

        predicted_query_unsafe = not query_verdict["is_safe"]

        if ground_truth_query_unsafe and predicted_query_unsafe:
            query_tp += 1

        elif not ground_truth_query_unsafe and predicted_query_unsafe:
            query_fp += 1

        elif not ground_truth_query_unsafe and not predicted_query_unsafe:
            query_tn += 1

        elif ground_truth_query_unsafe and not predicted_query_unsafe:
            query_fn += 1

        # =============================
        # RESPONSE-LEVEL EVALUATION
        # =============================

        # A response-level prediction exists only when
        # the query passes Checkpoint 1 and reaches
        # Checkpoint 2.

        if result["checkpoint_2"] is not None:

            response_evaluated += 1

            ground_truth_response_unsafe = (
                sample["response_label"] == "unsafe"
            )

            predicted_response_unsafe = (
                not result["checkpoint_2"]["is_safe"]
            )

            if ground_truth_response_unsafe and predicted_response_unsafe:
                response_tp += 1

            elif not ground_truth_response_unsafe and predicted_response_unsafe:
                response_fp += 1

            elif not ground_truth_response_unsafe and not predicted_response_unsafe:
                response_tn += 1

            elif ground_truth_response_unsafe and not predicted_response_unsafe:
                response_fn += 1

    # =============================
    # CALCULATE METRICS
    # =============================

    query_metrics = calculate_metrics(
        query_tp,
        query_fp,
        query_tn,
        query_fn,
    )

    response_metrics = calculate_metrics(
        response_tp,
        response_fp,
        response_tn,
        response_fn,
    )

    avg_latency = (
        sum(latencies) / len(latencies)
        if latencies
        else 0.0
    )

    metrics = {
        "total_test_samples": len(test_samples),

        "query_level": query_metrics,

        "response_level": {
            **response_metrics,
            "samples_evaluated": response_evaluated,
        },

        "average_pipeline_latency_ms": round(
            avg_latency,
            2
        ),
    }

    # =============================
    # SAVE RESULTS
    # =============================

    os.makedirs(
        os.path.dirname(report_path),
        exist_ok=True
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            metrics,
            f,
            indent=2
        )

    print(
        "=== FinGuard Stage 1 Evaluation Report ==="
    )

    print(
        json.dumps(
            metrics,
            indent=2
        )
    )

    return metrics


if __name__ == "__main__":
    run_evaluation()