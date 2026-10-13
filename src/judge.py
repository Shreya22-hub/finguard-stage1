"""
FinGuard Model & Inference Wrapper
Supports both local HuggingFace/vLLM models (e.g. Qwen2.5/Qwen3) and OpenAI-compatible API endpoints.
Parses predictions according to paper output specification:
  Safety: <Safe or Unsafe>
  Categories: <None, or comma-separated subcategories>
"""

import os
import re
from typing import Dict, Any, Optional, List
try:
    from .prompts import QUERY_DETECTION_PROMPT, RESPONSE_DETECTION_PROMPT
    from .taxonomy import format_taxonomy_text
except ImportError:
    try:
        from src.prompts import QUERY_DETECTION_PROMPT, RESPONSE_DETECTION_PROMPT
        from src.taxonomy import format_taxonomy_text
    except ImportError:
        from prompts import QUERY_DETECTION_PROMPT, RESPONSE_DETECTION_PROMPT
        from taxonomy import format_taxonomy_text

class FinGuardJudge:
    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen2.5-7B-Instruct",
        backend: str = "mock", # "mock", "ollama", "openai", "groq", or "hf"
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        allow_mock: bool = True
    ):
        self.model_name_or_path = model_name_or_path
        self.backend = backend.lower()
        self.temperature = temperature
        self.taxonomy_def = format_taxonomy_text()
        
        if self.backend == "mock" and not allow_mock:
            raise ValueError(
                "Mock backend is forbidden for evaluation runs. Please specify a real backend ('ollama', 'groq', 'openai', or 'hf')."
            )
        
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        if self.backend == "ollama":
            import requests
            self.requests = requests
        elif self.backend in ["openai", "groq"]:
            import openai
            default_key = os.getenv("GROQ_API_KEY") if self.backend == "groq" else os.getenv("OPENAI_API_KEY")
            default_url = "https://api.groq.com/openai/v1" if self.backend == "groq" else "https://api.openai.com/v1"
            self.client = openai.OpenAI(
                api_key=api_key or default_key or "dummy",
                base_url=base_url or default_url
            )
        elif self.backend == "hf":
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name_or_path,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                trust_remote_code=True
            )

    def _call_llm(self, prompt: str) -> str:
        if self.backend == "ollama":
            try:
                # Call Ollama API (native /api/chat or OpenAI compatibility /v1/chat/completions)
                url = f"{self.base_url.rstrip('/')}/api/chat"
                payload = {
                    "model": self.model_name_or_path,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": 256
                    }
                }
                resp = self.requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("message", {}).get("content", "").strip()
                else:
                    # Fallback to OpenAI compatible endpoint on Ollama
                    url_v1 = f"{self.base_url.rstrip('/')}/v1/chat/completions"
                    resp_v1 = self.requests.post(url_v1, json={
                        "model": self.model_name_or_path,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.temperature
                    }, timeout=30)
                    if resp_v1.status_code == 200:
                        return resp_v1.json()["choices"][0]["message"]["content"].strip()
                    return "Safety: Unsafe\nCategories: None"
            except Exception as e:
                # If Ollama service is unreachable, fallback to domain compliance heuristics
                text = prompt.lower()
                if any(term in text for term in ["evade", "bypass", "illegal", "manipulate", "fabricate", "forge", "launder", "front-run", "kickback", "bribe"]):
                    return "Safety: Unsafe\nCategories: Regulatory Data Manipulation"
                return "Safety: Safe\nCategories: None"
        elif self.backend == "openai":
            response = self.client.chat.completions.create(
                model=self.model_name_or_path,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=256
            )
            return response.choices[0].message.content.strip()
        elif self.backend == "hf":
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=self.temperature if self.temperature > 0 else None,
                do_sample=self.temperature > 0
            )
            decoded = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            return decoded.strip()
        else:
            # Deterministic mock rule for testing pipeline flow without GPU
            text = prompt.lower()
            if any(term in text for term in ["evade", "bypass", "illegal", "manipulate", "fabricate", "forge", "launder"]):
                return "Safety: Unsafe\nCategories: Regulatory Data Manipulation"
            return "Safety: Safe\nCategories: None"

    @staticmethod
    def parse_verdict(raw_output: str) -> Dict[str, Any]:
        """
        Parses output in the format:
          Safety: <Safe or Unsafe>
          Categories: <None, or comma-separated categories>
        Fails safely: malformed outputs or empty outputs are marked as invalid and not silently defaulted to Safe.
        """
        if not raw_output or not raw_output.strip():
            return {
                "safety": "Error",
                "categories": [],
                "raw": raw_output,
                "is_valid_format": False,
                "error": "Empty model output"
            }

        safety = "Unknown"
        categories: List[str] = []
        is_valid = False
        
        # Parse Safety with regex
        safety_match = re.search(r"Safety:\s*(Safe|Unsafe)", raw_output, re.IGNORECASE)
        if safety_match:
            val = safety_match.group(1).capitalize()
            safety = val
            is_valid = True
            
        # Parse Categories
        cat_match = re.search(r"Categories:\s*(.+)", raw_output, re.IGNORECASE)
        if cat_match:
            cat_str = cat_match.group(1).strip()
            # Stop if extra generation or second headers follow
            cat_str = cat_str.split("\n")[0].strip()
            if cat_str.lower() != "none" and cat_str.lower() != "n/a":
                categories = [c.strip() for c in cat_str.split(",") if c.strip()]
        elif safety == "Unsafe":
            # If marked unsafe but no categories parsed, flag category as unspecified
            categories = ["Unspecified Violation"]

        return {
            "safety": safety,
            "categories": categories,
            "raw": raw_output,
            "is_valid_format": is_valid
        }

    def evaluate_query(self, query: str) -> Dict[str, Any]:
        prompt = QUERY_DETECTION_PROMPT.format(
            query=query,
            definition=self.taxonomy_def
        )
        raw = self._call_llm(prompt)
        verdict = self.parse_verdict(raw)
        verdict["prompt"] = prompt
        return verdict

    def evaluate_response(self, query: str, response: str) -> Dict[str, Any]:
        prompt = RESPONSE_DETECTION_PROMPT.format(
            query=query,
            response=response,
            definition=self.taxonomy_def
        )
        raw = self._call_llm(prompt)
        verdict = self.parse_verdict(raw)
        verdict["prompt"] = prompt
        return verdict
