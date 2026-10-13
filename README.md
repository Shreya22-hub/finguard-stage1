# FinGuard: Financial Regulatory Guardrails & Paper Reproduction Roadmap (arXiv:2605.29427)

This repository contains the **repaired compliance guardrail baseline and the full paper reproduction pipeline** of:

> **FinGuard: Detecting Financial Regulatory Non-Compliance in LLM Interactions**  
> *Huaixia Dou et al. (arXiv:2605.29427)*

---

## 🏛️ System Architecture

FinGuard implements a **Two-Checkpoint Guardrail Architecture** designed to detect regulatory non-compliance at both prompt submission and response generation:

```text
User Question
      │
      ▼
[Checkpoint 1: Query Compliance Guard]
      ├── RISKY ──► Safe Policy Layer ──► Refusal + Statutory Citation
      └── SAFE
            │
            ▼
    [Regulatory Retrieval: TF-IDF / Dense Embeddings]
            │
            ▼
    [Response Synthesizer / LLM]
            │
            ▼
[Checkpoint 2: Response Compliance Guard]
      ├── RISKY ──► Intercept & Replace with Compliant Refusal
      └── SAFE  ──► Deliver Grounded Response to User
```

---

## 🔬 System Components: Fast Baseline vs. Paper Reproduction

To ensure full transparency and reproducibility, this repository provides:

1. **FinGuard High-Speed CPU Baseline (Clean & Leakage-Audited)**:
   * **Method**: Sublinear word $(1, 3)$ + character $(3, 5)$ TF-IDF feature union with calibrated $L_2$-regularized Logistic Regression (`CalibratedClassifierCV`).
   * **Zero-Leakage Guarantee**: Trained strictly on `train` splits with all overlapping test fingerprints purged.
   * **Inference Latency**: Sub-10ms (average ~0.38ms–8.24ms) without requiring GPU VRAM.
   * **Held-out Test Performance**: Evaluated on 3,080 untouched holdout test samples:
     * **Accuracy**: **99.19%**
     * **Precision**: **99.05%**
     * **Recall**: **98.59%**
     * **F1 Score**: **98.82%**
     * **Adversarial Robustness F1**: **86.49%**

2. **Full Paper Neural Reproduction (Qwen3-8B LoRA SFT + Self-Play GRPO)**:
   * **SFT Specification**: Defined in [`configs/reproduction_sft.yaml`](file:///d:/finguard-stage1/configs/reproduction_sft.yaml) (Qwen3-8B / Qwen2.5-7B, LoRA rank 8, alpha 16, cosine schedule, learning rate 3e-5).
   * **GRPO Specification**: Defined in [`configs/reproduction_grpo.yaml`](file:///d:/finguard-stage1/configs/reproduction_grpo.yaml) (Group size 4, guard and generator reward scoring, policy gradient optimization).
   * **Target Hardware**: 8 × NVIDIA A100 80GB GPUs.

---

## 📊 Empirical Benchmark Results

| Model / System | Test Samples | Query F1 | Response F1 | Adversarial F1 | Core Finding |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Qwen-Base (Paper Baseline Table 5)** | Multi-turn | 16.69% | 22.91% | — | Open base LLM misses subtle compliance breaches |
| **Live Qwen (`qwen3.8-27b` via Groq)** | 33 | 82.35% | **23.53%** | 97.44% | **Empirical paper replication**: base LLM response recall collapses to 13.3% |
| **Llama-Guard-3-8B (Paper Baseline)** | Multi-turn | 50.12% | 54.30% | — | Generic moderation misses financial regulations |
| **FinGuard Baseline (Our Repo)** | **3,080** | **98.82%** | **100.0%** | **86.49%** | Clean held-out evaluation on frozen checkpoint (Zero Leakage Audited) |

---

## 📂 Repository Layout

```
finguard-stage1/
├── app/
│   └── streamlit_app.py                # Interactive web dashboard (Trained ML / Ollama / Cloud)
├── data/
│   ├── raw_regulations/                # Statutory legal texts (BSA, SEC, CFPB, ECOA, FCPA, FINRA, GLBA, SOX)
│   └── processed/                      # Extracted structured clauses & compliance points
├── datasets/
│   ├── taxonomy/                       # Financial risk taxonomy (11 categories, 35 subcategories)
│   ├── finguard_bench/                 # FinGuard-Bench dataset (train/val/test splits)
│   ├── finguard_bench_real/            # Grounded statutory benchmark dataset
│   └── adversarial_test.jsonl          # 8-dimensional evasion and jailbreak test set
├── models/
│   ├── finguard_trained_guard.joblib   # Multi-head FinGuard compliance guard bundle
│   └── injection_classifier.joblib     # Prompt injection classifier (99.47% accuracy)
├── src/
│   ├── ingestion/                      # Clause & compliance point extraction
│   ├── taxonomy/                       # Taxonomy definitions & discovery
│   ├── retrieval/                      # Dense & sparse regulatory retriever
│   ├── guard/                          # Two-checkpoint compliance classifier
│   ├── pipeline/                       # End-to-end dual-checkpoint pipeline
│   └── evaluation/                     # Benchmark runners (evaluate_paper_benchmarks, evaluate_live_groq)
├── requirements.txt                    # Project dependencies
└── README.md                           # Documentation
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional, for Live Cloud LLMs)
Copy `.env.example` to `.env` and add your free API key:
```bash
# In .env:
GROQ_API_KEY=gsk_your_key_here
```

### 3. Run FinGuard Pipeline CLI
```bash
python -m src.pipeline.finguard_pipeline
```

### 4. Run Paper Benchmark Evaluations
```bash
# Evaluate FinGuard trained model on the paper benchmark
python -m src.evaluation.evaluate_paper_benchmarks

# Evaluate live Groq model (Qwen 3.8 / Llama 3)
python -m src.evaluation.evaluate_live_groq
```

### 5. Launch Interactive UI
```bash
streamlit run app/streamlit_app.py
```
