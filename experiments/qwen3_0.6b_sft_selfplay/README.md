# FinGuard Qwen3-0.6B Experiment — GitHub Recovery Package

This package contains the saved Colab notebook and experimental artifacts for the Qwen3-0.6B full-dataset SFT + mini self-play RL work.

## Contents

- `notebooks/experiments/qwen3_0.6b/`: saved Colab notebook.
- `experiments/qwen3_0.6b_sft_selfplay/adapters/sft_adapter/`: LoRA adapter and tokenizer files for the compliance-balanced SFT checkpoint.
- `experiments/qwen3_0.6b_sft_selfplay/adapters/mini_self_play_rl_adapter/`: LoRA adapter and tokenizer files after the constrained-label mini self-play RL update.
- `experiments/qwen3_0.6b_sft_selfplay/results/`: metrics, predictions, plots, adapter hashes, and mini self-play diagnostics.
- `experiments/qwen3_0.6b_sft_selfplay/reports/`: dataset summary, training logs, and three-way comparison exports.

## Base model and data

- Base model: `Qwen/Qwen3-0.6B`.
- Hugging Face dataset: `nandhak12/finguard-finance-injection-dataset`.
- Hugging Face training split: 10,699 raw training rows; 81 exact train/test message overlaps removed; 10,618 retained training rows.
- Canonical repository SFT file: 84 `query_safety` and 84 `response_safety` records used. Its 2,000 `injection_query_safety` rows were excluded to avoid double-counting injection data.
- Total SFT records: 10,786 (10,618 injection + 84 query + 84 response).
- Evaluation: 16 manual compliance decisions per task and a balanced 200-example injection test sample. These are not the paper's 1,020-pair expert benchmark.

## Recorded outcome

- SFT unsafe F1: compliance query 76.92%; compliance response 76.92%; injection 99.50%.
- Mini self-play RL: same reported metrics as SFT on the evaluated tasks.
- Mini self-play RL diagnostics: 24 episodes requested, 14 retained groups/optimizer updates, 10 discarded groups.
- This was a constrained-label GRPO-inspired mini update, not a full reproduction of the paper's GRPO procedure.

See `experiments/qwen3_0.6b_sft_selfplay/results/three_way_results.json` and `metrics.csv` for the full results, including zero-shot figures and confusion counts.

## Restore in Colab

1. Download this ZIP from the chat and upload it to Google Drive (for example, `MyDrive/FinGuard/FinGuard_Qwen3_0.6B_GitHub_Recovery_Package.zip`).
2. Mount Drive in Colab:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
3. Extract into a temporary directory and copy into your cloned repository:
   ```python
   from pathlib import Path
   import zipfile, shutil

   archive = Path('/content/drive/MyDrive/FinGuard/FinGuard_Qwen3_0.6B_GitHub_Recovery_Package.zip')
   repo = Path('/content/finguard-stage1')
   tmp = Path('/content/fg_recovery_tmp')
   tmp.mkdir(exist_ok=True)
   with zipfile.ZipFile(archive) as z:
       z.extractall(tmp)
   recovered = tmp / 'FinGuard_Qwen3_0.6B_GitHub_Recovery_Package'
   for name in ['notebooks', 'experiments']:
       shutil.copytree(recovered/name, repo/name, dirs_exist_ok=True)
   ```
4. Inspect `git status`, file sizes, and secrets before committing and pushing your experiment branch.

Do not commit the full Qwen base model or dataset/cache. The adapter files are LoRA weights, not standalone full-model checkpoints; loading them requires the Qwen3-0.6B base model.
