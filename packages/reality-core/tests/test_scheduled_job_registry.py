import pytest
from pydantic import ValidationError

from reality.jobs.registry import JobError, JobResult, definitions, register


def test_registry_rejects_duplicates_and_unknown_arguments():
    cleanup = definitions()["invitations.cleanup"]
    with pytest.raises(JobError, match="duplicate"):
        register(cleanup)
    with pytest.raises(JobError, match="configuration"):
        cleanup.validate({"secret": "never accepted"})
    with pytest.raises((ValueError, ValidationError)):
        JobResult(counts={"bad": "secret"})


def test_documented_registration_example_is_executable():
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[3] / "docs/features/scheduled-jobs.md"
    ).read_text()
    example = text.split("```python\n")[1].split("```")[0]
    namespace = {}
    exec(compile(example, "scheduled-jobs.md", "exec"), namespace)  # noqa: S102 - trusted repository example
    assert namespace["CLEANUP"].name == "invitations.cleanup"
    assert namespace["CLEANUP"].config_model.model_validate({}) is not None


def test_unknown_handler_and_bounded_payloads():
    from reality.jobs.registry import get_definition

    with pytest.raises(JobError, match="unknown_job_type"):
        get_definition("python -c arbitrary")
    with pytest.raises(JobError, match="invalid_configuration"):
        definitions()["invitations.cleanup"].validate({"payload": "x" * 16000})
    with pytest.raises((ValueError, ValidationError)):
        JobResult(counts={"x" * 4000: 1})
