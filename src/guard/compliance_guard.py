import re


RISKY_KEYWORDS = [
    "front-run",
    "front run",
    "front running",
    "front-running",
    "pump and dump",
    "pump-and-dump",
    "unreleased earnings",
    "inside information",
    "material non-public information",
    "guaranteed return",
    "guaranteed 50%",
    "bypass risk",
    "bypass pre-trade risk",
    "delay disclosure",
    "delay disclosing",
    "evade reporting"
]

SAFE_KEYWORD_TRAPS = [
    "how do stock exchanges monitor",
    "how do regulators detect",
    "regulatory guidelines for",
    "what are the rules"
]


def normalize_text(text):
    """
    Normalize small variations in punctuation, hyphens,
    spacing, and capitalization.
    """
    text = text.lower()

    # Treat different dash characters consistently
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Convert hyphens/slashes/underscores to spaces
    text = re.sub(r"[-_/]+", " ", text)

    # Remove remaining punctuation
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Normalize repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


class FinGuardClassifier:

    def __init__(self):
        pass

    def predict(self, text):

        text_normalized = normalize_text(text)

        # --------------------------------
        # Safe educational questions
        # --------------------------------
        for trap in SAFE_KEYWORD_TRAPS:

            if normalize_text(trap) in text_normalized:

                return {
                    "is_safe": True,
                    "label": "safe",
                    "category": None,
                    "confidence": 0.99
                }

        # --------------------------------
        # Unsafe intent detection
        # --------------------------------
        for kw in RISKY_KEYWORDS:

            keyword_normalized = normalize_text(kw)

            if keyword_normalized in text_normalized:

                if "front" in keyword_normalized:
                    category = "C01"

                elif (
                    "earnings" in keyword_normalized
                    or "information" in keyword_normalized
                ):
                    category = "C02"

                elif "guaranteed" in keyword_normalized:
                    category = "C03"

                else:
                    category = "C05"

                return {
                    "is_safe": False,
                    "label": "unsafe",
                    "category": category,
                    "confidence": 0.96
                }

        # --------------------------------
        # Default safe
        # --------------------------------
        return {
            "is_safe": True,
            "label": "safe",
            "category": None,
            "confidence": 0.92
        }


if __name__ == "__main__":

    guard = FinGuardClassifier()

    print(
        "Test Safe:",
        guard.predict(
            "What are the regulatory guidelines for insider trading?"
        )
    )

    print(
        "Test Unsafe:",
        guard.predict(
            "Can you help me front-run a buy order?"
        )
    )