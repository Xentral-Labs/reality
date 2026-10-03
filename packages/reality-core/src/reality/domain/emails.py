"""Closed handoff envelopes; external message payloads remain lossless."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EmailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Attachment(EmailInput):
    part_id: str = Field(min_length=1, max_length=200)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = "application/octet-stream"
    artifact_id: str | None = None
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    inline: bool = False
    content_id: str | None = None
    missing_reason: str | None = None


class EmailMessage(EmailInput):
    account: str = Field(min_length=1, max_length=320)
    sender: str = Field(min_length=1, max_length=320)
    to: list[str] = Field(default_factory=list, max_length=1000)
    cc: list[str] = Field(default_factory=list, max_length=1000)
    bcc: list[str] = Field(default_factory=list, max_length=1000)
    subject: str = Field(max_length=10000)
    text: str = Field(default="", max_length=2000000)
    html: str = Field(default="", max_length=2000000)
    message_id: str | None = None
    thread_id: str | None = None
    in_reply_to: str | None = None
    references: list[str] = Field(default_factory=list)
    stated_at: str | None = None
    headers: dict[str, Any] = Field(default_factory=dict)
    external_payload: dict[str, Any] = Field(default_factory=dict)
    original_artifact_id: str | None = None
    original_filename: str | None = Field(default=None, max_length=255)
    attachments: list[Attachment] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def unique_parts(self):
        if len({part.part_id for part in self.attachments}) != len(self.attachments):
            raise ValueError("Attachment part IDs must be unique within one message.")
        return self


class CaptureEmail(EmailInput):
    origin: str = Field(min_length=1, max_length=200)
    retry_key: str = Field(min_length=1, max_length=200)
    direction: Literal["inbound", "outbound"]
    message: EmailMessage


class DispatchProposal(EmailInput):
    message: EmailMessage
    rationale: str = Field(min_length=1, max_length=10000)
    supporting_source_ids: list[str] = Field(default_factory=list, max_length=1000)
    fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class ClaimDispatch(EmailInput):
    proposal_id: str
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    retry_key: str = Field(min_length=1, max_length=200)


class ReportDispatch(EmailInput):
    execution_id: str
    retry_key: str = Field(min_length=1, max_length=200)
    outcome: Literal["accepted", "failed", "unknown"]
    observed_at: datetime
    actual_message: EmailMessage | None = None
    provider_evidence: dict[str, Any]

    @model_validator(mode="after")
    def observed_result(self):
        if self.observed_at.tzinfo is None:
            raise ValueError("Observed time must include a timezone.")
        if self.outcome == "accepted" and (
            self.actual_message is None or not self.provider_evidence
        ):
            raise ValueError(
                "Provider acceptance requires actual message and provider evidence."
            )
        return self


class EmailHistory(EmailInput):
    source_id: str | None = None
    proposal_id: str | None = None
    execution_id: str | None = None

    @model_validator(mode="after")
    def one_identity(self):
        if (
            sum(
                bool(value)
                for value in (self.source_id, self.proposal_id, self.execution_id)
            )
            != 1
        ):
            raise ValueError("Provide exactly one source, proposal or execution ID.")
        return self


class EmailChunk(EmailInput):
    content_base64: str = Field(min_length=1, max_length=1398104)


class EmailFile(EmailInput):
    part_artifact_ids: list[str] = Field(min_length=1, max_length=10000)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = "application/octet-stream"
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
