"""Exact period differences with explicit absent groups and unknown baselines."""

from decimal import Decimal


def changes(current, previous, dimensions, measures):
    def key(row):
        return tuple(row.get(field) for field in dimensions)

    now = {key(row): row for row in current}
    before = {key(row): row for row in previous}
    rows = []
    for identity in dict.fromkeys([*now, *before]):
        row = dict(now.get(identity) or before[identity])
        for measure in measures:
            absent = None if measure in {"min_price", "max_price"} else "0"
            current_value = now[identity].get(measure) if identity in now else absent
            previous_value = (
                before[identity].get(measure) if identity in before else absent
            )
            row[measure] = current_value
            difference = (
                None
                if current_value is None or previous_value is None
                else Decimal(str(current_value)) - Decimal(str(previous_value))
            )
            row[f"change:{measure}"] = (
                str(difference) if difference is not None else None
            )
            row[f"percent_change:{measure}"] = (
                str(difference / abs(Decimal(str(previous_value))) * 100)
                if difference is not None and Decimal(str(previous_value)) != 0
                else None
            )
        rows.append(row)
    return rows


def order_changes(rows, sorts, dimensions):
    # Stable passes preserve tie ordering; unknowns remain last in either direction.
    rows = sorted(
        rows,
        key=lambda row: tuple(
            (row.get(key) is None, str(row.get(key) or "")) for key in dimensions
        ),
    )
    for sort in reversed(sorts):
        known = [row for row in rows if row.get(sort.field) is not None]
        unknown = [row for row in rows if row.get(sort.field) is None]
        known.sort(
            key=lambda row: (
                str(row[sort.field])
                if sort.field in dimensions
                else Decimal(str(row[sort.field]))
            ),
            reverse=sort.direction == "desc",
        )
        rows = known + unknown
    return rows
