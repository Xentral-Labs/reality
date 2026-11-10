"""Spec393: bounded existing references, without mapping authority."""

from typing import Annotated, Literal

from pydantic import Field, field_validator

from reality.domain.shopify_buyer_mapping import HEX, Strict, instant
from reality.domain.shopify_intake_preflight import PreflightInput, SourceBinding

PURPOSE = "shopify_source_reference_lookup_only/1"
MAX_WIRE_BYTES = 24000


class ReferenceLookupInput(PreflightInput):
    family: Literal["company", "location", "item"]
    query: str = Field(default="", max_length=120)
    record_id: str | None = Field(default=None, min_length=1, max_length=200)


class KnownRoles(Strict):
    kind: Literal["known"]
    values: list[str] = Field(max_length=50)


class UnknownRoles(Strict):
    kind: Literal["unknown"]


class ReferenceCandidate(Strict):
    id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=500)
    digest: str = Field(pattern=HEX)
    active: Literal[True]
    roles: Annotated[KnownRoles | UnknownRoles, Field(discriminator="kind")]
    stockUnit: str | None = Field(min_length=1, max_length=100)
    sourceLineIds: list[
        Annotated[str, Field(pattern=r"^gid://shopify/LineItem/[0-9]{1,32}$")]
    ] = Field(max_length=100)

    @field_validator("sourceLineIds")
    @classmethod
    def unique_source_lines(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("duplicate_source_line")
        return value


class ReferenceLookupResult(Strict):
    purpose: Literal["shopify_source_reference_lookup_only/1"]
    source_binding: SourceBinding
    observed_at: str = Field(min_length=1, max_length=100)

    @field_validator("observed_at")
    @classmethod
    def observed_instant(cls, value):
        instant(value)
        return value

    records: list[ReferenceCandidate] = Field(max_length=20)
    hasMore: bool
