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
    [Regulatory Retrieval: FAISS + Dense Embeddings]
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

## 📂 Repository Layout

```
finguard-stage1/
├── app/
│   └── streamlit_app.py                # Interactive web dashboard
├── data/
│   ├── regulations/                    # Raw regulatory text sources
│   └── processed/                      # Extracted structured clauses & FAISS vector index
├── datasets/
│   ├── taxonomy/                       # Discovered empirical regulatory taxonomy
│   └── finguard_bench/                 # FinGuard-Bench dataset (train/val/test splits)
├── src/
│   ├── ingestion/                      # Clause & compliance point extraction
│   ├── taxonomy/                       # Unsupervised HDBSCAN taxonomy discovery
│   ├── retrieval/                      # FAISS dense vector retriever
│   ├── guard/                          # Two-Checkpoint compliance classifier
│   ├── pipeline/                       # FinGuard dual-checkpoint chatbot & policy layer
│   └── evaluation/                     # FinGuard-Bench evaluation runner
├── requirements.txt                    # Project dependencies
└── README.md                           # Documentation
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run FinGuard Pipeline CLI
```bash
python -m src.pipeline.finguard_pipeline
```

### 3. Run FinGuard-Bench Evaluation
```bash
python -m src.evaluation.evaluate
```

### 4. Launch Interactive UI
```bash
streamlit run app/streamlit_app.py
```
