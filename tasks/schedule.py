"""
On which days a repeating task is scheduled. Pure date arithmetic: no database, no clock.

A rule answers one question, "is the task scheduled on this day?". Two functions build on
it: the first scheduled day on or after a given day, and the next one after it. The rest
of the app only ever asks these (docs/design.md, section 5).
"""

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

ONCE = "once"
DAYS = "days"
WEEKLY = "weekly"
MONTHLY = "monthly"


@dataclass(frozen=True)
class Rule:
    repeat: str
    # The first day the task can be scheduled on. Counting "every N" starts here.
    start: date
    interval: int = 1
    # For WEEKLY. Monday is 0, Sunday is 6.
    weekdays: tuple[int, ...] = ()
    # For MONTHLY. 31 means the last day in shorter months.
    day_of_month: int | None = None
    # The last day the task can be scheduled on, if it ever stops.
    end: date | None = None


def _monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _day_in_month(wanted: int, month_of: date) -> int:
    last_day = calendar.monthrange(month_of.year, month_of.month)[1]
    return min(wanted, last_day)


def is_scheduled(rule: Rule, day: date) -> bool:
    if day < rule.start or (rule.end is not None and day > rule.end):
        return False
    if rule.repeat == ONCE:
        return day == rule.start
    if rule.repeat == DAYS:
        return (day - rule.start).days % rule.interval == 0
    if rule.repeat == WEEKLY:
        # "Every second week" counts whole weeks from the week the task started in.
        weeks = (_monday_of(day) - _monday_of(rule.start)).days // 7
        return weeks % rule.interval == 0 and day.weekday() in rule.weekdays
    if rule.repeat == MONTHLY:
        if rule.day_of_month is None:
            return False
        months = (day.year - rule.start.year) * 12 + day.month - rule.start.month
        return months % rule.interval == 0 and day.day == _day_in_month(rule.day_of_month, day)
    raise ValueError(f"unknown way of repeating: {rule.repeat!r}")


def first_on_or_after(rule: Rule, day: date) -> date | None:
    """The first scheduled day that is `day` or later. None if there is none."""
    day = max(day, rule.start)

    if rule.repeat == ONCE:
        found = rule.start if day == rule.start else None
    elif rule.repeat == DAYS:
        days_into_cycle = (day - rule.start).days % rule.interval
        found = day if days_into_cycle == 0 else day + timedelta(rule.interval - days_into_cycle)
    else:
        # Weekly and monthly rules are looked through day by day. One full cycle plus a
        # little is always enough to meet a scheduled day, if the rule has any.
        if rule.repeat == WEEKLY:
            days_to_look_at = 7 * (rule.interval + 1)
        else:
            days_to_look_at = 31 * (rule.interval + 1)
        found = None
        for offset in range(days_to_look_at + 1):
            candidate = day + timedelta(days=offset)
            if is_scheduled(rule, candidate):
                found = candidate
                break

    if found is not None and rule.end is not None and found > rule.end:
        return None
    return found


def next_after(rule: Rule, day: date) -> date | None:
    """The first scheduled day later than `day`. None if there is none."""
    return first_on_or_after(rule, day + timedelta(days=1))
