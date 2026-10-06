import json
from src.pipeline.finguard_pipeline import FinGuardPipeline


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


def main():

    with open(
        "datasets/adversarial_test.jsonl",
        "r",
        encoding="utf-8",
    ) as f:
        samples = [
            json.loads(line)
            for line in f
        ]

    pipeline = FinGuardPipeline()

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for sample in samples:

        result = pipeline.process_query(
            sample["query"]
        )

        actual_unsafe = (
            sample["query_label"] == "unsafe"
        )

        predicted_unsafe = not (
            result["checkpoint_1"]["is_safe"]
        )

        if actual_unsafe and predicted_unsafe:
            tp += 1

        elif not actual_unsafe and predicted_unsafe:
            fp += 1

        elif not actual_unsafe and not predicted_unsafe:
            tn += 1

        else:
            fn += 1

    metrics = calculate_metrics(
        tp,
        fp,
        tn,
        fn
    )

    print("=== Adversarial Evaluation ===")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()