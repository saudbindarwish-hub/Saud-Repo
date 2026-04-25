import pytest
from services.whoop_service import rule_based_suggestion


class TestRuleBasedSuggestion:
    def test_high_recovery(self):
        result = rule_based_suggestion(80)
        assert "full" in result.lower() or "great" in result.lower()

    def test_moderate_recovery(self):
        result = rule_based_suggestion(50)
        assert "moderate" in result.lower() or "light" in result.lower()

    def test_low_recovery(self):
        result = rule_based_suggestion(20)
        assert "rest" in result.lower() or "low" in result.lower()

    def test_boundary_67(self):
        result = rule_based_suggestion(67)
        assert result  # Just ensure it returns something

    def test_boundary_34(self):
        result = rule_based_suggestion(34)
        assert result
