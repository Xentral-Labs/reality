"""Bounded external mapping intents; no financial amount or tax calculations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Intent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=4000)


class CreateTarget(Intent):
    namespace: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)


class UpdateTarget(Intent):
    target_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    state: Literal["active", "blocked"]


class CreateReference(Intent):
    target_id: str = Field(min_length=1)
    kind: Literal["account", "tax_code"]
    code: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)


class UpdateReference(Intent):
    reference_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    state: Literal["active", "blocked"]


class SetMapping(Intent):
    target_id: str = Field(min_length=1)
    mapping_kind: Literal["local_account", "case_routing"]
    local_account_id: str | None = None
    transaction_kind: (
        Literal[
            "sales_invoice", "supplier_invoice", "credit_note", "supplier_credit_note"
        ]
        | None
    ) = None
    case_reference_id: str | None = None
    group_mode: Literal["none", "exact"] | None = None
    group_reference_id: str | None = None
    external_account_id: str = Field(min_length=1)
    external_tax_code_id: str | None = None
    state: Literal["active", "blocked"] = "active"

    @model_validator(mode="after")
    def shape(self):
        if self.mapping_kind == "local_account":
            valid = bool(self.local_account_id) and all(
                v is None
                for v in (
                    self.transaction_kind,
                    self.case_reference_id,
                    self.group_mode,
                    self.group_reference_id,
                    self.external_tax_code_id,
                )
            )
        else:
            valid = (
                self.local_account_id is None
                and bool(
                    self.transaction_kind and self.case_reference_id and self.group_mode
                )
                and (
                    bool(self.group_reference_id)
                    if self.group_mode == "exact"
                    else self.group_reference_id is None
                )
            )
        if not valid:
            raise ValueError("Invalid mapping scope shape.")
        return self


COMMANDS = {
    "finance.target.create": CreateTarget,
    "finance.target.update": UpdateTarget,
    "finance.target_reference.create": CreateReference,
    "finance.target_reference.update": UpdateReference,
    "finance.target_mapping.set": SetMapping,
}
SCOPE = (
    "target_id",
    "mapping_kind",
    "local_account_id",
    "transaction_kind",
    "case_reference_id",
    "group_mode",
    "group_reference_id",
)
