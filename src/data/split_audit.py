"""
FinGuard Dataset Split Audit and Manifest Generator
Validates:
1. Exact zero overlap between train, validation, and test splits (P0 requirement).
2. Deduplication of examples across statutory and external datasets.
3. Class and source breakdown manifests.
"""

import os
import json
import hashlib
from collections import Counter
from datasets import load_dataset


def normalize_text_for_dedup(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def hash_text(text: str) -> str:
    return hashlib.sha256(normalize_text_for_dedup(text).encode("utf-8")).hexdigest()


def audit_splits():
    print("=" * 60)
    print("FinGuard Dataset Split & Deduplication Audit")
    print("=" * 60)

    dataset_dirs = ["datasets/finguard_bench_real", "datasets/finguard_bench"]
    split_records = {"train": [], "validation": [], "test": []}
    text_hashes = {"train": set(), "validation": set(), "test": set()}

    manifest = {
        "sources": {},
        "leakage_audit": {
            "train_val_overlap": 0,
            "train_test_overlap": 0,
            "val_test_overlap": 0,
            "passed": False
        },
        "split_counts": {}
    }

    # 1. Audit local statutory files
    for d in dataset_dirs:
        manifest["sources"][d] = {}
        for split in ["train.jsonl", "validation.jsonl", "test.jsonl"]:
            p = os.path.join(d, split)
            split_key = split.replace(".jsonl", "")
            if not os.path.exists(p):
                continue

            rows = 0
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    rows += 1
                    q = item.get("query", "").strip()
                    r = item.get("response", "").strip()
                    q_lbl = 1 if str(item.get("query_label", "safe")).strip().lower() in ["unsafe", "1", "true"] else 0
                    
                    q_hash = hash_text(q)
                    text_hashes[split_key].add(q_hash)
                    split_records[split_key].append({
                        "query": q,
                        "label": q_lbl,
                        "hash": q_hash,
                        "source": d,
                        "response": r
                    })
            manifest["sources"][d][split_key] = rows

    # 2. Audit HuggingFace injection dataset splits
    try:
        ds = load_dataset("nandhak12/finguard-finance-injection-dataset")
        hf_train = ds["train"]
        hf_test = ds["test"]

        manifest["sources"]["nandhak12/finguard-finance-injection-dataset"] = {
            "train": len(hf_train),
            "test": len(hf_test)
        }

        for x in hf_train:
            q = str(x["user_message"]).strip()
            lbl = 1 if str(x["label"]).upper() == "ATTACK" else 0
            q_hash = hash_text(q)
            text_hashes["train"].add(q_hash)
            split_records["train"].append({
                "query": q,
                "label": lbl,
                "hash": q_hash,
                "source": "hf_injection"
            })

        for x in hf_test:
            q = str(x["user_message"]).strip()
            lbl = 1 if str(x["label"]).upper() == "ATTACK" else 0
            q_hash = hash_text(q)
            text_hashes["test"].add(q_hash)
            split_records["test"].append({
                "query": q,
                "label": lbl,
                "hash": q_hash,
                "source": "hf_injection"
            })
    except Exception as e:
        print(f"Warning: Could not load external injection dataset: {e}")

    # 3. Check for Data Leakage across splits
    train_val_overlap = text_hashes["train"].intersection(text_hashes["validation"])
    train_test_overlap = text_hashes["train"].intersection(text_hashes["test"])
    val_test_overlap = text_hashes["validation"].intersection(text_hashes["test"])

    manifest["leakage_audit"]["train_val_overlap"] = len(train_val_overlap)
    manifest["leakage_audit"]["train_test_overlap"] = len(train_test_overlap)
    manifest["leakage_audit"]["val_test_overlap"] = len(val_test_overlap)
    manifest["leakage_audit"]["passed"] = (
        len(train_val_overlap) == 0 and len(train_test_overlap) == 0 and len(val_test_overlap) == 0
    )

    manifest["split_counts"] = {
        "train": len(split_records["train"]),
        "validation": len(split_records["validation"]),
        "test": len(split_records["test"])
    }

    print("\nAudit Summary:")
    print(f"- Train Samples:      {manifest['split_counts']['train']}")
    print(f"- Validation Samples: {manifest['split_counts']['validation']}")
    print(f"- Test Samples:       {manifest['split_counts']['test']}")
    print(f"- Train-Test Overlap: {len(train_test_overlap)} items")
    print(f"- Train-Val Overlap:  {len(train_val_overlap)} items")
    print(f"- Val-Test Overlap:   {len(val_test_overlap)} items")
    print(f"- Leakage Audit Pass: {manifest['leakage_audit']['passed']}")

    # Write audit report
    os.makedirs("experiments", exist_ok=True)
    manifest_path = os.path.join("experiments", "dataset_split_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest saved to: {manifest_path}")

    return manifest


if __name__ == "__main__":
    audit_splits()
