"""A saved graph report holds the question, never its answer.

Reopening one re-executes the traversal, so what comes back is a fresh
observation rather than a preserved number — which is the only honest thing a
report can be when the records underneath it keep changing.

That is also why the stored question carries no SQL and no dialect: it is the
same checked object both surfaces produce, and a different execution backend
would be a compiler change rather than a migration of everything ever saved.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from reality.domain.analytics import StrictModel
from reality.domain.traversal import Traversal


class GraphReportChange(StrictModel):
    operation: Literal["create", "update", "rename", "duplicate", "delete"] = Field(
        description="The private graph report change to prepare for confirmation."
    )
    request_id: UUID = Field(
        description=(
            "A fresh UUID for this change. Generate a new one every time; reuse "
            "one only to retry the identical change after a failed response. "
            "The same key with different content is refused, because it cannot "
            "be told apart from a change that was already saved."
        )
    )
    report_id: str | None = Field(
        default=None,
        max_length=128,
        description="Opaque owned report ID; omitted only when creating.",
    )
    expected_revision: int | None = Field(
        default=None,
        ge=1,
        description="Revision shown to the caller; required for every existing report change.",
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        description="Private report name for create, rename or duplicate.",
    )
    question: Traversal | None = Field(
        default=None,
        description="Complete replacement question for create or update.",
    )

    @model_validator(mode="after")
    def operation_fields(self) -> GraphReportChange:
        if self.name is not None:
            self.name = self.name.strip()
            if not self.name:
                raise ValueError("Enter a report name.")
        if self.operation == "create":
            if (
                not self.name
                or not self.question
                or self.report_id
                or self.expected_revision
            ):
                raise ValueError("Creating a report requires only a name and question.")
        elif not self.report_id or not self.expected_revision:
            raise ValueError(
                "A report change requires its identity and expected revision."
            )
        if self.operation in {"rename", "duplicate"} and not self.name:
            raise ValueError("Enter a report name.")
        if self.operation == "update" and not self.question:
            raise ValueError("An update requires the complete question.")
        if self.operation in {"rename", "duplicate", "delete"} and self.question:
            raise ValueError("This operation does not accept a replacement question.")
        return self
