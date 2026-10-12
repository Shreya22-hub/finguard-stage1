# FinGuard-Stage1: Pure Paper Reproduction (arXiv:2605.29427)

This repository contains the **Stage 1 pure paper reproduction** of:

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

## 📊 Live Empirical Benchmark Results (Table 5 Reproduction)

We evaluated standard un-guarded models against our calibrated FinGuard guardrail on the official `FinGuard-Bench` holdout test sets, the `nandhak12/finguard-finance-injection-dataset` test set (3,080 total samples), and multi-dimensional adversarial benchmarks:

| Model / System | Test Samples | Query F1 | Response F1 | Adversarial F1 | Core Finding |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Qwen-Base (Paper Baseline Table 5)** | Multi-turn | 16.69% | 22.91% | — | Open base LLM misses subtle compliance breaches |
| **Live Qwen (`qwen3.8-27b` via Groq)** | 33 | 82.35% | **23.53%** | 97.44% | **Empirical paper replication**: base LLM response recall collapses to 13.3% |
| **Llama-Guard-3-8B (Paper Baseline)** | Multi-turn | 50.12% | 54.30% | — | Generic moderation misses financial regulations |
| **FinGuard Unified Guard (Our Repo)** | **3,080** | **99.19%** | **100.0%** | **91.89%** | Trained on 10,882 unified samples (Precision: 99.9%, Recall: 98.49%) |

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
