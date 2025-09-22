from datetime import datetime, timedelta
from habits.repo import start_of_day, start_of_iso_week, period_bounds, longest_streak_for_habit, step_for

def test_start_of_day():
    ts = datetime(2025, 9, 15, 14, 30, 45)
    s = start_of_day(ts)
    assert s == datetime(2025, 9, 15)

def test_start_of_iso_week():
    wed = datetime(2025, 9, 17, 23, 59)   # Wednesday
    s = start_of_iso_week(wed)
    assert s == datetime(2025, 9, 15)     # Monday of same ISO week

def test_period_bounds_daily():
    ts = datetime(2025, 9, 15, 14, 0)
    start, end = period_bounds(ts, "daily")
    assert start == datetime(2025, 9, 15)
    assert end   == datetime(2025, 9, 16)

def test_period_bounds_weekly():
    ts = datetime(2025, 9, 21, 8, 0)      # Sunday
    start, end = period_bounds(ts, "weekly")
    assert start == datetime(2025, 9, 15)  # Monday
    assert end   == datetime(2025, 9, 22)  # +7 days

def test_longest_streak_for_habit_daily():
    base = datetime(2025, 9, 15)  # Monday
    periods = [base, base + timedelta(days=1), base + timedelta(days=2)]
    s = longest_streak_for_habit(periods, step_for("daily"))
    assert s == 3
