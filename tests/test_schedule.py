"""
The repeat rules. Date arithmetic is where mistakes hide for months, so this is the most
heavily tested part of the app: month ends, leap years, "every second week", start and
end dates, and a cross-check of the two functions against each other.
"""

from datetime import date, timedelta

import pytest

from tasks.schedule import (
    DAYS,
    MONTHLY,
    ONCE,
    WEEKLY,
    Rule,
    first_on_or_after,
    is_scheduled,
    next_after,
)

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

# Handy fixed points. 2 November 2026 is a Monday.
MONDAY = date(2026, 11, 2)


def days_scheduled(rule: Rule, first: date, count: int) -> list[date]:
    found, day = [], first_on_or_after(rule, first)
    while day is not None and len(found) < count:
        found.append(day)
        day = next_after(rule, day)
    return found


def test_the_fixed_point_is_a_monday():
    assert MONDAY.weekday() == MON


# ---- Once ----


def test_a_one_time_task_is_scheduled_on_its_day_only():
    rule = Rule(ONCE, start=date(2026, 11, 10))

    assert first_on_or_after(rule, date(2026, 11, 1)) == date(2026, 11, 10)
    assert first_on_or_after(rule, date(2026, 11, 10)) == date(2026, 11, 10)
    assert first_on_or_after(rule, date(2026, 11, 11)) is None
    assert next_after(rule, date(2026, 11, 10)) is None


# ---- Every N days ----


def test_a_daily_task_is_scheduled_every_day_from_its_start():
    rule = Rule(DAYS, start=MONDAY)

    assert not is_scheduled(rule, MONDAY - timedelta(days=1))
    assert days_scheduled(rule, MONDAY, 3) == [MONDAY, date(2026, 11, 3), date(2026, 11, 4)]


def test_every_third_day_is_counted_from_the_start_not_from_when_it_was_done():
    rule = Rule(DAYS, start=date(2026, 11, 1), interval=3)

    assert days_scheduled(rule, date(2026, 11, 1), 4) == [
        date(2026, 11, 1),
        date(2026, 11, 4),
        date(2026, 11, 7),
        date(2026, 11, 10),
    ]
    # Asked from a day in between, the answer is the next day on the same grid.
    assert first_on_or_after(rule, date(2026, 11, 5)) == date(2026, 11, 7)
    assert next_after(rule, date(2026, 11, 4)) == date(2026, 11, 7)


def test_every_n_days_crosses_a_leap_day_correctly():
    rule = Rule(DAYS, start=date(2028, 2, 27), interval=2)

    assert days_scheduled(rule, date(2028, 2, 27), 3) == [
        date(2028, 2, 27),
        date(2028, 2, 29),
        date(2028, 3, 2),
    ]


# ---- Weekly ----


def test_a_weekly_task_is_scheduled_on_its_weekdays():
    rule = Rule(WEEKLY, start=MONDAY, weekdays=(WED, SAT))

    assert days_scheduled(rule, MONDAY, 4) == [
        date(2026, 11, 4),
        date(2026, 11, 7),
        date(2026, 11, 11),
        date(2026, 11, 14),
    ]


def test_a_weekly_task_that_starts_midweek_skips_the_days_before_its_start():
    thursday = date(2026, 11, 5)
    rule = Rule(WEEKLY, start=thursday, weekdays=(MON, FRI))

    # Monday of the starting week is before the start; Friday is the first.
    assert days_scheduled(rule, date(2026, 11, 1), 3) == [
        date(2026, 11, 6),
        date(2026, 11, 9),
        date(2026, 11, 13),
    ]


def test_every_second_week_counts_whole_weeks_from_the_starting_week():
    rule = Rule(WEEKLY, start=MONDAY, interval=2, weekdays=(TUE,))

    assert days_scheduled(rule, MONDAY, 3) == [
        date(2026, 11, 3),
        date(2026, 11, 17),
        date(2026, 12, 1),
    ]
    # The Tuesday of the week in between is not scheduled.
    assert not is_scheduled(rule, date(2026, 11, 10))


def test_every_second_week_keeps_its_rhythm_across_new_year():
    rule = Rule(WEEKLY, start=date(2026, 12, 21), interval=2, weekdays=(MON,))

    assert days_scheduled(rule, date(2026, 12, 21), 3) == [
        date(2026, 12, 21),
        date(2027, 1, 4),
        date(2027, 1, 18),
    ]


def test_a_weekly_task_without_weekdays_is_never_scheduled():
    assert first_on_or_after(Rule(WEEKLY, start=MONDAY), MONDAY) is None


# ---- Monthly ----


