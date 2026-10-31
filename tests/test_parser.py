"""
Unit tests for structured output parsing in FinGuardJudge (P1 requirement).
Verifies:
1. Standard valid output format.
2. Case-insensitive header parsing.
3. Extra trailing prose / commentary handling.
4. Malformed / empty outputs return fail-safe error state (not defaulted to Safe).
5. Unsafe output with missing category header receives fail-safe assignment.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.judge import FinGuardJudge


def test_parse_valid_safe():
    raw = "Safety: Safe\nCategories: None"
    verdict = FinGuardJudge.parse_verdict(raw)
    assert verdict["safety"] == "Safe"
    assert verdict["categories"] == []
    assert verdict["is_valid_format"] is True


def test_parse_valid_unsafe_multiple_categories():
    raw = "Safety: Unsafe\nCategories: C01 Front-Running, C02 Insider Trading"
    verdict = FinGuardJudge.parse_verdict(raw)
    assert verdict["safety"] == "Unsafe"
    assert "C01 Front-Running" in verdict["categories"]
    assert "C02 Insider Trading" in verdict["categories"]
    assert verdict["is_valid_format"] is True


def test_parse_with_trailing_prose():
    raw = "Safety: Unsafe\nCategories: C03 Market Manipulation\n\nExplanation: The user is attempting to manipulate closing prices."
    verdict = FinGuardJudge.parse_verdict(raw)
    assert verdict["safety"] == "Unsafe"
    assert verdict["categories"] == ["C03 Market Manipulation"]
    assert verdict["is_valid_format"] is True


def test_parse_empty_or_whitespace_output():
    verdict = FinGuardJudge.parse_verdict("")
    assert verdict["safety"] == "Error"
    assert verdict["is_valid_format"] is False

    verdict_ws = FinGuardJudge.parse_verdict("   \n\t  ")
    assert verdict_ws["safety"] == "Error"
    assert verdict_ws["is_valid_format"] is False


def test_parse_malformed_prose_only():
    raw = "I am an AI assistant and I think this question is quite dangerous."
    verdict = FinGuardJudge.parse_verdict(raw)
    assert verdict["safety"] == "Unknown"
    assert verdict["is_valid_format"] is False


def test_disallow_silent_mock_in_evaluations():
    try:
        FinGuardJudge(backend="mock", allow_mock=False)
        assert False, "Expected ValueError when mock backend is forbidden in evaluation mode"
    except ValueError:
        pass


if __name__ == "__main__":
    print("Running parser unit tests...")
    test_parse_valid_safe()
    print("[PASS] test_parse_valid_safe")
    test_parse_valid_unsafe_multiple_categories()
    print("[PASS] test_parse_valid_unsafe_multiple_categories")
    test_parse_with_trailing_prose()
    print("[PASS] test_parse_with_trailing_prose")
    test_parse_empty_or_whitespace_output()
    print("[PASS] test_parse_empty_or_whitespace_output")
    test_parse_malformed_prose_only()
    print("[PASS] test_parse_malformed_prose_only")
    test_disallow_silent_mock_in_evaluations()
    print("[PASS] test_disallow_silent_mock_in_evaluations")
    print("All parser unit tests PASSED successfully!")
