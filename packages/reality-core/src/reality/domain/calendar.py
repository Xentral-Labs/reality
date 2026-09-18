"""One calendar day, and the two conversions every boundary needs.

A document date is a day, not an instant and not a piece of text. It is stored as
a `date` so the database can order, compare and index it, and so an impossible day
cannot be written at all.

Every surface that carries it — the tools, the web API, the MCP schemas, the
storyline fixtures — keeps speaking ISO text, because that is what a caller sends
and what JSON transports. These two functions are where the text becomes a day and
the day becomes text again. An absent day is `None` inside and `""` outside; the
empty string is the shape those surfaces already used for "not stated", and
changing it would be a visible change nobody asked for.
"""

from __future__ import annotations

from datetime import date, datetime


class InvalidDay(ValueError):
    """The text was meant to be a calendar day and is not one."""


def as_day(value: date | datetime | str | None) -> date | None:
    """The day a caller stated, or None when they stated none.

    Accepts what the writers already hold: a `date`, a `datetime` (its UTC day), or
    ISO text. Blank text means "not stated" rather than an error, because that is
    how the existing callers spell an absent document date.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10] if len(text) > 10 else text)
    except ValueError as error:
        raise InvalidDay(f"{value!r} is not a calendar day") from error


def day_text(value: date | None) -> str:
    """What a surface shows: the ISO day, or the empty string for none."""
    return value.isoformat() if value is not None else ""