def test_a_monthly_task_is_scheduled_on_its_day_of_the_month():
    rule = Rule(MONTHLY, start=date(2026, 11, 1), day_of_month=1)

    assert days_scheduled(rule, date(2026, 11, 1), 3) == [
        date(2026, 11, 1),
        date(2026, 12, 1),
        date(2027, 1, 1),
    ]


def test_the_31st_means_the_last_day_in_shorter_months():
    rule = Rule(MONTHLY, start=date(2027, 1, 1), day_of_month=31)

    assert days_scheduled(rule, date(2027, 1, 1), 5) == [
        date(2027, 1, 31),
        date(2027, 2, 28),
        date(2027, 3, 31),
        date(2027, 4, 30),
        date(2027, 5, 31),
    ]


def test_the_last_day_of_february_in_a_leap_year_is_the_29th():
    rule = Rule(MONTHLY, start=date(2028, 1, 1), day_of_month=30)

    assert first_on_or_after(rule, date(2028, 2, 1)) == date(2028, 2, 29)


def test_a_monthly_task_whose_day_has_passed_in_the_starting_month_begins_next_month():
    rule = Rule(MONTHLY, start=date(2026, 11, 20), day_of_month=5)

    assert first_on_or_after(rule, date(2026, 11, 1)) == date(2026, 12, 5)


def test_every_third_month_counts_from_the_starting_month():
    rule = Rule(MONTHLY, start=date(2026, 11, 1), interval=3, day_of_month=15)

    assert days_scheduled(rule, date(2026, 11, 1), 3) == [
        date(2026, 11, 15),
        date(2027, 2, 15),
        date(2027, 5, 15),
    ]


def test_a_monthly_task_without_a_day_is_never_scheduled():
    assert first_on_or_after(Rule(MONTHLY, start=MONDAY), MONDAY) is None


# ---- Start and end ----


def test_nothing_is_scheduled_before_the_start_or_after_the_end():
    rule = Rule(DAYS, start=date(2026, 11, 10), end=date(2026, 11, 12))

    assert first_on_or_after(rule, date(2026, 1, 1)) == date(2026, 11, 10)
    assert days_scheduled(rule, date(2026, 1, 1), 10) == [
        date(2026, 11, 10),
        date(2026, 11, 11),
        date(2026, 11, 12),
    ]
    assert next_after(rule, date(2026, 11, 12)) is None


def test_an_end_between_two_scheduled_days_stops_before_the_second():
    rule = Rule(WEEKLY, start=MONDAY, weekdays=(MON,), end=date(2026, 11, 8))

    assert days_scheduled(rule, MONDAY, 5) == [MONDAY]


def test_an_unknown_way_of_repeating_is_an_error_not_a_silent_never():
    with pytest.raises(ValueError):
        is_scheduled(Rule("yearly", start=MONDAY), MONDAY)


# ---- The two functions against each other ----

RULES = [
    Rule(ONCE, start=date(2027, 3, 15)),
    Rule(DAYS, start=date(2027, 1, 1)),
    Rule(DAYS, start=date(2027, 1, 3), interval=5),
    Rule(DAYS, start=date(2027, 2, 1), interval=45),
    Rule(WEEKLY, start=date(2027, 1, 6), weekdays=(MON, WED, SUN)),
    Rule(WEEKLY, start=date(2027, 1, 6), interval=3, weekdays=(SAT,)),
    Rule(WEEKLY, start=date(2027, 1, 6), interval=8, weekdays=(TUE, THU)),
    Rule(MONTHLY, start=date(2027, 1, 20), day_of_month=1),
    Rule(MONTHLY, start=date(2027, 1, 1), day_of_month=31),
    Rule(MONTHLY, start=date(2027, 1, 1), interval=6, day_of_month=29),
    Rule(MONTHLY, start=date(2027, 1, 1), interval=12, day_of_month=30),
    Rule(DAYS, start=date(2027, 1, 1), interval=2, end=date(2027, 6, 30)),
    Rule(WEEKLY, start=date(2027, 1, 1), weekdays=(FRI,), end=date(2027, 3, 1)),
]


@pytest.mark.parametrize("rule", RULES, ids=lambda rule: f"{rule.repeat}-{rule.interval}")
def test_first_on_or_after_agrees_with_checking_every_day_one_by_one(rule):
    window_start = date(2026, 12, 1)
    every_day = [window_start + timedelta(days=n) for n in range(900)]
    scheduled = [day for day in every_day if is_scheduled(rule, day)]

    for day in every_day[:500]:
        expected = next((s for s in scheduled if s >= day), None)
        assert first_on_or_after(rule, day) == expected, f"asked from {day}"

        expected_next = next((s for s in scheduled if s > day), None)
        assert next_after(rule, day) == expected_next, f"asked for the day after {day}"
