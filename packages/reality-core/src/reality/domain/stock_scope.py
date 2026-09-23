"""One definition of what it means for a record to sit at a location.

The register scope and the item/location explanation must agree about which
movements and reservations belong to a place, so the predicate lives here once
instead of in each read.
"""

from sqlalchemy import or_
from sqlalchemy.sql.elements import ColumnElement

from reality.db.core import Movement, Reservation


def movement_at(location_id: str) -> ColumnElement[bool]:
    """A movement belongs to a place through either side of its route."""
    return or_(
        Movement.from_location_id == location_id,
        Movement.to_location_id == location_id,
    )


def reservation_at(location_id: str) -> ColumnElement[bool]:
    """A reservation holds stock at exactly one place."""
    return Reservation.location_id == location_id
