"""Short texts shown on cards."""

from datetime import date

from django.utils.formats import date_format
from django.utils.translation import gettext as _

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
