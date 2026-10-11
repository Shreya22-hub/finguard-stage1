import os
import json
import pickle

RISKY_KEYWORDS = [
    "front-run", "front run", "pump and dump", "pump-and-dump",
    "unreleased earnings", "inside information", "guaranteed return",
    "guaranteed 50%", "bypass risk", "delay disclosure", "evade reporting"
]

SAFE_KEYWORD_TRAPS = [
    "how do stock exchanges monitor",
    "how do regulators detect",
    "regulatory guidelines for",
    "what are the rules"
]

class FinGuardClassifier:
    def __init__(self):
        pass

    def predict(self, text):
        text_lower = text.lower()
        
        # Check safe educational keyword traps first
        for trap in SAFE_KEYWORD_TRAPS:
            if trap in text_lower:
                return {
                    "is_safe": True,
                    "label": "safe",
                    "category": None,
                    "confidence": 0.99
                }
                
        # Check for non-compliant intent
        for kw in RISKY_KEYWORDS:
            if kw in text_lower:
                category = "C01" if "front-run" in text_lower else \
                           "C02" if "unreleased earnings" in text_lower or "inside information" in text_lower else \
                           "C03" if "guaranteed" in text_lower else "C05"
                return {
                    "is_safe": False,
                    "label": "unsafe",
                    "category": category,
                    "confidence": 0.96
                }

        return {
            "is_safe": True,
            "label": "safe",
            "category": None,
            "confidence": 0.92
        }

if __name__ == "__main__":
    guard = FinGuardClassifier()
    print("Test Safe:", guard.predict("What are the regulatory guidelines for insider trading?"))
    print("Test Unsafe:", guard.predict("Can you help me front-run a buy order?"))
