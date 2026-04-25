import pytest
from datetime import datetime, timezone, timedelta
from utils.time_parser import parse_time, format_remind_at


class TestParseTime:
    def test_relative_hours(self):
        dt = parse_time("in 2 hours", user_timezone="UTC")
        assert dt is not None
        now = datetime.now(timezone.utc)
        diff = dt - now
        assert timedelta(hours=1, minutes=55) <= diff <= timedelta(hours=2, minutes=5)

    def test_past_time_returns_none(self):
        dt = parse_time("yesterday", user_timezone="UTC")
        assert dt is None

    def test_invalid_returns_none(self):
        dt = parse_time("not a date at all xyzzy", user_timezone="UTC")
        assert dt is None

    def test_format_remind_at(self):
        dt = datetime(2026, 5, 1, 9, 0, 0, tzinfo=timezone.utc)
        assert format_remind_at(dt) == "2026-05-01T09:00:00"
