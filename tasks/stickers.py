"""QR stickers: a printable page of codes, each leading to its task's scan page."""

import segno
from django.urls import reverse
from django.utils.safestring import mark_safe


def stickers_context(request, tasks, back_url: str) -> dict:
    """
    The stickers for these tasks, ready for `tasks/stickers.html`.

    Each code holds the full address of the task's scan page, as this browser reached
    the app. That is why the stickers are printed from the address the family uses.
    """
    stickers = []
    for task in tasks:
        address = request.build_absolute_uri(reverse("task-qr", args=[task.ensure_qr_key()]))
        code = segno.make(address, error="m").svg_inline(omitsize=True, title=task.name)
        stickers.append((task, mark_safe(code)))  # noqa: S308 - segno escapes the title
    return {"stickers": stickers, "address": request.build_absolute_uri("/"), "back_url": back_url}
