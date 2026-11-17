"""Short texts shown on cards."""

from datetime import date

from django.utils.dates import WEEKDAYS_ABBR
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from . import schedule

# Written out one by one because other languages change the word after "since"
# (Czech: "od pondělí", "od středy").
_SINCE_WEEKDAY = [
    lambda: _("since Monday"),
    lambda: _("since Tuesday"),
    lambda: _("since Wednesday"),
    lambda: _("since Thursday"),
    lambda: _("since Friday"),
    lambda: _("since Saturday"),
    lambda: _("since Sunday"),
]


def waiting_since(card_date: date, day: date) -> str:
    """
    How long a card has been waiting, in neutral words. Empty for a card of today.

    Never "overdue" and never a number of days late (docs/design.md, section 3.1).
    """
    days = (day - card_date).days
    if days <= 0:
        return ""
    if days == 1:
        return _("since yesterday")
    if days < 7:
        return _SINCE_WEEKDAY[card_date.weekday()]()
    # Translators: a date format for Django's date filter, giving day and month, as in "3 November".
    return _("since %(date)s") % {"date": date_format(card_date, _("j F"))}


def day_heading(shown: date, day: date) -> str:
    """The heading of one day in the list of finished tasks: Today, Yesterday, or the date."""
    days = (day - shown).days
    if days == 0:
        return _("Today")
    if days == 1:
        return _("Yesterday")
    # Translators: a date format for Django's date filter, giving weekday, day and month,
    # as in "Monday 2 November".
    heading = date_format(shown, _("l j F"))
    if shown.year != day.year:
        heading += f" {shown.year}"
    return heading


def repeat_summary(task) -> str:
    """How often a task comes, in a few words, for the list of tasks."""
    n = task.interval or 1
    if task.repeat == schedule.ON_DEMAND:
        return _("When asked for")
    if task.repeat == schedule.ONCE:
        # Translators: a one-time task's day, as in "Once, 3 November".
        return _("Once, %(date)s") % {"date": date_format(task.start_date, _("j F"))}
    if task.repeat == schedule.DAYS:
        if n == 1:
            return _("Every day")
        return ngettext("Every %(n)d day", "Every %(n)d days", n) % {"n": n}
    if task.repeat == schedule.WEEKLY:
        days = ", ".join(str(WEEKDAYS_ABBR[day]).capitalize() for day in sorted(task.weekdays))
        if n == 1:
            return days
        return ngettext("%(days)s, every %(n)d week", "%(days)s, every %(n)d weeks", n) % {
            "days": days,
            "n": n,
        }
    if task.repeat == schedule.MONTHLY:
        if task.day_of_month == 31:
            day = _("on the last day")
        else:
            day = _("on day %(day)d") % {"day": task.day_of_month or 1}
        if n == 1:
            return _("Every month, %(day)s") % {"day": day}
        return ngettext("Every %(n)d month, %(day)s", "Every %(n)d months, %(day)s", n) % {
            "n": n,
            "day": day,
        }
    return ""
