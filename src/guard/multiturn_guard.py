import re
import os
import sys

# Ensure repository root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.adaptation.jurisdiction_adapter import JurisdictionAdapter


class MultiTurnSessionGuard:
    """
    Multi-Turn Conversational Compliance Guardrail.
    Tracks cumulative compliance risk over dialogue turns to prevent
    context-stacking and progressive escalation evasion.
    """

    def __init__(self, jurisdiction="US_GLOBAL", decay_factor=0.70, risk_threshold=0.65):
        self.jurisdiction_adapter = JurisdictionAdapter(default_jurisdiction=jurisdiction)
        self.decay_factor = decay_factor
        self.risk_threshold = risk_threshold
        self.reset_session()

        # Sensitive compliance patterns and boundary indicators
        self.risk_patterns = [
            (r"(?i)\b(insider|unannounced|draft report|non-public|before.*earnings|board meeting.*trade|front-run)\b", 0.75, "Insider Trading"),
            (r"(?i)\b(bypass|disable.*risk|kill-switch|order-to-trade|flood.*order|spoof|quote.*non-bona-fide)\b", 0.80, "Algorithmic Controls"),
            (r"(?i)\b(obscur.*beneficial|nominee.*entity|hide.*owner|smurf|structur.*deposit|circumvent.*kyc)\b", 0.85, "AML / Structuring"),
            (r"(?i)\b(guaranteed.*profit|without.*license|unregistered.*advis|telegram.*signals|tip.*channel)\b", 0.75, "Unlicensed Advisory"),
            (r"(?i)\b(short-term call options|structure.*trade|execute.*before|profit before the announcement)\b", 0.60, "Insider Trading"),
            (r"(?i)\b(how.*can.*they.*structure|profit.*based on draft|exploit|arbitrage.*leak)\b", 0.55, "Market Manipulation")
        ]

        # Contextual priming indicators (turn 1 or 2 exploring theoretical boundary)
        self.priming_patterns = [
            r"(?i)\b(what happens if|draft quarterly report|internal analyst|offshore holding|subscription-based commentary)\b",
            r"(?i)\b(pre-trade risk control|gateways|tier.*entities|regulatory boundaries)\b"
        ]

    def reset_session(self):
        """Reset conversation session history and cumulative risk."""
        self.history = []
        self.cumulative_risk = 0.0

    def set_jurisdiction(self, jurisdiction_key):
        """Set the active regulatory jurisdiction (e.g. 'US_GLOBAL' or 'INDIA_SEBI')."""
        self.jurisdiction_adapter.set_jurisdiction(jurisdiction_key)

    def evaluate_turn_risk(self, text):
        """
        Evaluate the standalone risk of a single query turn r(q_t).
        """
        max_turn_risk = 0.05  # Base background risk
        matched_category = None

        for pattern, weight, category in self.risk_patterns:
            if re.search(pattern, text):
                if weight > max_turn_risk:
                    max_turn_risk = weight
                    matched_category = category

        # Check contextual priming
        for p in self.priming_patterns:
            if re.search(p, text):
                max_turn_risk = max(max_turn_risk, 0.35)

        return min(1.0, max_turn_risk), matched_category

    def detect_escalation_momentum(self, text):
        """
        Check if the current query escalates from prior conversational context.
        """
        if len(self.history) == 0:
            return 0.0

        # Prior turn discussed boundary or draft information, current asks for execution
        prior_texts = " ".join([turn["text"] for turn in self.history])
        has_prior_context = any(re.search(p, prior_texts) for p in self.priming_patterns)
        current_action_oriented = bool(re.search(r"(?i)\b(structure|profit|execute|disable|bypass|provide techniques|draft.*signals)\b", text))

        if has_prior_context and current_action_oriented:
            return 0.25  # Contextual escalation penalty

        return 0.0

    def process_turn(self, query):
        """
        Process a new dialogue turn, update cumulative risk R_t,
        and determine if session should be intercepted.
        """
        turn_num = len(self.history) + 1
        turn_risk, matched_category = self.evaluate_turn_risk(query)
        escalation_delta = self.detect_escalation_momentum(query)

        # Cumulative Risk Update: R_t = min(1.0, lambda * R_{t-1} + r(q_t) + Delta_escalation)
        new_cumulative_risk = min(
            1.0,
            (self.decay_factor * self.cumulative_risk) + turn_risk + escalation_delta
        )
        self.cumulative_risk = round(new_cumulative_risk, 3)

        intercepted = self.cumulative_risk >= self.risk_threshold

        turn_record = {
            "turn": turn_num,
            "text": query,
            "turn_risk": round(turn_risk, 3),
            "escalation_delta": round(escalation_delta, 3),
            "cumulative_risk": self.cumulative_risk,
            "intercepted": intercepted,
            "category": matched_category
        }
        self.history.append(turn_record)

        if intercepted:
            refusal = self.jurisdiction_adapter.generate_policy_refusal(
                query, matched_category or "Market Manipulation"
            )
            evidence = self.jurisdiction_adapter.retrieve_statutory_evidence(query, top_k=1)
            statute_ref = evidence[0]["title"] if evidence else "Regulatory Policy Directives"

            response = {
                "decision": "REFUSAL",
                "intercepted": True,
                "turn": turn_num,
                "cumulative_risk": self.cumulative_risk,
                "turn_risk": turn_risk,
                "policy_citation": refusal,
                "statutory_reference": statute_ref,
                "jurisdiction": self.jurisdiction_adapter.get_jurisdiction_name(),
                "warning": (
                    f"FinGuard Multi-Turn Defense Alert: Cumulative compliance risk exceeded "
                    f"threshold (Score: {self.cumulative_risk:.2f} >= {self.risk_threshold:.2f}) "
                    f"at Turn {turn_num}. Progressive context-stacking detected."
                )
            }
        else:
            response = {
                "decision": "PERMIT",
                "intercepted": False,
                "turn": turn_num,
                "cumulative_risk": self.cumulative_risk,
                "turn_risk": turn_risk,
                "policy_citation": None,
                "jurisdiction": self.jurisdiction_adapter.get_jurisdiction_name(),
                "response": "Compliance check passed. The request conforms with statutory guidelines."
            }

        return response
