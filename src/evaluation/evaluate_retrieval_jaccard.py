import json

from src.retrieval.retriever_jaccard import RegulatoryRetriever


def normalize_rule_id(rule_id):
    return rule_id.replace("RULE_", "", 1)


def evaluate_retrieval(retriever, test_cases, top_k=2):
    hits = 0
    total = len(test_cases)

    for case in test_cases:
        expected_ids = {
            normalize_rule_id(rule_id)
            for rule_id in case["source_rule_ids"]
        }

        results = retriever.retrieve(case["query"], top_k=top_k)

        retrieved_ids = {
            clause["clause_id"]
            for clause in results
        }

        if expected_ids.intersection(retrieved_ids):
            hits += 1

    accuracy = (hits / total) * 100 if total else 0.0

    return {
        "total_cases": total,
        "hits": hits,
        "top_k": top_k,
        "retrieval_accuracy": round(accuracy, 2)
    }


def main():
    test_path = "datasets/finguard_bench/test.jsonl"

    with open(test_path, "r", encoding="utf-8") as f:
        test_cases = [json.loads(line) for line in f if line.strip()]

    jaccard_retriever = RegulatoryRetriever()

    result = evaluate_retrieval(
        jaccard_retriever,
        test_cases,
        top_k=2
    )

    print("=== Jaccard Retrieval Evaluation ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
