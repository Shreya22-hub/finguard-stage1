import os
import json
import time
from dotenv import load_dotenv
from src.judge import FinGuardJudge
from src.evaluation.evaluate_paper_benchmarks import load_test_benchmarks, calculate_metrics

load_dotenv()

def run_live_groq_benchmark(model_name="qwen/qwen3.8-27b", max_samples=None):
    api_key = os.getenv("GROQ_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
    
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env!")
        
    print(f"=== Running Live Paper Benchmark with Groq: {model_name} ===")
    
    judge = FinGuardJudge(
        backend="openai",
        model_name_or_path=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.0
    )
    
    test_samples, adv_samples = load_test_benchmarks()
    if max_samples:
        test_samples = test_samples[:max_samples]
        adv_samples = adv_samples[:max_samples]
        
    print(f"Evaluating {len(test_samples)} benchmark test samples and {len(adv_samples)} adversarial samples...")
    
    # 1. Query-level Evaluation
    q_tp = q_fp = q_tn = q_fn = 0
    query_results = []
    
    print("\n--- Evaluating Checkpoint 1 (Queries) ---")
    for idx, sample in enumerate(test_samples):
        query = sample["query"]
        gold_unsafe = (sample["query_label"] == 1)
        
        try:
            verdict = judge.evaluate_query(query)
            pred_unsafe = (verdict["safety"] == "Unsafe")
            
            if gold_unsafe:
                if pred_unsafe: q_tp += 1
                else: q_fn += 1
            else:
                if pred_unsafe: q_fp += 1
                else: q_tn += 1
                
            query_results.append({
                "query": query,
                "gold": "Unsafe" if gold_unsafe else "Safe",
                "pred": verdict["safety"],
                "categories": verdict.get("categories", [])
            })
            print(f"[{idx+1}/{len(test_samples)}] Gold: {'Unsafe' if gold_unsafe else 'Safe':<6} | Pred: {verdict['safety']:<6} | Query: {query[:50]}...")
            time.sleep(0.5) # respect rate limit
        except Exception as e:
            print(f"Error on query {idx}: {e}")
            time.sleep(2)
            
    query_metrics = calculate_metrics(q_tp, q_fp, q_tn, q_fn)
    
    # 2. Response-level Evaluation
    r_tp = r_fp = r_tn = r_fn = 0
    response_samples = [s for s in test_samples if s.get("response")]
    print(f"\n--- Evaluating Checkpoint 2 (Responses: {len(response_samples)} samples) ---")
    for idx, sample in enumerate(response_samples):
        query = sample["query"]
        resp = sample["response"]
        gold_unsafe = (sample["response_label"] == 1)
        
        try:
            verdict = judge.evaluate_response(query, resp)
            pred_unsafe = (verdict["safety"] == "Unsafe")
            
            if gold_unsafe:
                if pred_unsafe: r_tp += 1
                else: r_fn += 1
            else:
                if pred_unsafe: r_fp += 1
                else: r_tn += 1
                
            print(f"[{idx+1}/{len(response_samples)}] Gold: {'Unsafe' if gold_unsafe else 'Safe':<6} | Pred: {verdict['safety']:<6} | Resp: {resp[:50]}...")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error on response {idx}: {e}")
            time.sleep(2)
            
    response_metrics = calculate_metrics(r_tp, r_fp, r_tn, r_fn)
    
    # 3. Adversarial Robustness
    adv_tp = adv_fp = adv_tn = adv_fn = 0
    print(f"\n--- Evaluating Adversarial Evasion ({len(adv_samples)} samples) ---")
    for idx, sample in enumerate(adv_samples):
        query = sample["query"]
        gold_unsafe = (sample["label"] == 1)
        
        try:
            verdict = judge.evaluate_query(query)
            pred_unsafe = (verdict["safety"] == "Unsafe")
            
            if gold_unsafe:
                if pred_unsafe: adv_tp += 1
                else: adv_fn += 1
            else:
                if pred_unsafe: adv_fp += 1
                else: adv_tn += 1
                
            print(f"[{idx+1}/{len(adv_samples)}] Gold: {'Unsafe' if gold_unsafe else 'Safe':<6} | Pred: {verdict['safety']:<6} | Query: {query[:50]}...")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error on adv {idx}: {e}")
            time.sleep(2)
            
    adv_metrics = calculate_metrics(adv_tp, adv_fp, adv_tn, adv_fn)
    
    report = {
        "model_name": model_name,
        "backend": "Groq Cloud",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checkpoint_1_query_guard": query_metrics,
        "checkpoint_2_response_guard": response_metrics,
        "adversarial_robustness": adv_metrics
    }
    
    os.makedirs("experiments", exist_ok=True)
    out_file = os.path.join("experiments", f"live_{model_name.replace('/', '_')}_benchmark.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print("\n" + "="*60)
    print(f"LIVE BENCHMARK RESULTS: {model_name}")
    print("="*60)
    print(f"Query Level:     Accuracy: {query_metrics['accuracy']}% | F1: {query_metrics['f1']}% | Precision: {query_metrics['precision']}% | Recall: {query_metrics['recall']}%")
    print(f"Response Level:  Accuracy: {response_metrics['accuracy']}% | F1: {response_metrics['f1']}% | Precision: {response_metrics['precision']}% | Recall: {response_metrics['recall']}%")
    print(f"Adversarial:     Accuracy: {adv_metrics['accuracy']}% | F1: {adv_metrics['f1']}% | Precision: {adv_metrics['precision']}% | Recall: {adv_metrics['recall']}%")
    print("="*60)
    print(f"Saved results to: {out_file}")
    
    return report

if __name__ == "__main__":
    run_live_groq_benchmark()
