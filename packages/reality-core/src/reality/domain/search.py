"""Read-only search vocabulary and deterministic matching, independent of storage."""

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Provider = Literal[
    "partners", "items_locations", "orders", "finance", "shipping", "reality", "reports"
]
Group = Literal[
    "partners",
    "items_locations",
    "orders",
    "finance",
    "shipping",
    "reality",
    "reports",
    "actions",
    "pages",
    "help",
    "companies",
]
FAMILIES: dict[str, tuple[str, ...]] = {
    "partners": ("party",),
    "items_locations": ("item", "location"),
    "orders": ("customer_order", "supplier_order"),
    "finance": (
        "customer_invoice",
        "supplier_invoice",
        "customer_credit",
        "supplier_credit",
        "payment",
    ),
    "shipping": ("shipment",),
    "reality": (
        "document",
        "source_record",
        "commitment",
        "reservation",
        "movement",
        "fact",
        "ledger_entry",
    ),
    "reports": ("private_report",),
}


def normalize(value: str) -> str:
    """Version-one display folding; never use the result as a business identity."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return value.lower().replace("ß", "ss").replace("æ", "ae").replace("œ", "oe")


def words(value: str) -> list[str]:
    return re.findall(r"[^\W_]+", normalize(value), re.UNICODE)


def edit_one(left: str, right: str) -> bool:
    """At most one insertion, deletion, substitution or adjacent transposition."""
    if left == right:
        return True
    if abs(len(left) - len(right)) > 1:
        return False
    i = 0
    while i < min(len(left), len(right)) and left[i] == right[i]:
        i += 1
    if len(left) == len(right):
        return left[i + 1 :] == right[i + 1 :] or (
            i + 1 < len(left)
            and left[i] == right[i + 1]
            and left[i + 1] == right[i]
            and left[i + 2 :] == right[i + 2 :]
        )
    if len(left) > len(right):
        return left[i + 1 :] == right[i:]
    return left[i:] == right[i + 1 :]


def match_tier(query: str, labels: list[str], references: list[str]) -> int | None:
    query = query.strip()
    if not query:
        return None
    if query in references:
        return 0
    folded = normalize(query)
    names = [normalize(x) for x in labels]
    refs = [normalize(x) for x in references]
    if folded in names or folded in refs:
        return 1
    tokens = words(query)
    names_words = [token for name in names for token in words(name)]
    if any(ref.startswith(folded) for ref in refs) or (
        tokens
        and all(any(word.startswith(token) for word in names_words) for token in tokens)
    ):
        return 2
    if tokens and all(
        any(
            word.startswith(token) or (len(token) >= 5 and edit_one(token, word))
            for word in names_words
        )
        for token in tokens
    ):
        return 3
    return None


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(default="", max_length=500)
    provider: Provider
    family: str = ""
    language: Literal["en", "de", "nl", "es"] = "en"
    limit: int = Field(default=4, ge=1, le=50)
    cursor: str | None = Field(default=None, max_length=4096)
    recent_keys: list[str] = Field(default_factory=list, max_length=20)
    context: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def valid_family(self):
        if self.family and self.family not in FAMILIES[self.provider]:
            raise ValueError("Family does not belong to this search provider.")
        if any(len(key) > 256 for key in self.recent_keys + self.context):
            raise ValueError("Search context reference is too long.")
        return self


class RecordTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["record", "saved_report"] = "record"
    record_kind: Literal[
        "party",
        "item",
        "location",
        "document",
        "source_record",
        "commitment",
        "reservation",
        "movement",
        "fact",
        "ledger_entry",
        "payment",
        "shipment",
        "analytics_report",
    ]
    id: str = Field(min_length=1, max_length=256)


class ResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    targets: list[RecordTarget] = Field(max_length=40)


class SearchHit(BaseModel):
    key: str
    family: str
    group: Group
    label: str
    secondary: str = ""
    roles: list[str] = Field(default_factory=list)
    target: RecordTarget
    tier: int = Field(ge=0, le=3)
    sort_key: tuple[int, int, int, int, str, str, str]


class SearchPage(BaseModel):
    items: list[SearchHit]
    has_more: bool
    next_cursor: str | None = None
    provider: Provider
    scope: str
