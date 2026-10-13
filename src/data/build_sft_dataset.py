"""
FinGuard SFT Training Data Builder
Formats query-level and response-level training data into the canonical structured
prompt-response format required for Qwen3-8B / Qwen2.5-7B LoRA fine-tuning.

Format adheres to paper's prompt template:
Input:
  Human: [Query Detection Prompt with Taxonomy definitions + Query]
Target:
  Assistant: Safety: <Safe or Unsafe>\nCategories: <None or specific category>
"""

import os
import json
from datasets import load_dataset
try:
    from src.prompts import QUERY_DETECTION_PROMPT, RESPONSE_DETECTION_PROMPT
    from src.taxonomy import format_taxonomy_text
except ImportError:
    from prompts import QUERY_DETECTION_PROMPT, RESPONSE_DETECTION_PROMPT
    from taxonomy import format_taxonomy_text


def build_sft_dataset(
    output_path="data/finguard_sft_train.jsonl",
    max_external_samples=2000
):
    print("=" * 60)
    print("Building Canonical FinGuard SFT Dataset for Qwen LoRA")
    print("=" * 60)

    taxonomy_def = format_taxonomy_text()
    records = []

    # 1. Statutory Grounded Benchmark Training Split
    stat_path = "datasets/finguard_bench_real/train.jsonl"
    if os.path.exists(stat_path):
        with open(stat_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                q = item.get("query", "").strip()
                if not q:
                    continue
                lbl = 1 if str(item.get("query_label", "safe")).strip().lower() in ["unsafe", "1", "true"] else 0
                cat = item.get("query_category") or "General Financial Compliance"

                prompt = QUERY_DETECTION_PROMPT.format(query=q, definition=taxonomy_def)
                target = f"Safety: {'Unsafe' if lbl == 1 else 'Safe'}\nCategories: {cat if lbl == 1 else 'None'}"

                records.append({
                    "instruction": prompt,
                    "input": "",
                    "output": target,
                    "task": "query_safety"
                })

                # Also format query-conditioned response training
                r = item.get("response", "").strip()
                if r:
                    r_lbl = 1 if str(item.get("response_label", "safe")).strip().lower() in ["unsafe", "1", "true"] else 0
                    r_cat = item.get("response_category") or cat
                    r_prompt = RESPONSE_DETECTION_PROMPT.format(query=q, response=r, definition=taxonomy_def)
                    r_target = f"Safety: {'Unsafe' if r_lbl == 1 else 'Safe'}\nCategories: {r_cat if r_lbl == 1 else 'None'}"
                    records.append({
                        "instruction": r_prompt,
                        "input": "",
                        "output": r_target,
                        "task": "response_safety"
                    })

    print(f"Statutory SFT samples generated: {len(records)}")

    # 2. Financial Injection Training Split
    try:
        ds = load_dataset("nandhak12/finguard-finance-injection-dataset")
        train_ds = ds["train"]
        count = 0
        for item in train_ds:
            if count >= max_external_samples:
                break
            msg = str(item["user_message"]).strip()
            if not msg:
                continue
            lbl = 1 if str(item["label"]).upper() == "ATTACK" else 0
            cat = "Prompt Injection / Financial Attack"

            prompt = QUERY_DETECTION_PROMPT.format(query=msg, definition=taxonomy_def)
            target = f"Safety: {'Unsafe' if lbl == 1 else 'Safe'}\nCategories: {cat if lbl == 1 else 'None'}"

            records.append({
                "instruction": prompt,
                "input": "",
                "output": target,
                "task": "injection_query_safety"
            })
            count += 1
        print(f"External injection SFT samples added: {count}")
    except Exception as e:
        print(f"Warning: Could not add external injection samples: {e}")

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"\nTotal SFT Training Examples: {len(records)}")
    print(f"SFT Dataset saved -> {output_path}")
    return records


if __name__ == "__main__":
    build_sft_dataset()
