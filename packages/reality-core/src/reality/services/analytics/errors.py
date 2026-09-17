"""What analytics refuses, and how a saved change is recognised on retry.

These lived in the configured generation's executor, which every other module
imported for them alone. The executor is gone; the refusal and the fingerprint
are not, so they have a home of their own rather than a module that has to stay
alive to be imported from.
"""

import hashlib
import json
from datetime import datetime
from decimal import Decimal

from reality.services.core import InvalidOperation


class AnalyticsError(InvalidOperation):
    """The request was understood and cannot be served, and why.

    The code is what a caller branches on; the sentence is what a person reads.
    It is an InvalidOperation because that is what it is — not an outage.
    """

    def __init__(self, message: str, code: str = "invalid_definition"):
        super().__init__(message)
        self.code = code


def encode(value):
    if isinstance(value, Decimal):
        return str(value)  # exact, and never a float on the way out
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def canonical(value):
    """One spelling per value, so the same change hashes the same twice."""
    return json.dumps(value, default=encode, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()
