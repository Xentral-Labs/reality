"""Vocabulary for learning metadata; operational truth stays in Reality records."""

from enum import StrEnum


class TenantPurpose(StrEnum):
    BUSINESS = "business"
    PLAYGROUND = "playground"


class PlaygroundRunStatus(StrEnum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INITIALIZATION_FAILED = "initialization_failed"
    ARCHIVED = "archived"
