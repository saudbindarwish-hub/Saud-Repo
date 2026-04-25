import pytest
from utils.validators import (
    validate_task_title, validate_priority, validate_task_id,
    validate_recovery_score, validate_hrv, validate_rhr,
    validate_sleep_hours, validate_sleep_quality, validate_strain_score,
    validate_reminder_message, validate_plan_time, validate_fitness_goal,
)


class TestTaskValidators:
    def test_title_valid(self):
        assert validate_task_title("Buy groceries") == "Buy groceries"

    def test_title_strips_whitespace(self):
        assert validate_task_title("  Buy groceries  ") == "Buy groceries"

    def test_title_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_task_title("")

    def test_title_too_long_raises(self):
        with pytest.raises(ValueError, match="500"):
            validate_task_title("x" * 501)

    def test_priority_valid(self):
        assert validate_priority("1") == 1
        assert validate_priority("2") == 2
        assert validate_priority("3") == 3

    def test_priority_invalid_raises(self):
        with pytest.raises(ValueError):
            validate_priority("4")
        with pytest.raises(ValueError):
            validate_priority("abc")

    def test_task_id_valid(self):
        assert validate_task_id("42") == 42

    def test_task_id_non_positive_raises(self):
        with pytest.raises(ValueError):
            validate_task_id("0")
        with pytest.raises(ValueError):
            validate_task_id("-1")

    def test_task_id_non_numeric_raises(self):
        with pytest.raises(ValueError):
            validate_task_id("abc")


class TestWhoopValidators:
    def test_recovery_score_valid(self):
        assert validate_recovery_score("0") == 0
        assert validate_recovery_score("100") == 100
        assert validate_recovery_score("75") == 75

    def test_recovery_score_out_of_range(self):
        with pytest.raises(ValueError):
            validate_recovery_score("101")
        with pytest.raises(ValueError):
            validate_recovery_score("-1")

    def test_recovery_score_non_numeric(self):
        with pytest.raises(ValueError):
            validate_recovery_score("abc")

    def test_hrv_valid(self):
        assert validate_hrv("45.2") == 45.2

    def test_hrv_invalid(self):
        with pytest.raises(ValueError):
            validate_hrv("0")
        with pytest.raises(ValueError):
            validate_hrv("abc")

    def test_rhr_valid(self):
        assert validate_rhr("60") == 60

    def test_rhr_out_of_range(self):
        with pytest.raises(ValueError):
            validate_rhr("29")
        with pytest.raises(ValueError):
            validate_rhr("201")

    def test_sleep_hours_valid(self):
        assert validate_sleep_hours("7.5") == 7.5

    def test_sleep_hours_invalid(self):
        with pytest.raises(ValueError):
            validate_sleep_hours("25")

    def test_sleep_quality_valid(self):
        assert validate_sleep_quality("85") == 85

    def test_sleep_quality_invalid(self):
        with pytest.raises(ValueError):
            validate_sleep_quality("101")

    def test_strain_score_valid(self):
        assert validate_strain_score("12.5") == 12.5

    def test_strain_score_invalid(self):
        with pytest.raises(ValueError):
            validate_strain_score("22")


class TestReminderValidators:
    def test_message_valid(self):
        assert validate_reminder_message("call mom") == "call mom"

    def test_message_empty_raises(self):
        with pytest.raises(ValueError):
            validate_reminder_message("")

    def test_message_too_long_raises(self):
        with pytest.raises(ValueError):
            validate_reminder_message("x" * 1001)


class TestPreferenceValidators:
    def test_plan_time_valid(self):
        assert validate_plan_time("08:00") == "08:00"
        assert validate_plan_time("23:59") == "23:59"

    def test_plan_time_invalid_format(self):
        with pytest.raises(ValueError):
            validate_plan_time("8:00")
        with pytest.raises(ValueError):
            validate_plan_time("25:00")

    def test_fitness_goal_valid(self):
        assert validate_fitness_goal("strength") == "strength"
        assert validate_fitness_goal("GENERAL") == "general"

    def test_fitness_goal_invalid(self):
        with pytest.raises(ValueError):
            validate_fitness_goal("yoga")
